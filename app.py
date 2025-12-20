import streamlit as st
import pandas as pd
import yfinance as yf
import json
from datetime import datetime, timedelta

st.set_page_config(page_title="Zenith Pro: Kurtarma Modu", layout="wide")

# --- 1. VERİLERİNİ KODA GÖMDÜK (DOSYA YÜKLENEMEZSE BURADAN ÇALIŞIR) ---
SABIT_VERI = [
    {"kod": "NLE", "tarih": "2025-06-04", "adet": 13922.0, "maliyet": 1.005556, "guncel": 1.259509, "usd_old": 39.1445999, "gbp_old": 52.9526, "gold_old": 4246.11},
    {"kod": "NLE", "tarih": "2025-07-29", "adet": 20262.0, "maliyet": 1.243136, "guncel": 1.259509, "usd_old": 40.561698, "gbp_old": 54.1986, "gold_old": 4334.49},
    {"kod": "TTE", "tarih": "2024-02-06", "adet": 14955.0, "maliyet": 0.787447, "guncel": 0.991358, "usd_old": 30.536800, "gbp_old": 38.2068, "gold_old": 1997.65},
    {"kod": "DTM", "tarih": "2025-06-13", "adet": 11064.0, "maliyet": 0.994418, "guncel": 1.145821, "usd_old": 39.395599, "gbp_old": 53.6745, "gold_old": 4346.43},
    {"kod": "ICZ", "tarih": "2024-02-06", "adet": 1781.0, "maliyet": 4.399736, "guncel": 5.894043, "usd_old": 30.536800, "gbp_old": 38.2068, "gold_old": 1997.65},
    {"kod": "BDS", "tarih": "2025-04-09", "adet": 1180.0, "maliyet": 1.694492, "guncel": 2.370899, "usd_old": 38.007999, "gbp_old": 48.5092, "gold_old": 3735.41},
    {"kod": "BDS", "tarih": "2025-09-18", "adet": 3213.0, "maliyet": 2.489381, "guncel": 2.370899, "usd_old": 41.301101, "gbp_old": 56.2959, "gold_old": 4838.86},
    {"kod": "KOT", "tarih": "2025-08-26", "adet": 4004.0, "maliyet": 1.248606, "guncel": 1.22724, "usd_old": 41.003501, "gbp_old": 55.1604, "gold_old": 4467.66},
    {"kod": "KOT", "tarih": "2025-11-03", "adet": 4164.0, "maliyet": 1.200711, "guncel": 1.22724, "usd_old": 42.039619, "gbp_old": 55.2497, "gold_old": 5407.43},
    {"kod": "IIH", "tarih": "2024-02-06", "adet": 283.0, "maliyet": 17.322261, "guncel": 27.889396, "usd_old": 30.536800, "gbp_old": 38.2068, "gold_old": 1997.65},
    {"kod": "IIH", "tarih": "2025-03-14", "adet": 76.0, "maliyet": 26.2125, "guncel": 27.889396, "usd_old": 36.679599, "gbp_old": 47.5218, "gold_old": 3531.73}
]

# Belleği başlat ve eğer boşsa sabit veriyi yükle
if 'portfolio' not in st.session_state or len(st.session_state.portfolio) == 0:
    for item in SABIT_VERI:
        if isinstance(item['tarih'], str):
            item['tarih'] = datetime.strptime(item['tarih'], '%Y-%m-%d').date()
    st.session_state.portfolio = SABIT_VERI

# --- 2. GİRİŞ ALANLARI (ALT ALTA VE KESİN) ---
st.title("🛡️ Zenith Pro: Kesin Kayıt Paneli")

with st.expander("➕ YENİ FON EKLEME ALANI", expanded=True):
    f_kod = st.text_input("FON KODU").upper()
    f_tar = st.date_input("ALIŞ TARİHİ")
    f_adet = st.number_input("ADET", format="%.4f")
    f_alis = st.number_input("BİRİM ALIŞ (₺)", format="%.4f")
    f_gun = st.number_input("BİRİM GÜNCEL (₺) <--- ARADIĞINIZ HÜCRE BURADA", format="%.4f")
    
    if st.button("🚀 LİSTEYE EKLE VE HESAPLA"):
        if f_kod and f_adet > 0:
            # Otomatik dolar kuru (geçmiş)
            u_o = yf.download("USDTRY=X", start=f_tar, end=(f_tar + timedelta(days=5)), progress=False)['Close'].iloc[0]
            st.session_state.portfolio.append({
                "kod": f_kod, "tarih": f_tar, "adet": f_adet, "maliyet": f_alis, "guncel": f_gun, "usd_old": u_o
            })
            st.success("Eklendi!")
            st.rerun()

st.divider()

# --- 3. TABLO VE GÜNCEL KURLAR ---
if st.session_state.portfolio:
    u_n = yf.download("USDTRY=X", period="1d", progress=False)['Close'].iloc[-1]
    
    st.subheader("📋 Mevcut Portföy Analizi")
    sonuclar = []
    for i, f in enumerate(st.session_state.portfolio):
        m_top = f['adet'] * f['maliyet']
        g_top = f['adet'] * f['guncel']
        
        sonuclar.append({
            "KOD": f['kod'],
            "ADET": f['adet'],
            "TOPLAM ALIŞ": f"{m_top:,.2f} ₺",
            "GÜNCEL DEĞER": f"{g_top:,.2f} ₺",
            "DOLAR FARKI ($)": f"{((g_top/u_n) - (m_top/f['usd_old'])):,.2f} $"
        })
        if st.button(f"🗑️ Sil: {f['kod']} ({i})", key=f"del_{i}"):
            st.session_state.portfolio.pop(i)
            st.rerun()

    st.table(sonuclar)
