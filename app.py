import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: Yönetim & Reel Getiri", layout="wide")

# --- VERİ ÇEKME MOTORU ---
@st.cache_data(ttl=3600)
def get_historical_data(ticker, date_obj):
    try:
        start_str = date_obj.strftime('%Y-%m-%d')
        end_str = (date_obj + timedelta(days=7)).strftime('%Y-%m-%d')
        data = yf.download(ticker, start=start_str, end=end_str, progress=False)
        return float(data['Close'].iloc[0]) if not data.empty else None
    except:
        return None

@st.cache_data(ttl=600)
def get_live_price(ticker):
    try:
        data = yf.download(ticker, period="5d", progress=False)
        return float(data['Close'].iloc[-1]) if not data.empty else None
    except:
        return None

# Sabit Fon Fiyatları (Örnek)
live_fund_prices = {"AFT": 185.40, "TCD": 12.80, "MAC": 245.15, "GUM": 0.45, "TI3": 4.12, "ZRE": 115.30}

# --- Session State ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- Sidebar: Yeni Kayıt ---
with st.sidebar:
    st.header("📥 Yeni Fon Girişi")
    f_code = st.text_input("Fon Kodu").upper()
    f_qty = st.number_input("Adet", min_value=0.1, value=1.0)
    f_cost = st.number_input("Alış Maliyeti (TL)", min_value=0.01)
    f_date = st.date_input("Alış Tarihi", value=datetime.now() - timedelta(days=365))
    
    if st.button("➕ Portföye Ekle", use_container_width=True):
        if f_code and f_cost > 0:
            with st.spinner("Kurlar alınıyor..."):
                u_old = get_historical_data("USDTRY=X", f_date)
                g_ons_old = get_historical_data("GC=F", f_date)
                if u_old and g_ons_old:
                    g_old = (g_ons_old / 31.10) * u_old
                    st.session_state.portfolio.append({
                        "kod": f_code, "adet": f_qty, "maliyet": f_cost, "tarih": f_date,
                        "usd_maliyet": u_old, "gold_maliyet": g_old
                    })
                    st.rerun()
                else:
                    st.error("O tarihe ait kur verisi bulunamadı.")

# --- Ana Ekran ---
st.title("🛡️ Zenith: Yönetim & Reel Performans")

if st.session_state.portfolio:
    # 1. YÖNETİM VE DÜZENLEME PANELİ
    st.subheader("⚙️ Portföy Yönetimi (Düzenle/Sil)")
    
    # Güncel kurları bir kez çekelim
    usd_now = get_live_price("USDTRY=X")
    gold_ons_now = get_live_price("GC=F")
    gold_now = (gold_ons_now / 31.10) * usd_now if usd_now and gold_ons_now else 1
    
    # Satır satır düzenleme alanı
    for idx, item in enumerate(st.session_state.portfolio):
        c1, c2, c3, c4, c5 = st.columns([1, 1.5, 1.5, 2, 0.5])
        with c1:
            st.write(f"**{item['kod']}**\n*{item['tarih']}*")
        with c2:
            st.session_state.portfolio[idx]['adet'] = st.number_input("Adet", value=float(item['adet']), key=f"q_{idx}")
        with c3:
            st.session_state.portfolio[idx]['maliyet'] = st.number_input("Maliyet", value=float(item['maliyet']), key=f"m_{idx}")
        with c4:
            curr_p = live_fund_prices.get(item['kod'], item['maliyet'] * 1.2)
            val = st.session_state.portfolio[idx]['adet'] * curr_p
            st.write(f"Güncel Değer: **{val:,.2f} ₺**")
        with c5:
            if st.button("🗑️", key=f"del_{idx}"):
                st.session_state.portfolio.pop(idx)
                st.rerun()

    st.divider()

    # 2. ANALİZ VE RAPORLAMA
    df = pd.DataFrame(st.session_state.portfolio)
    df['Güncel Fiyat'] = df['kod'].map(live_fund_prices).fillna(df['maliyet'] * 1.2)
    df['Güncel Değer'] = df['adet'] * df['Güncel Fiyat']
    df['Toplam Maliyet'] = df['adet'] * df['maliyet']
    
    # Reel Getiri Hesaplama
    df['USD Fark %'] = ((df['Güncel Değer'] / usd_now) / (df['Toplam Maliyet'] / df['usd_maliyet']) - 1) * 100
    df['Altın Fark %'] = ((df['Güncel Değer'] / gold_now) / (df['Toplam Maliyet'] / df['gold_maliyet']) - 1) * 100

    # Üst Metrikler
    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Portföy", f"{df['Güncel Değer'].sum():,.2f} ₺")
    m2.metric("USD Reel Getiri (Ort)", f"% {df['USD Fark %'].mean():.2f}")
    m3.metric("Altın Reel Getiri (Ort)", f"% {df['Altın Fark %'].mean():.2f}")

    # Rapor Tablosu
    st.subheader("📊 Reel Performans Raporu")
    st.dataframe(df[['kod', 'tarih', 'USD Fark %', 'Altın Fark %']].style.background_gradient(cmap='RdYlGn', subset=['USD Fark %', 'Altın Fark %']), use_container_width=True)

    # Grafik
    
    st.plotly_chart(px.bar(df, x='kod', y=['USD Fark %', 'Altın Fark %'], barmode='group', title="Döviz & Altın Karşısındaki Durum"), use_container_width=True)

else:
    st.info("Portföy boş. Sol taraftan fon ekleyerek başlayın.")
