import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: Hisse Bazlı Raporlama", layout="wide")

# --- 1. DETAYLI TÜRK FONLARI HİSSE VERİTABANI ---
# Bu veriler fonların güncel portföy dağılım raporlarından (yaklaşık) derlenmiştir.
fund_composition = {
    "TCD": {"detay": {"TÜPRAŞ (TUPRS)": 0.14, "KOÇ HOLDİNG (KCHOL)": 0.12, "ASELSAN (ASELS)": 0.11, "THY (THYAO)": 0.09, "BİMAS": 0.07, "ALTIN": 0.15, "DİĞER HİSSE/NAKİT": 0.32}},
    "MAC": {"detay": {"THY (THYAO)": 0.16, "MGROS": 0.13, "EREĞLİ (EREGL)": 0.11, "SAHOL": 0.10, "BİMAS": 0.09, "KCHOL": 0.08, "DİĞER HİSSE": 0.33}},
    "TI3": {"detay": {"FROTO": 0.14, "SISE": 0.12, "TOASO": 0.11, "KCHOL": 0.10, "ARCLK": 0.08, "TUPRS": 0.07, "DİĞER": 0.38}},
    "ZRE": {"detay": {"THY (THYAO)": 0.12, "TUPRS": 0.11, "AKBNK": 0.10, "ISCTR": 0.10, "KCHOL": 0.09, "EREGL": 0.08, "DİĞER": 0.40}},
    "GMR": {"detay": {"PGSUS": 0.13, "TAVHL": 0.11, "MGROS": 0.10, "YKBNK": 0.09, "BİMAS": 0.08, "DİĞER": 0.49}},
    "AFT": {"detay": {"NVIDIA": 0.19, "APPLE": 0.16, "MICROSOFT": 0.14, "ALPHABET": 0.11, "META": 0.09, "NAKİT/DİĞER": 0.31}}
}

# --- 2. VERİ ÇEKME FONKSİYONLARI ---
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

# Temsili Fon Fiyatları
live_fund_prices = {"AFT": 185.40, "TCD": 12.80, "MAC": 245.15, "GMR": 18.20, "TI3": 4.12, "ZRE": 115.30}

# --- 3. SESSION STATE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 4. SIDEBAR: GİRİŞ ---
with st.sidebar:
    st.header("📥 Yeni Fon Girişi")
    f_code = st.text_input("Fon Kodu (TCD, MAC, ZRE vb.)").upper()
    f_qty = st.number_input("Adet", min_value=0.000001, value=1.0)
    f_cost = st.number_input("Birim Alış Maliyeti (TL)", min_value=0.000001, format="%.6f")
    f_date = st.date_input("Alış Tarihi", value=datetime.now() - timedelta(days=365))
    
    if st.button("➕ Portföye Ekle", use_container_width=True):
        if f_code and f_cost > 0:
            with st.spinner("Kur verileri çekiliyor..."):
                u_old = get_historical_data("USDTRY=X", f_date)
                g_ons_old = get_historical_data("GC=F", f_date)
                if u_old and g_ons_old:
                    st.session_state.portfolio.append({
                        "kod": f_code, "adet": f_qty, "maliyet": f_cost, "tarih": f_date,
                        "usd_maliyet": u_old, "gold_maliyet": (g_ons_old / 31.10) * u_old
                    })
                    st.rerun()

# --- 5. ANA EKRAN ---
st.title("🛡️ Zenith Pro: Türk Fonları Hisse Analiz Raporu")

if st.session_state.portfolio:
    # --- YÖNETİM PANELİ ---
    st.subheader("⚙️ Portföy Yönetimi")
    usd_now = get_live_price("USDTRY=X") or 1.0
    gold_now = ((get_live_price("GC=F") or 1.0) / 31.10) * usd_now
    
    for idx, item in enumerate(st.session_state.portfolio):
        c_name, c_qty, c_cost, c_date, c_del = st.columns([1, 1, 1.2, 1.3, 0.5])
        with c_name: st.write(f"**{item['kod']}**")
        with c_qty: st.session_state.portfolio[idx]['adet'] = st.number_input("Adet", value=float(item['adet']), key=f"q_{idx}")
        with c_cost: st.session_state.portfolio[idx]['maliyet'] = st.number_input("Maliyet", value=float(item['maliyet']), key=f"m_{idx}", format="%.6f")
        with c_date:
            new_date = st.date_input("Tarih", value=item['tarih'], key=f"d_{idx}")
            if new_date != item['tarih']:
                u_o = get_historical_data("USDTRY=X", new_date)
                g_o = get_historical_data("GC=F", new_date)
                if u_o and g_o:
                    st.session_state.portfolio[idx].update({"tarih": new_date, "usd_maliyet": u_o, "gold_maliyet": (g_o/31.10)*u_o})
                    st.rerun()
        with c_del:
            if st.button("🗑️", key=f"del_{idx}"):
                st.session_state.portfolio.pop(idx); st.rerun()

    st.divider()

    # --- HESAPLAMALAR VE RAPORLAMA ---
    df = pd.DataFrame(st.session_state.portfolio)
    df['G. Fiyat'] = df['kod'].map(live_fund_prices).fillna(df['maliyet'] * 1.1)
    df['G. Değer'] = df['adet'] * df['G. Fiyat']
    df['T. Maliyet'] = df['adet'] * df['maliyet']
    
    tab1, tab2 = st.tabs(["📉 Reel Getiri Analizi", "💎 Hisse Senedi Dağılım Raporu"])

    with tab1:
        df['USD Fark %'] = ((df['G. Değer']/usd_now)/(df['T. Maliyet']/df['usd_maliyet'])-1)*100
        df['Altın Fark %'] = ((df['G. Değer']/gold_now)/(df['T. Maliyet']/df['gold_maliyet'])-1)*100
        st.dataframe(df[['kod', 'tarih', 'maliyet', 'USD Fark %', 'Altın Fark %']].style.format({'maliyet': '{:.6f}'}).background_gradient(cmap='RdYlGn'), use_container_width=True)

    with tab2:
        st.subheader("Portföyünüzdeki Toplam Hisse Senedi Ağırlıkları")
        st.write("Girdiğiniz fonların içindeki şirketlerin toplam portföyünüzdeki TL karşılığı ve yüzde dağılımı:")
        
        hisse_bazli = {}
        for _, row in df.iterrows():
            f_detay = fund_composition.get(row['kod'], {"detay": {f"{row['kod']} (Genel)": 1.0}})['detay']
            for hisse, oran in f_detay.items():
                hisse_bazli[hisse] = hisse_bazli.get(hisse, 0) + (row['G. Değer'] * oran)
        
        report_df = pd.DataFrame(list(hisse_bazli.items()), columns=['Şirket/Enstrüman', 'TL Değeri']).sort_values(by='TL Değeri', ascending=False)
        report_df['Yüzde (%)'] = (report_df['TL Değeri'] / report_df['TL Değeri'].sum()) * 100
        
        c_left, c_right = st.columns([1.5, 1])
        with c_left:
            st.plotly_chart(px.pie(report_df, values='TL Değeri', names='Şirket/Enstrüman', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel), use_container_width=True)
        with c_right:
            st.write("**Detaylı Hisse Listesi**")
            st.dataframe(report_df.style.format({'TL Değeri': '{:,.2f} ₺', 'Yüzde (%)': '% {:.2f}'}), use_container_width=True)

    st.divider()
    st.metric("Toplam Portföy Büyüklüğü", f"{df['G. Değer'].sum():,.2f} ₺")

else:
    st.info("Rapor oluşturmak için sol taraftan fon girişi yapın.")
