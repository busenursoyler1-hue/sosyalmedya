import streamlit as st
from playwright.sync_api import sync_playwright
import re
import os

# --- TARAYICI KURULUMU (Web Sunucusu İçin) ---
# Render veya Streamlit Cloud üzerinde Chromium'un kurulu olduğundan emin olur
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="MY-Sosyal Medya Analiz Aracı", layout="centered")

# --- ÖZEL TASARIM (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; transition: 0.3s; }
    .stButton>button:hover { border-color: #1a73e8; color: #1a73e8; }
    .result-card { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 10px; }
    .title-text { color: #1a73e8; font-weight: bold; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- FONKSİYONLAR (Senin Kodundaki Mantıkla Birebir) ---
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
            # Headless mod (Ekran açılmadan çalışır)
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            page = context.new_page()
            # Resimleri yükleme (Hız kazanmak için)
            page.route("**/*.{png,jpg,jpeg,gif,svg}", lambda route: route.abort())
            
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
            
            # Platforma özel başlık çekme
            profil_adi = ""
            if "tiktok.com" in url:
                try: profil_adi = page.locator('h1[data-e2e="user-title"]').first.inner_text()
                except: profil_adi = page.title()
            elif "x.com" in url or "twitter.com" in url:
                try:
                    page.wait_for_selector('[data-testid="UserName"]', timeout=5000)
                    profil_adi = page.locator('[data-testid="UserName"] span').first.inner_text()
                except: profil_adi = page.title()
            else:
                profil_adi = page.title()
            
            # Adı temizle ve ID ara
            profil_adi = temizle_profil_adi(profil_adi, url)
            uzanti = url.rstrip("/").split("/")[-1].replace("@", "").split("?")[0]
            
            sayfa_kaynagi = page.content()
            id_regex = r'"identifier":"(\d+)"|"rest_id":"(\d+)"|"userID":"(\d+)"|user_id=(\d+)|"id":"(\d+)"|"authorId":"(\d+)"'
            match = re.search(id_regex, sayfa_kaynagi)
            profil_id = next((m for m in match.groups() if m), "ID Bulunamadı")
            
            browser.close()
            return profil_adi, profil_id, uzanti, url
        except Exception as e:
            return "Hata", "Bağlantı Sorunu veya Gizli Profil", "Bulunamadı", url

# --- ANA ARAYÜZ ---
st.markdown("<h1 class='title-text'>MY-Sosyal Medya Analiz Aracı</h1>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 URL ile Otomatik Sorgu", "⚙️ Manuel Sorgu Paneli"])

# --- TAB 1: URL SORGULAMA ---
with tab1:
    st.info("Sosyal medya profil URL'sini yapıştırın, sistem tüm bilgileri otomatik çeksin.")
    url_input = st.text_input("Profil URL'si:", placeholder="Örn: https://x.com/kullaniciadi", key="main_url")
    
    col_btn, col_cls = st.columns([3, 1])
    with col_btn:
        btn_analiz = st.button("ANALİZ ET", type="primary", use_container_width=True)
    with col_cls:
        if st.button("TEMİZLE", key="cls_1"):
            st.rerun()

    if btn_analiz and url_input:
        with st.spinner('Veriler toplanıyor...'):
            ad, pid, uz, sn_url = sorgu_motoru(url_input)
            st.subheader("📊 Sorgu Sonucu")
            st.markdown(f"""
                <div class="result-card">
                    <p><b>👤 Profil Adı:</b> {ad}</p>
                    <p><b>🆔 Profil ID:</b> {pid}</p>
                    <p><b>🔗 Uzantı:</b> {uz}</p>
                    <p><b>🌍 URL:</b> {sn_url}</p>
                </div>
            """, unsafe_allow_html=True)
            # Kopyalamayı kolaylaştırmak için
            st.text_area("Kopyalanabilir Format:", f"Ad: {ad}\nID: {pid}\nURL: {sn_url}", height=100)

# --- TAB 2: MANUEL SORGULAMA ---
with tab2:
    st.warning("Elinizde sadece kullanıcı adı veya ID varsa burayı kullanın.")
    platform = st.radio("Platform seçiniz:", ["X", "Facebook", "Instagram", "TikTok"], horizontal=True)
    
    c1, c2 = st.columns(2)
    with c1:
        mod = st.selectbox("Yöntem:", ["Kullanıcı Adından ID Bul", "ID'den Kullanıcı Adı Bul"])
    with c2:
        val = st.text_input("Giriş yapın:", placeholder="Kullanıcı adı veya ID...")

    if st.button("SİSTEMİ ÇÖZÜMLE", use_container_width=True):
        if val:
            clean_val = val.replace("@", "")
            target_url = ""
            if "Kullanıcı Adı" in mod:
                links = {"X": f"https://x.com/{clean_val}", "Facebook": f"https://www.facebook.com/{clean_val}", 
                         "Instagram": f"https://www.instagram.com/{clean_val}", "TikTok": f"https://www.tiktok.com/@{clean_val}"}
                target_url = links[platform]
            else:
                if platform == "Facebook":
                    target_url = f"https://www.facebook.com/profile.php?id={clean_val}"
                else:
                    st.error("Bu işlem şimdilik sadece Facebook için geçerlidir.")
            
            if target_url:
                with st.spinner('Manuel tarama yapılıyor...'):
                    ad, pid, uz, sn_url = sorgu_motoru(target_url)
                    st.success("Manuel Sorgu Başarılı")
                    st.markdown(f"""
                        <div class="result-card" style="border-top: 4px solid #e67e22;">
                            <p><b>👤 Profil Adı:</b> {ad}</p>
                            <p><b>🆔 Profil ID:</b> {pid}</p>
                            <p><b>🔗 Uzantı:</b> {uz}</p>
                        </div>
                    """, unsafe_allow_html=True)