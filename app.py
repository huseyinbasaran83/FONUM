import streamlit as st
import pandas as pd
import yfinance as yf
import json
from datetime import datetime, timedelta

# 1. TÜM BELLEĞİ VE ID'LERİ SIFIRLAYAN AYAR
st.set_page_config(page_title="Zenith Pro: Kesin Çözüm", layout="wide")

# Session State'i daha önce kullanılmamış anahtarlarla (keys) başlatıyoruz
if 'ANA_LISTE' not in st.session_state:
    st.session_state['ANA_LISTE'] = []

# 2. YARDIMCI FONKSİYONLAR
def kur_getir(t):
    try:
        d_s = t.strftime('%Y-%m-%d')
        u = yf.download("USDTRY=X", start=d_s, end=(t + timedelta(days=5)).strftime('%Y-%m-%d'), progress=False)
        return float(u['Close'].iloc[0]) if not u.empty else 1.0
    except: return 1.0

# 3. YEDEK YÜKLEME (SOL PANEL)
with st.sidebar:
    st.subheader("📁 DOSYA SİSTEMİ")
    yeni_dosya = st.file_uploader("JSON Yedeği Seç", type=['json'], key="UNIQUE_UPLOADER_99")
    
    if yeni_dosya:
        try:
            veriler = json.load(yeni_dosya)
            hazir_liste = []
            for v in veriler:
                if isinstance(v.get('tarih'), str):
                    v['tarih'] = datetime.strptime(v['tarih'], '%Y-%m-%d').date()
                hazir_liste.append(v)
            
            if st.button("LİSTEYE AKTAR", key="UNIQUE_ACTIVATE_BTN"):
                st.session_state['ANA_LISTE'] = hazir_liste
                st.rerun()
        except: st.error("Dosya okunamadı.")

# 4. ANA EKRAN: VERİ GİRİŞİ (SIRALI VE NUMARALI)
st.title("⚖️ Portföy Yönetim Paneli")
st.write("---")

# Giriş alanlarını hiçbir yapı (column/form) kullanmadan, doğrudan alt alta koyuyoruz.
# Her birinin Key'i daha önce hiç kullanılmamış isimler.

# SIRA 1
st.subheader("1. Fon Tanımı")
k_ad = st.text_input("FON KODU (Örn: BTC-USD)", key="K_1").upper()

# SIRA 2
st.subheader("2. Tarih Seçimi")
k_tar = st.date_input("ALIM TARİHİ", key="K_2")

# SIRA 3
st.subheader("3. Miktar")
k_adet = st.number_input("ADET", min_value=0.0, format="%.4f", key="K_3")

# SIRA 4
st.subheader("4. Alış Değeri")
k_alis = st.number_input("ALIM BİRİM FİYATI (TL)", min_value=0.0, format="%.4f", key="K_4")

# SIRA 5 - MEŞHUR GÜNCEL FİYAT HÜCRESİ
st.subheader("5. Güncel Değer")
k_guncel = st.number_input("ŞU ANKİ BİRİM FİYAT (TL)", min_value=0.0, format="%.4f", key="K_5_GUNCEL_CELL")

# SIRA 6 - KAYDET BUTONU
if st.button("👉 PORTFÖYE ŞİMDİ EKLE", use_container_width=True, key="K_6_SAVE"):
    if k_ad and k_adet > 0:
        u_eski = kur_getir(k_tar)
        yeni_fon = {
            "kod": k_ad, "tarih": k_tar, "adet": k_adet, 
            "maliyet": k_alis, "guncel": k_guncel if k_guncel > 0 else k_alis,
            "usd_old": u_eski
        }
        st.session_state['ANA_LISTE'].append(yeni_fon)
        st.success("Başarıyla eklendi!")
        st.rerun()
    else:
        st.error("Lütfen tüm alanları (özellikle Kod ve Adet) doldurun.")

st.write("---")

# 5. LİSTELEME VE HESAPLAMA
if st.session_state['ANA_LISTE']:
    st.subheader("📊 Güncel Liste")
    
    # Anlık kur
    u_simdi = yf.download("USDTRY=X", period="1d", progress=False)['Close'].iloc[-1]
    
    df_verisi = []
    for i, f in enumerate(st.session_state['ANA_LISTE']):
        top_m = f['adet'] * f['maliyet']
        top_g = f['adet'] * f['guncel']
        
        df_verisi.append({
            "FON": f['kod'],
            "TARİH": f['tarih'],
            "TOPLAM ALIŞ": f"{top_m:,.2f} TL",
            "GÜNCEL DEĞER": f"{top_g:,.2f} TL",
            "DOLAR FARKI": f"{((top_g/u_simdi) - (top_m/f['usd_old'])):,.2f} $"
        })
        
        if st.button(f"SİL: {f['kod']} - {f['tarih']}", key=f"SIL_ID_{i}"):
            st.session_state['ANA_LISTE'].pop(i)
            st.rerun()

    st.table(df_verisi)
else:
    st.info("Portföyünüzde henüz fon bulunmuyor.")
