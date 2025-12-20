import streamlit as st
import pandas as pd
import yfinance as yf
import json
from datetime import datetime, timedelta

# --- 1. SİSTEM AYARLARI ---
st.set_page_config(page_title="Zenith Portföy Pro", layout="wide")

# Session State'i en güvenli şekilde başlatıyoruz
if 'portfoy_listesi' not in st.session_state:
    st.session_state['portfoy_listesi'] = []

# --- 2. DOSYA YÖNETİMİ (SOL PANEL) ---
with st.sidebar:
    st.header("📂 VERİ YÜKLE")
    dosya = st.file_uploader("Yedek JSON Seç", type=['json'], key="uploader")
    
    if dosya is not None:
        try:
            okunan_veri = json.load(dosya)
            # Tarihleri objeye çevir
            for icerik in okunan_veri:
                if isinstance(icerik.get('tarih'), str):
                    icerik['tarih'] = datetime.strptime(icerik['tarih'], '%Y-%m-%d').date()
            
            # JSON verisini listeye AKTAR (Üzerine yazma, listeyi güncelle)
            st.session_state['portfoy_listesi'] = okunan_veri
            st.success("Yedek başarıyla içeri aktarıldı!")
        except Exception as e:
            st.error(f"Hata: {e}")

    st.divider()
    if st.session_state['portfoy_listesi']:
        # İndirme hazırlığı
        indirilecek_liste = []
        for p in st.session_state['portfoy_listesi']:
            kopya = p.copy()
            if hasattr(kopya['tarih'], 'strftime'):
                kopya['tarih'] = kopya['tarih'].strftime('%Y-%m-%d')
            indirilecek_liste.append(kopya)
        
        st.download_button("📥 MEVCUT LİSTEYİ YEDEKLE", 
                           data=json.dumps(indirilecek_liste),
                           file_name="guncel_portfoy.json",
                           use_container_width=True)

# --- 3. ANA EKRAN: VERİ GİRİŞİ ---
st.title("⚖️ Portföy Takip Sistemi")
st.info("Aşağıdaki alanları doldurarak fon ekleyin. JSON yüklü olsa bile ekleme yapabilirsiniz.")

# Giriş alanlarını alt alta ve birbirinden bağımsız anahtarlarla (key) tanımlıyoruz
v_kod = st.text_input("1. FON KODU (ÖRN: TCD)", key="v1").upper().strip()
v_tar = st.date_input("2. ALIŞ TARİHİ", value=datetime.now() - timedelta(days=30), key="v2")
v_adet = st.number_input("3. SATIN ALINAN ADET", value=0.0, format="%.4f", key="v3")
v_alis = st.number_input("4. ALIŞTAKİ BİRİM FİYAT (TL)", value=0.0, format="%.4f", key="v4")

# İşte kaybolan o meşhur hücre - İsmini ve yerini değiştirdik
v_guncel_fiyat = st.number_input("5. ŞU ANKİ GÜNCEL BİRİM FİYAT (TL)", value=0.0, format="%.4f", key="v5_guncel")

if st.button("➕ PORTFÖYE ŞİMDİ EKLE", use_container_width=True):
    if v_kod and v_adet > 0:
        with st.spinner("Kurlar alınıyor..."):
            t_str = v_tar.strftime('%Y-%m-%d')
            # Dolar kurunu çek
            u_data = yf.download("USDTRY=X", start=t_str, end=(v_tar + timedelta(days=5)).strftime('%Y-%m-%d'), progress=False)
            u_eski = float(u_data['Close'].iloc[0]) if not u_data.empty else 1.0
            
            # Yeni kaydı oluştur
            yeni_kayit = {
                "kod": v_kod,
                "tarih": v_tar,
                "adet": v_adet,
                "maliyet": v_alis,
                "guncel": v_guncel_fiyat if v_guncel_fiyat > 0 else v_alis,
                "usd_old": u_eski
            }
            
            # Listeye ekle (Session State'i doğrudan manipüle et)
            st.session_state['portfoy_listesi'].append(yeni_kayit)
            st.success(f"{v_kod} eklendi!")
            st.rerun()
    else:
        st.error("Lütfen en azından Kod ve Adet kısımlarını doldurun!")

st.divider()

# --- 4. TABLO VE HESAPLAR ---
if st.session_state['portfoy_listesi']:
    st.subheader("📊 Portföy Durumu")
    
    # Güncel doları çek
    u_simdi = yf.download("USDTRY=X", period="1d", progress=False)['Close'].iloc[-1]
    
    tablo_verisi = []
    for i, kalem in enumerate(st.session_state['portfoy_listesi']):
        ana_para = kalem['adet'] * kalem['maliyet']
        son_deger = kalem['adet'] * kalem['guncel']
        
        tablo_verisi.append({
            "FON": kalem['kod'],
            "TARİH": kalem['tarih'],
            "TOPLAM MALİYET": f"{ana_para:,.2f} TL",
            "GÜNCEL DEĞER": f"{son_deger:,.2f} TL",
            "K/Z (TL)": f"{(son_deger - ana_para):,.2f} TL",
            "DOLAR BAZLI FARK": f"{((son_deger / u_simdi) - (ana_para / kalem['usd_old'])):,.2f} $"
        })
        
        # Silme seçeneği
        if st.button(f"🗑️ {kalem['kod']} ({kalem['tarih']}) Kaydını Sil", key=f"btn_{i}"):
            st.session_state['portfoy_listesi'].pop(i)
            st.rerun()

    st.table(tablo_verisi)

    # Genel Toplamlar
    toplam_m = sum(k['adet'] * k['maliyet'] for k in st.session_state['portfoy_listesi'])
    toplam_g = sum(k['adet'] * k['guncel'] for k in st.session_state['portfoy_listesi'])
    
    c1, c2 = st.columns(2)
    c1.metric("TOPLAM ANA PARA", f"{toplam_m:,.2f} TL")
    c2.metric("TOPLAM PORTFÖY", f"{toplam_g:,.2f} TL", delta=f"{toplam_g - toplam_m:,.2f} TL")

else:
    st.info("Portföyünüz boş. Yukarıdaki 5 adımı doldurarak ekleme yapın.")
