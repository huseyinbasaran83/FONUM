import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Portföy: Reel Getiri Agent", layout="wide")

# --- CANLI & GEÇMİŞ VERİ MOTORU ---
@st.cache_data
def get_historical_data(ticker, date):
    try:
        data = yf.download(ticker, start=date, end=date.replace(day=date.day+3 if date.day < 25 else date.day))
        return data['Close'].iloc[0]
    except:
        return None

def get_live_price(ticker):
    try:
        return yf.Ticker(ticker).fast_info['last_price']
    except:
        return None

# Temsili Fon Fiyatları (Gerçek API yoksa buradan simüle edilir)
live_fund_prices = {"AFT": 185.40, "TCD": 12.80, "MAC": 245.15, "GUM": 0.45, "TI3": 4.12}

# --- Session State ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- Sidebar: Gelişmiş Giriş ---
with st.sidebar:
    st.header("📅 İşlem Kaydı")
    f_code = st.text_input("Fon Kodu").upper()
    f_qty = st.number_input("Adet", min_value=1.0, value=100.0)
    f_cost = st.number_input("Birim Alış Maliyeti (TL)", min_value=0.0)
    f_date = st.date_input("Alış Tarihi", value=datetime(2023, 1, 1))
    
    if st.button("➕ İşlemi Analize Ekle", use_container_width=True):
        with st.spinner("Geçmiş kurlar çekiliyor..."):
            usd_old = get_historical_data("USDTRY=X", f_date)
            gold_old = get_historical_data("GC=F", f_date) # Ons bazlı, TRY'ye çevrilecek
            gbp_old = get_historical_data("GBPTRY=X", f_date)
            
            st.session_state.portfolio.append({
                "kod": f_code, "adet": f_qty, "maliyet": f_cost, "tarih": f_date,
                "usd_maliyet": usd_old, "gold_maliyet": gold_old, "gbp_maliyet": gbp_old
            })
            st.rerun()

# --- Ana Ekran ---
st.title("⚖️ Zenith: Fırsat Maliyeti & Reel Getiri")

if st.session_state.portfolio:
    # Veri İşleme
    df = pd.DataFrame(st.session_state.portfolio)
    
    # Güncel Verileri Çek
    usd_now = get_live_price("USDTRY=X")
    gbp_now = get_live_price("GBPTRY=X")
    
    df['Güncel Fiyat'] = df['kod'].map(live_fund_prices).fillna(df['maliyet'] * 1.2)
    df['Toplam Maliyet'] = df['adet'] * df['maliyet']
    df['Güncel Değer'] = df['adet'] * df['Güncel Fiyat']
    
    # Kar-Zarar Hesapları
    df['Net Kar TL'] = df['Güncel Değer'] - df['Toplam Maliyet']
    
    # REEL GETİRİ ANALİZİ (Dolar/Altın Karşılığı)
    df['Dolar Bazlı Kar %'] = ((df['Güncel Değer'] / usd_now) / (df['Toplam Maliyet'] / df['usd_maliyet']) - 1) * 100
    df['GBP Bazlı Kar %'] = ((df['Güncel Değer'] / gbp_now) / (df['Toplam Maliyet'] / df['gbp_maliyet']) - 1) * 100

    # Metrikler
    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Portföy", f"{df['Güncel Değer'].sum():,.2f} ₺")
    m2.metric("USD Bazlı Reel Getiri", f"% {df['Dolar Bazlı Kar %'].mean():.2f}")
    m3.metric("GBP Bazlı Reel Getiri", f"% {df['GBP Bazlı Kar %'].mean():.2f}")

    st.divider()
    
    # PERFORMANS TABLOSU
    st.subheader("📊 Döviz Bazlı Performans Karşılaştırması")
    st.write("*(Eksi değerler, fonun ilgili döviz biriminden daha az kazandırdığını gösterir)*")
    
    styled_df = df[['kod', 'tarih', 'Net Kar TL', 'Dolar Bazlı Kar %', 'GBP Bazlı Kar %']]
    st.dataframe(styled_df.style.background_gradient(cmap='RdYlGn', subset=['Dolar Bazlı Kar %', 'GBP Bazlı Kar %']), use_container_width=True)

    # GÖRSELLEŞTİRME
    st.subheader("🎯 Fon vs Döviz: Kim Daha Çok Kazandırdı?")
    fig = px.bar(df, x='kod', y=['Dolar Bazlı Kar %', 'GBP Bazlı Kar %'], 
                 barmode='group', title="Döviz Bazlı Görece Performans")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Analiz için fon kodu, adet, maliyet ve tarih giriniz. Sistem o günkü kurları otomatik bulacaktır.")
