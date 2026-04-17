import streamlit as st
from playwright.sync_api import sync_playwright
import re
import os

# --- TARAYICI KURULUMU (Web Sunucusu İçin) ---
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="MY-Sosyal Medya Analiz Aracı", layout="centered")

# --- CSS TASARIMI (Mavi-Beyaz Teman) ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-title { color: #1a73e8; font-family: 'Arial'; font-weight: bold; text-align: center; padding: 10px; }
    .result-container { background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .stButton>button { border-radius: 6px; font-weight: bold; transition: 0.2s; }
    .stButton>button:hover { transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

# --- ANALİZ FONKSİYONU (Orijinal Kodundaki Mantık) ---
def analiz_motoru(url):
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            page = context.new_page()
            page.route("**/*.{png,jpg,jpeg,gif,svg}", lambda route: route.abort()) # Hız için resimleri engelle
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Başlık ve Ad Çekme
            if "tiktok.com" in url:
                try: ad = page.locator('h1[data-e2e="user-title"]').first.inner_text()
                except: ad = page.title()
            elif "x.com" in url or "twitter.com" in url:
                try:
                    page.wait_for_selector('[data-testid="UserName"]', timeout=5000)
                    ad = page.locator('[data-testid="UserName"] span').first.inner_text()
                except: ad = page.title()
            else: ad = page.title()

            # Temizleme
            gereksizler = ["TikTok", "Instagram", "Facebook", "X.com", "Twitter", "Giriş Yap", "|", "-", "•"]
            ad = re.sub(r'\(.*?\)', '', ad)
            for k in gereksizler: ad = ad.replace(k, "")
            ad = ad.strip()
            
            uzanti = url.rstrip("/").split("/")[-1].replace("@", "").split("?")[0]
            
            # ID Bulma
            source = page.content()
            id_match = re.search(r'"identifier":"(\d+)"|"rest_id":"(\d+)"|"userID":"(\d+)"|user_id=(\d+)', source)
            pid = next((m for m in id_match.groups() if m), "ID Bulunamadı") if id_match else "ID Bulunamadı"
            
            browser.close()
            return ad, pid, uzanti, url
        except Exception as e:
            return "Hata", "Bağlantı Başarısız", "Bulunamadı", url

# --- ARAYÜZ ---
st.markdown("<h1 class='main-title'>MY-Sosyal Medya Analiz Aracı</h1>", unsafe_allow_html=True)

# Giriş Kutusu
url_input = st.text_input("", placeholder="Analiz edilecek URL'yi buraya yapıştırın...", label_visibility="collapsed")

# Butonlar
col1, col2 = st.columns([3, 1])
with col1:
    analiz_btn = st.button("Analiz Et", type="primary", use_container_width=True)
with col2:
    if st.button("Temizle", use_container_width=True):
        st.rerun()

# Sonuç Ekranı
if analiz_btn and url_input:
    with st.spinner("Sorgulanıyor..."):
        ad, pid, uz, sn_url = analiz_motoru(url_input)
        
        st.markdown("### 📊 Sorgu Sonucu")
        with st.container():
            st.markdown(f"""
                <div class="result-container">
                    <p><b>👤 Profil Adı:</b> {ad}</p>
                    <p><b>🆔 Profil ID:</b> {pid}</p>
                    <p><b>🔗 Uzantı:</b> {uz}</p>
                    <p><b>🌍 URL:</b> {sn_url}</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            # KOPYALAMA BUTONU GÖREVİ GÖREN ALAN
            # Bu kutunun sağ üstündeki kopyala ikonuna basıldığında tüm bilgiler kopyalanır.
            st.code(f"Profil Adı: {ad}\nProfil ID: {pid}\nProfil URL: {sn_url}", language="text")
            st.toast("Sonuçlar kopyalanmaya hazır!")