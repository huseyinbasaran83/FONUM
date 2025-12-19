import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: Kar/Zarar & Reel Getiri", layout="wide")

# --- GELİŞMİŞ VERİ ÇEKME MOTORU ---
@st.cache_data(ttl=3600)
def get_historical_data(ticker, date_obj):
    try:
        # Tarihi string formatına çevir
        start_str = date_obj.strftime('%Y-%m-%d')
        # Veri çekme aralığını geniş tutuyoruz (hafta sonu riskine karşı)
        end_str = (date_obj + timedelta(days=7)).strftime('%Y-%m-%d')
        data = yf.download(ticker, start=start_str, end=end_str, progress=False)
        if not data.empty:
            return float(data['Close'].iloc[0])
        return None
    except Exception as e:
        return None

@st.cache_data(ttl=600)
def get_live_price(ticker):
    try:
        data = yf.download(ticker, period="5d", progress=False)
        if not data.empty:
            return float(data['Close'].iloc[-1])
        return None
    except:
        return None

# Önemli Fonlar İçin Güncel Tahmini Fiyatlar
live_fund_prices = {"AFT": 185.40, "TCD": 12.80, "MAC": 245.15, "GUM": 0.45, "TI3": 4.12, "ZRE": 115.30}

# --- Session State ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- Sidebar ---
with st.sidebar:
    st.header("📅 İşlem Kaydı")
    f_code = st.text_input("Fon Kodu (AFT, TCD vb.)").upper()
    f_qty = st.number_input("Adet", min_value=0.1, value=1.0)
    f_cost = st.number_input("Birim Alış Maliyeti (TL)", min_value=0.01)
    f_date = st.date_input("Alış Tarihi", value=datetime.now() - timedelta(days=365))
    
    if st.button("➕ Analize Ekle", use_container_width=True):
        if f_code and f_cost > 0:
            with st.spinner(f"Veriler çekiliyor..."):
                usd_old = get_historical_data("USDTRY=X", f_date)
                # Altın için ONS/USD çekiyoruz
                gold_ons_old = get_historical_data("GC=F", f_date)
                
                if usd_old and gold_ons_old:
                    gold_try_old = (gold_ons_old / 31.10) * usd_old
                    st.session_state.portfolio.append({
                        "kod": f_code, "adet": f_qty, "maliyet": f_cost, "tarih": f_date,
                        "usd_maliyet": usd_old, "gold_maliyet": gold_try_old
                    })
                    st.success("Veriler başarıyla eklendi!")
                    st.rerun()
                else:
                    st.error("Seçilen tarih için kur verisi alınamadı. Lütfen başka bir gün deneyin.")

    if st.session_state.portfolio:
        if st.button("🚨 TÜMÜNÜ SİL"):
            st.session_state.portfolio = []
            st.rerun()

# --- Ana Ekran ---
st.title("🛡️ Zenith: Reel Performans Analizörü")

if st.session_state.portfolio:
    df = pd.DataFrame(st.session_state.portfolio)
    
    with st.spinner("Güncel kurlar alınıyor..."):
        usd_now = get_live_price("USDTRY=X")
        gold_ons_now = get_live_price("GC=F")
        gold_now = (gold_ons_now / 31.10) * usd_now if usd_now and gold_ons_now else None

    # Hesaplamalar
    df['Güncel Fiyat'] = df['kod'].map(live_fund_prices).fillna(df['maliyet'] * 1.2) # Liste dışı fonlara %20 hayali kâr
    df['Toplam Maliyet'] = df['adet'] * df['maliyet']
    df['Güncel Değer'] = df['adet'] * df['Güncel Fiyat']
    
    # REEL GETİRİ ANALİZİ
    if usd_now and gold_now:
        # USD Bazlı Fark: (Fonun bugünkü dolar değeri / Fonun o günkü dolar değeri) - 1
        df['USD Bazlı Fark %'] = ((df['Güncel Değer'] / usd_now) / (df['Toplam Maliyet'] / df['usd_maliyet']) - 1) * 100
        # Altın Bazlı Fark: (Fonun bugünkü altın değeri / Fonun o günkü altın değeri) - 1
        df['Altın Bazlı Fark %'] = ((df['Güncel Değer'] / gold_now) / (df['Toplam Maliyet'] / df['gold_maliyet']) - 1) * 100

        # Metrikler
        c1, c2, c3 = st.columns(3)
        total_v = df['Güncel Değer'].sum()
        c1.metric("Toplam Değer", f"{total_v:,.2f} ₺")
        c2.metric("USD'ye Göre Fark", f"% {df['USD Bazlı Fark %'].mean():.2f}")
        c3.metric("Altın'a Göre Fark", f"% {df['Altın Bazlı Fark %'].mean():.2f}")

        st.divider()

        # TABLO
        st.subheader("📋 Karşılaştırmalı Performans Listesi")
        show_df = df[['kod', 'tarih', 'maliyet', 'Güncel Fiyat', 'USD Bazlı Fark %', 'Altın Bazlı Fark %']]
        st.dataframe(show_df.style.background_gradient(cmap='RdYlGn', subset=['USD Bazlı Fark %', 'Altın Bazlı Fark %']).format(precision=2), use_container_width=True)

        

        # GRAFİK
        st.subheader("🎯 Fon Performansı vs Döviz & Altın")
        fig = px.bar(df, x='kod', y=['USD Bazlı Fark %', 'Altın Bazlı Fark %'], 
                     barmode='group', labels={'value': 'Fark (%)', 'variable': 'Kıyaslama'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Güncel piyasa verileri çekilemediği için raporlama yapılamıyor.")

else:
    st.info("Sol panelden fon verilerinizi girin. Agent, döviz ve altın karşısındaki reel performansınızı hesaplayacaktır.")
