import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Portföy: Reel Getiri Agent", layout="wide")

# --- CANLI & GEÇMİŞ VERİ MOTORU ---
@st.cache_data(ttl=3600)
def get_historical_data(ticker, date_obj):
    try:
        # Hafta sonuna denk gelirse diye 5 günlük veri çekip ilk günü alıyoruz
        end_date = date_obj + timedelta(days=5)
        data = yf.download(ticker, start=date_obj.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), progress=False)
        if not data.empty:
            return float(data['Close'].iloc[0])
        return None
    except:
        return None

@st.cache_data(ttl=600)
def get_live_price(ticker):
    try:
        data = yf.download(ticker, period="1d", progress=False)
        return float(data['Close'].iloc[-1])
    except:
        return None

# Temsili Fon Fiyatları (Not: Gerçek fon verileri için manuel giriş gerekebilir)
live_fund_prices = {"AFT": 185.40, "TCD": 12.80, "MAC": 245.15, "GUM": 0.45, "TI3": 4.12}

# --- Session State ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- Sidebar: Gelişmiş Giriş ---
with st.sidebar:
    st.header("📅 İşlem Kaydı")
    f_code = st.text_input("Fon Kodu").upper()
    f_qty = st.number_input("Adet", min_value=0.1, value=100.0)
    f_cost = st.number_input("Birim Alış Maliyeti (TL)", min_value=0.0)
    f_date = st.date_input("Alış Tarihi", value=datetime(2023, 1, 1))
    
    if st.button("➕ İşlemi Analize Ekle", use_container_width=True):
        if f_code:
            with st.spinner(f"{f_date} tarihindeki kurlar çekiliyor..."):
                usd_old = get_historical_data("USDTRY=X", f_date)
                gbp_old = get_historical_data("GBPTRY=X", f_date)
                
                # Altın için ONS/USD çekip o günkü kurla TL'ye çeviriyoruz (Yaklaşık Gram Altın)
                gold_ons_old = get_historical_data("GC=F", f_date)
                gold_old = (gold_ons_old / 31.10) * usd_old if usd_old and gold_ons_old else None
                
                st.session_state.portfolio.append({
                    "kod": f_code, "adet": f_qty, "maliyet": f_cost, "tarih": f_date,
                    "usd_maliyet": usd_old, "gold_maliyet": gold_old, "gbp_maliyet": gbp_old
                })
                st.rerun()

    if st.session_state.portfolio and st.checkbox("⚠️ Listeyi Temizle"):
        if st.button("🚨 TÜMÜNÜ SİL"):
            st.session_state.portfolio = []
            st.rerun()

# --- Ana Ekran ---
st.title("⚖️ Zenith: Fırsat Maliyeti & Reel Getiri")

if st.session_state.portfolio:
    df = pd.DataFrame(st.session_state.portfolio)
    
    with st.spinner("Güncel piyasa verileri çekiliyor..."):
        usd_now = get_live_price("USDTRY=X")
        gbp_now = get_live_price("GBPTRY=X")
        gold_ons_now = get_live_price("GC=F")
        gold_now = (gold_ons_now / 31.10) * usd_now

    df['Güncel Fiyat'] = df['kod'].map(live_fund_prices).fillna(df['maliyet'] * 1.1) # Bilinmeyen fonlar için %10 kâr varsayalım
    df['Toplam Maliyet'] = df['adet'] * df['maliyet']
    df['Güncel Değer'] = df['adet'] * df['Güncel Fiyat']
    df['Net Kar TL'] = df['Güncel Değer'] - df['Toplam Maliyet']
    
    # REEL GETİRİ ANALİZİ (Döviz Karşılığı)
    # Formül: ((Güncel Değer / Güncel Kur) / (Maliyet Değeri / Eski Kur)) - 1
    df['USD Bazlı Fark %'] = ((df['Güncel Değer'] / usd_now) / (df['Toplam Maliyet'] / df['usd_maliyet']) - 1) * 100
    df['Altın Bazlı Fark %'] = ((df['Güncel Değer'] / gold_now) / (df['Toplam Maliyet'] / df['gold_maliyet']) - 1) * 100

    # Metrikler
    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Portföy", f"{df['Güncel Değer'].sum():,.2f} ₺")
    m2.metric("USD Bazlı Ortalama Reel Fark", f"% {df['USD Bazlı Fark %'].mean():.2f}")
    m3.metric("Altın Bazlı Ortalama Reel Fark", f"% {df['Altın Bazlı Fark %'].mean():.2f}")

    st.divider()
    
    # PERFORMANS TABLOSU
    st.subheader("📊 Döviz ve Altın Karşılaştırmalı Performans")
    st.write("*(Pozitif Değer: Fon dövizi yendi | Negatif Değer: Dövizda kalsan daha iyiydi)*")
    
    display_cols = ['kod', 'tarih', 'Net Kar TL', 'USD Bazlı Fark %', 'Altın Bazlı Fark %']
    # Renklendirme için stil uygula
    st.dataframe(df[display_cols].style.background_gradient(cmap='RdYlGn', subset=['USD Bazlı Fark %', 'Altın Bazlı Fark %']), use_container_width=True)

    # GÖRSELLEŞTİRME
    
    st.subheader("🎯 Kim Daha Çok Kazandırdı?")
    fig = px.bar(df, x='kod', y=['USD Bazlı Fark %', 'Altın Bazlı Fark %'], 
                 barmode='group', labels={'value': 'Reel Fark (%)', 'variable': 'Kıyaslama Birimi'})
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Sol taraftan fon kodunu ve alış tarihini girerek başlayın. Agent o günkü kurları otomatik çekip kıyaslayacaktır.")
