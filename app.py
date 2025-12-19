import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: Tam Yönetim & Analiz", layout="wide")

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

live_fund_prices = {"AFT": 185.40, "TCD": 12.80, "MAC": 245.15, "GUM": 0.45, "TI3": 4.12}

# --- 3. SESSION STATE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 4. SIDEBAR: GİRİŞ ---
with st.sidebar:
    st.header("📥 Yeni Fon Girişi")
    f_code = st.text_input("Fon Kodu").upper()
    f_qty = st.number_input("Adet", min_value=0.1, value=1.0)
    f_cost = st.number_input("Alış Maliyeti (TL)", min_value=0.01)
    f_date = st.date_input("Alış Tarihi", value=datetime.now() - timedelta(days=365))
    
    if st.button("➕ Portföye Ekle", use_container_width=True):
        if f_code:
            with st.spinner("Veriler alınıyor..."):
                u_old = get_historical_data("USDTRY=X", f_date)
                g_ons_old = get_historical_data("GC=F", f_date)
                if u_old and g_ons_old:
                    g_old = (g_ons_old / 31.10) * u_old
                    st.session_state.portfolio.append({
                        "kod": f_code, "adet": f_qty, "maliyet": f_cost, "tarih": f_date,
                        "usd_maliyet": u_old, "gold_maliyet": g_old
                    })
                    st.rerun()

# --- 5. ANA EKRAN ---
st.title("🛡️ Zenith Pro: 360° Akıllı Portföy")

if st.session_state.portfolio:
    # --- YÖNETİM PANELİ ---
    st.subheader("⚙️ Portföy Yönetimi (Adet, Maliyet ve Tarih Değiştir)")
    usd_now = get_live_price("USDTRY=X")
    gold_now = (get_live_price("GC=F") / 31.10) * usd_now if usd_now else 1
    
    for idx, item in enumerate(st.session_state.portfolio):
        c_name, c_qty, c_cost, c_date, c_del = st.columns([1, 1, 1, 1.5, 0.5])
        
        with c_name:
            st.write(f"**{item['kod']}**")
        
        with c_qty:
            st.session_state.portfolio[idx]['adet'] = st.number_input("Adet", value=float(item['adet']), key=f"q_{idx}")
            
        with c_cost:
            st.session_state.portfolio[idx]['maliyet'] = st.number_input("Maliyet", value=float(item['maliyet']), key=f"m_{idx}")
            
        with c_date:
            # Tarih değiştirme özelliği eklendi
            new_date = st.date_input("Alış Tarihi", value=item['tarih'], key=f"d_{idx}")
            if new_date != item['tarih']:
                # Tarih değiştiyse kurları yeniden çek
                with st.spinner("Yeni tarihin kurları çekiliyor..."):
                    u_old = get_historical_data("USDTRY=X", new_date)
                    g_ons_old = get_historical_data("GC=F", new_date)
                    if u_old and g_ons_old:
                        st.session_state.portfolio[idx]['tarih'] = new_date
                        st.session_state.portfolio[idx]['usd_maliyet'] = u_old
                        st.session_state.portfolio[idx]['gold_maliyet'] = (g_ons_old / 31.10) * u_old
                        st.rerun()
        
        with c_del:
            if st.button("🗑️", key=f"del_{idx}"):
                st.session_state.portfolio.pop(idx)
                st.rerun()

    st.divider()

    # --- HESAPLAMALAR ---
    df = pd.DataFrame(st.session_state.portfolio)
    df['Güncel Fiyat'] = df['kod'].map(live_fund_prices).fillna(df['maliyet'] * 1.1)
    df['G. Değer'] = df['adet'] * df['Güncel Fiyat']
    df['T. Maliyet'] = df['adet'] * df['maliyet']
    
    # Reel Getiri Hesaplama
    df['USD Fark %'] = ((df['G. Değer'] / usd_now) / (df['T. Maliyet'] / df['usd_maliyet']) - 1) * 100
    df['Altın Fark %'] = ((df['G. Değer'] / gold_now) / (df['T. Maliyet'] / df['gold_maliyet']) - 1) * 100

    # --- ANALİZ SEKMELERİ ---
    tab1, tab2 = st.tabs(["📈 Reel Performans", "💎 Varlık Röntgeni"])

    with tab1:
        st.subheader("USD ve Altın Karşısındaki Durum")
        st.dataframe(df[['kod', 'tarih', 'USD Fark %', 'Altın Fark %']].style.background_gradient(cmap='RdYlGn'), use_container_width=True)
        st.plotly_chart(px.bar(df, x='kod', y=['USD Fark %', 'Altın Fark %'], barmode='group'), use_container_width=True)

    with tab2:
        st.subheader("Portföy İçindeki Şirket ve Varlık Dağılımı")
        asset_map = {}
        for _, row in df.iterrows():
            comp = fund_composition.get(row['kod'], {"detay": {"DİĞER": 1.0}})['detay']
            for asset, ratio in comp.items():
                asset_map[asset] = asset_map.get(asset, 0) + (row['G. Değer'] * ratio)
        
        breakdown_df = pd.DataFrame(list(asset_map.items()), columns=['Varlık', 'Değer']).sort_values(by='Değer', ascending=False)
        
        col_pie, col_list = st.columns([1.5, 1])
        with col_pie:
            st.plotly_chart(px.pie(breakdown_df, values='Değer', names='Varlık', hole=0.4), use_container_width=True)
        with col_list:
            st.table(breakdown_df.style.format({'Değer': '{:,.2f} ₺'}))

    st.divider()
    st.metric("Toplam Portföy Değeri", f"{df['G. Değer'].sum():,.2f} ₺")

else:
    st.info("Henüz fon eklenmemiş. Sol taraftan işlem girişi yapabilirsiniz.")
