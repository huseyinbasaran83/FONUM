import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: Kesin Hisse Analizi", layout="wide")

# --- 1. FON İÇERİKLERİ (KODLARIN TAM EŞLEŞMESİ İÇİN) ---
fund_composition = {
    "AFT": {"NVIDIA": 0.19, "APPLE": 0.16, "MICROSOFT": 0.14, "ALPHABET": 0.11, "META": 0.09, "NAKİT/DİĞER": 0.31},
    "TCD": {"TUPRS": 0.14, "KCHOL": 0.12, "ASELS": 0.11, "THYAO": 0.09, "BIMAS": 0.07, "ALTIN": 0.15, "DİĞER": 0.32},
    "MAC": {"THYAO": 0.16, "MGROS": 0.13, "EREGL": 0.11, "SAHOL": 0.10, "BIMAS": 0.09, "KCHOL": 0.08, "DİĞER": 0.33},
    "TI3": {"FROTO": 0.14, "SISE": 0.12, "TOASO": 0.11, "KCHOL": 0.10, "ARCLK": 0.08, "TUPRS": 0.07, "DİĞER": 0.38},
    "ZRE": {"THYAO": 0.12, "TUPRS": 0.11, "AKBNK": 0.10, "ISCTR": 0.10, "KCHOL": 0.09, "EREGL": 0.08, "DİĞER": 0.40},
    "GMR": {"PGSUS": 0.13, "TAVHL": 0.11, "MGROS": 0.10, "YKBNK": 0.09, "BIMAS": 0.08, "DİĞER": 0.49}
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

# Temsili Güncel Fiyatlar
live_fund_prices = {"AFT": 185.40, "TCD": 12.80, "MAC": 245.15, "GMR": 18.20, "TI3": 4.12, "ZRE": 115.30}

# --- 3. SESSION STATE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 4. SIDEBAR: GİRİŞ ---
with st.sidebar:
    st.header("📥 Yeni Fon Girişi")
    f_code = st.text_input("Fon Kodu").upper().strip() # Boşlukları temizler
    f_qty = st.number_input("Adet", min_value=0.000001, value=1.0)
    f_cost = st.number_input("Birim Alış Maliyeti (TL)", min_value=0.000001, format="%.6f")
    f_date = st.date_input("Alış Tarihi", value=datetime.now() - timedelta(days=365))
    
    if st.button("➕ Portföye Ekle", use_container_width=True):
        if f_code and f_cost > 0:
            with st.spinner("Kurlar alınıyor..."):
                u_old = get_historical_data("USDTRY=X", f_date)
                g_ons_old = get_historical_data("GC=F", f_date)
                if u_old and g_ons_old:
                    st.session_state.portfolio.append({
                        "kod": f_code, "adet": f_qty, "maliyet": f_cost, "tarih": f_date,
                        "usd_maliyet": u_old, "gold_maliyet": (g_ons_old / 31.10) * u_old
                    })
                    st.rerun()

# --- 5. ANA EKRAN ---
st.title("🛡️ Zenith Pro: Kesin Hisse Dağılım Raporu")

if st.session_state.portfolio:
    # --- YÖNETİM PANELİ ---
    st.subheader("⚙️ Portföy Yönetimi")
    usd_now = get_live_price("USDTRY=X") or 34.0
    gold_now = ((get_live_price("GC=F") or 2600.0) / 31.10) * usd_now
    
    for idx, item in enumerate(st.session_state.portfolio):
        c_name, c_qty, c_cost, c_date, c_del = st.columns([1, 1, 1.2, 1.3, 0.5])
        with c_name: st.write(f"**{item['kod']}**")
        with c_qty: st.session_state.portfolio[idx]['adet'] = st.number_input("Adet", value=float(item['adet']), key=f"q_{idx}")
        with c_cost: st.session_state.portfolio[idx]['maliyet'] = st.number_input("Maliyet", value=float(item['maliyet']), key=f"m_{idx}", format="%.6f")
        with c_date: 
            st.session_state.portfolio[idx]['tarih'] = st.date_input("Tarih", value=item['tarih'], key=f"d_{idx}")
        with c_del:
            if st.button("🗑️", key=f"del_{idx}"):
                st.session_state.portfolio.pop(idx); st.rerun()

    st.divider()

    # --- HESAPLAMALAR ---
    df = pd.DataFrame(st.session_state.portfolio)
    df['G. Fiyat'] = df['kod'].map(live_fund_prices).fillna(df['maliyet'] * 1.1)
    df['G. Değer'] = df['adet'] * df['G. Fiyat']
    df['T. Maliyet'] = df['adet'] * df['maliyet']
    
    tab1, tab2 = st.tabs(["📈 Reel Getiri Analizi", "💎 Hisse Senedi Dağılım Raporu"])

    with tab1:
        df['USD Fark %'] = ((df['G. Değer']/usd_now)/(df['T. Maliyet']/df['usd_maliyet'])-1)*100
        df['Altın Fark %'] = ((df['G. Değer']/gold_now)/(df['T. Maliyet']/df['gold_maliyet'])-1)*100
        st.dataframe(df[['kod', 'tarih', 'maliyet', 'USD Fark %', 'Altın Fark %']].style.format({'maliyet': '{:.6f}'}).background_gradient(cmap='RdYlGn'), use_container_width=True)

    with tab2:
        st.subheader("Hisse Senedi ve Varlık Detayları")
        hisse_data = []
        
        for _, row in df.iterrows():
            # Fon kodunu bulamazsa fonun kendisini %100 hisseymiş gibi listeye ekler
            target_fund = row['kod'].strip().upper()
            comp = fund_composition.get(target_fund, {f"{target_fund} (Diğer/Bilinmeyen)": 1.0})
            
            for asset, ratio in comp.items():
                hisse_data.append({
                    "Hisse/Varlık": asset,
                    "TL Değeri": row['G. Değer'] * ratio
                })
        
        final_hisse_df = pd.DataFrame(hisse_data).groupby("Hisse/Varlık").sum().reset_index().sort_values(by="TL Değeri", ascending=False)
        final_hisse_df["Yüzde (%)"] = (final_hisse_df["TL Değeri"] / final_hisse_df["TL Değeri"].sum()) * 100

        

        c_pie, c_table = st.columns([1.5, 1])
        with c_pie:
            st.plotly_chart(px.pie(final_hisse_df, values='TL Değeri', names='Hisse/Varlık', hole=0.4, title="Toplam Portföy Dağılımı"), use_container_width=True)
        with c_table:
            st.write("**Detaylı Liste**")
            st.dataframe(final_hisse_df.style.format({'TL Değeri': '{:,.2f} ₺', 'Yüzde (%)': '% {:.2f}'}), use_container_width=True)

    st.divider()
    st.metric("Toplam Portföy", f"{df['G. Değer'].sum():,.2f} ₺")
else:
    st.info("Portföyünüz boş. Lütfen fon ekleyin.")
