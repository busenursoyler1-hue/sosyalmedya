import streamlit as st
from playwright.sync_api import sync_playwright
import re

# Sayfa ayarları
st.set_page_config(page_title="MY-Sosyal Medya Analiz Aracı", layout="centered")

# --- Fonksiyonlar ---
def temizle_profil_adi(ad, url):
    gereksizler = ["TikTok", "Instagram", "Facebook", "X.com", "Twitter", "Giriş Yap", "Log in", "Sign up", "Kaydolun", "Make Your Day", "ve videoları", "photos and videos", "on Instagram", "official", "|", "-", "•"]
    ad = re.sub(r'\(.*?\)', '', ad)
    for kelime in gereksizler:
        ad = ad.replace(kelime, "")
    if "facebook.com" in url:
        kelimeler = ad.strip().split()
        ad = " ".join(kelimeler[:2]) if len(kelimeler) > 2 else " ".join(kelimeler)
    return ad.strip()

def sorgu_motoru(url):
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            page = context.new_page()
            page.route("**/*.{png,jpg,jpeg,gif,svg}", lambda route: route.abort())
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Profil Adı yakalama
            if "tiktok.com" in url:
                profil_adi = page.locator('h1[data-e2e="user-title"]').first.inner_text() if page.locator('h1[data-e2e="user-title"]').count() > 0 else page.title()
            elif "x.com" in url or "twitter.com" in url:
                profil_adi = page.locator('[data-testid="UserName"] span').first.inner_text() if page.locator('[data-testid="UserName"]').count() > 0 else page.title()
            else:
                profil_adi = page.title()
            
            profil_adi = temizle_profil_adi(profil_adi, url)
            uzanti = url.rstrip("/").split("/")[-1].replace("@", "").split("?")[0]
            
            sayfa_kaynagi = page.content()
            id_regex = r'"identifier":"(\d+)"|"rest_id":"(\d+)"|"userID":"(\d+)"|user_id=(\d+)|"id":"(\d+)"|"authorId":"(\d+)"'
            match = re.search(id_regex, sayfa_kaynagi)
            profil_id = next((m for m in match.groups() if m), "ID Bulunamadı")
            
            browser.close()
            return profil_adi, profil_id, uzanti
        except Exception as e:
            return "Hata", str(e), "Hata"

# --- Arayüz ---
st.title("MY-Sosyal Medya Analiz Aracı")

# Sekmeler (Üst ve Manuel)
tab1, tab2 = st.tabs(["URL ile Analiz", "Gelişmiş Manuel Sorgu"])

with tab1:
    url = st.text_input("Analiz edilecek URL'yi girin:")
    if st.button("Analiz Et"):
        if url:
            with st.spinner('Sorgulanıyor...'):
                ad, pid, uz = sorgu_motoru(url)
                st.success("Profil Sorgu Sonucu")
                st.write(f"**Profil Adı:** {ad}")
                st.write(f"**Profil ID:** {pid}")
                st.write(f"**Uzantı:** {uz}")
        else:
            st.warning("URL giriniz.")

with tab2:
    platform = st.radio("Platform:", ["X", "Facebook", "Instagram", "TikTok"], horizontal=True)
    mod = st.selectbox("Mod:", ["Kullanıcı Adından ID Bulma", "ID'den Kullanıcı Adı Bulma"])
    val = st.text_input("Kullanıcı adı veya ID:")
    
    if st.button("Çözümle"):
        if val:
            v = val.replace("@", "")
            if "Kullanıcı Adı" in mod:
                url = {"X": f"https://x.com/{v}", "Facebook": f"https://www.facebook.com/{v}", 
                       "Instagram": f"https://www.instagram.com/{v}", "TikTok": f"https://www.tiktok.com/@{v}"}[platform]
            else:
                url = f"https://www.facebook.com/profile.php?id={v}" if platform == "Facebook" else None
            
            if url:
                with st.spinner('Çözümleniyor...'):
                    ad, pid, uz = sorgu_motoru(url)
                    st.success("Sonuç (Manuel)")
                    st.write(f"**Profil Adı:** {ad}")
                    st.write(f"**Profil ID:** {pid}")
            else:
                st.error("Sadece Facebook ID desteklenir.")
        else:
            st.warning("Değer giriniz.")