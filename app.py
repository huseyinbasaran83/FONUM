import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: Hassas Analiz", layout="wide")

# --- 1. VERİTABANI: FON İÇERİKLERİ ---
fund_composition = {
    "AFT": {"detay": {"NVIDIA": 0.18, "APPLE": 0.15, "MICROSOFT": 0.12, "ALPHABET": 0.10, "NAKİT": 0.45}},
    "TCD": {"detay": {"TÜPRAŞ": 0.15, "KOÇ HOLDİNG": 0.12, "ASELSAN": 0.10, "THY": 0.08, "ALTIN": 0.15, "NAKİT": 0.40}},
    "MAC": {"detay": {"THY": 0.18, "BİMAS": 0.14, "EREĞLİ": 0.12, "SAHOL": 0.10, "MGROS": 0.08, "DİĞER": 0.38}},
    "GUM": {"detay": {"GÜMÜŞ": 0.95, "NAKİT": 0.05}},
    "TI3": {"detay": {"FROTO": 0.15, "SISE": 0.12, "TOASO": 0.10, "KCHOL": 0.08, "DİĞER": 0.45}}
}

# --- 2. VERİ ÇEKME MOTORU ---
@st.cache_data(ttl=3600)
def get_historical_data(ticker, date_obj):
    try:
        start_str = date_obj.strftime('%Y-%m-%d')
        end_str = (date_obj + timedelta(days=7)).strftime('%Y-%m-%d')
        data = yf.download(ticker, start=start_str, end=end_str, progress=False)
        return float(data['Close'].iloc[0]) if not data.empty else None
    except: return None

@st.cache_data(ttl=600)
def get_live_price(ticker):
    try:
        data = yf.download(ticker, period="5d", progress=False)
        return float(data['Close'].iloc[-1]) if not data.empty else None
    except: return None

# Güncel fiyatlarda da hassasiyeti korumak için 6 basamak formatı kullanılabilir
live_fund_prices = {"AFT": 185.402134, "TCD": 12.805567, "MAC": 245.150000, "GUM": 0.451234, "TI3": 4.129876}

# --- 3. SESSION STATE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 4. SIDEBAR: GİRİŞ ---
with st.sidebar:
    st.header("📥 Yeni Fon Girişi")
    f_code = st.text_input("Fon Kodu").upper()
    f_qty = st.number_input("Adet", min_value=0.000001, value=1.0, format="%.6f")
    # Hassasiyeti 6 basamağa çıkardık
    f_cost = st.number_input("Alış Maliyeti (TL)", min_value=0.000001, value=0.000000, format="%.6f")
    f_date = st.date_input("Alış Tarihi", value=datetime.now() - timedelta(days=365))
    
    if st.button("➕ Portföye Ekle", use_container_width=True):
        if f_code and f_cost > 0:
            with st.spinner("Veriler alınıyor..."):
                u_old = get_historical_data("USDTRY=X", f_date)
                g_ons_old = get_historical_data("GC=F", f_date)
                if u_old and g_ons_old:
                    g_old = (g_ons_old / 31.10) * u_old
                    st.session_state.portfolio.append({
                        "kod": f_code, "adet": f_qty, "maliyet": f_cost, "tarih": f_date,
                        "usd_maliyet": u_old, "
