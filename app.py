import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: TEFAS Veri Senkronu", layout="wide")

# --- 1. GENİŞLETİLMİŞ KAP VERİTABANI ---
KAP_DATA = {
    "TCD": {"TUPRS": 0.14, "KCHOL": 0.12, "ASELS": 0.11, "THYAO": 0.09, "ALTIN": 0.15, "DİĞER": 0.39},
    "MAC": {"THYAO": 0.16, "MGROS": 0.13, "EREGL": 0.11, "SAHOL": 0.10, "KCHOL": 0.08, "DİĞER": 0.32},
    "TI3": {"FROTO": 0.14, "SISE": 0.12, "TOASO": 0.11, "KCHOL": 0.10, "TUPRS": 0.07, "DİĞER": 0.46},
    "AFT": {"NVIDIA": 0.20, "APPLE": 0.16, "MICROSOFT": 0.14, "ALPHABET": 0.12, "META": 0.10, "NAKİT": 0.28},
    "ZRE": {"THYAO": 0.12, "TUPRS": 0.11, "AKBNK": 0.10, "ISCTR": 0.10, "KCHOL": 0.09, "DİĞER": 0.48},
    "NNF": {"THYAO": 0.12, "PGSUS": 0.10, "TUPRS": 0.09, "KCHOL": 0.08, "BIMAS": 0.08, "DİĞER": 0.53},
    "GMR": {"PGSUS": 0.13, "TAVHL": 0.11, "MGROS": 0.10, "YKBNK": 0.09, "BIMAS": 0.08, "DİĞER": 0.49},
}

# --- 2. CANLI KUR MOTORU ---
@st.cache_data(ttl=3600)
def get_hist_kur(ticker, date_obj):
    try:
        data = yf.download(ticker, start=date_obj.strftime('%Y-%m-%d'), end=(date_obj + timedelta(days=7)).strftime('%Y-%m-%d'), progress=False)
        return float(data['Close'].iloc[0]) if not data.empty else None
    except: return None

@st.cache_data(ttl=600)
