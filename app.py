import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: Canlı Veri Analizi", layout="wide")

# --- 1. FON & VARLIK VERİTABANI ---
# Burası fonların güncel piyasa fiyatlarını etkileyen ana varlıkları simüle eder
KAP_DATA = {
    "TCD": {"TUPRS": 0.14, "KCHOL": 0.12, "ASELS": 0.11, "ALTIN": 0.15, "DİĞER": 0.48},
    "AFT": {"NVIDIA": 0.20, "APPLE": 0.16, "MICROSOFT": 0.14, "ALPHABET": 0.12, "META": 0.10, "NAKİT": 0.28},
    "MAC": {"THYAO": 0.16, "MGROS": 0.13, "EREGL": 0.11, "SAHOL": 0.10, "KCHOL": 0.08, "DİĞER": 0.32},
}

# --- 2. GELİŞMİŞ VERİ ÇEKME FONKSİYONLARI ---
@st.cache_data(ttl=600)  # 10 dakikada bir veriyi yeniler
def get_live_price(ticker):
    """
    Hisse senetleri ve döviz için canlı fiyat çeker.
    Fonlar için yfinance üzerinde 'XXX.IS' formatını dener.
    """
    try:
        # Fonlar genellikle yfinance üzerinde doğrudan bulunmaz, 
        # ancak fonun içindeki ana varlıkların (BIST100 vb) hareketini çekebiliriz.
        data = yf.download(ticker, period="1d", progress=False)
        return float(data['Close'].iloc[-1]) if not data.empty else None
    except:
        return None

# --- 3. SESSION STATE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 4. SIDEBAR: CANLI PİYASA PANELİ ---
with st.sidebar:
    st.header("⚡ Canlı Piyasa Verileri")
    u_now = get_live_price("USDTRY=X")
    g_now = (get_live_price("GC=F") / 31.10) * (u_now if u_now else 1)
    bist_now = get_live_price("XU100.IS")
    
    col_u, col_g = st.columns(2)
    if u_now: col_u.metric("Dolar/TL", f"{u_now:.2f}")
    if g_now: col_g.metric("Gram Altın", f"{g_now:.0f} ₺")
    if bist_now: st.metric("BIST 100", f"{bist_now:,.0f}", delta=f"Günlük")

    st.divider()
    st.header("➕ İşlem Girişi")
    f_code = st.text_input("Fon Kodu (Örn: TCD)").upper().strip()
    f_qty = st.number_input("Adet", min_value=0.0, format="%.6f")
    f_cost = st.number_input("Maliyet (TL)", min_value=0.0, format="%.6f")
    f_live = st.number_input("Güncel Birim Fiyat (TL)", min_value=0.0, value=f_cost, format="%.6f")
    
    if st.button("Portföye Ekle", use_container_width=True):
        if f_code and f_qty > 0:
            st.session_state.portfolio.append({
                "kod": f_code, "adet": f_qty, "maliyet": f_cost, 
                "guncel_fiyat": f_live, "u_maliyet": u_now, "g_maliyet": g_now
            })
            st.rerun()

# --- 5. ANA EKRAN ---
st.title("🛡️ Zenith Pro: API Destekli Portföy")

if st.session_state.portfolio:
    st.subheader("⚙️ Portföy Yönetimi")
    
    # Yönetim Tablosu (Manuel Güncelleme ve Takip)
    for idx, item in enumerate(st.session_state.portfolio):
        c = st.columns([0.8, 1, 1, 1, 0.4])
        with c[0]: st.write(f"**{item['kod']}**")
        with c[1]: st.session_state.portfolio[idx]['adet'] = c[1].number_input("Adet", value=float(item['adet']), key=f"q_{idx}", label_visibility="collapsed")
        with c[2]: st.session_state.portfolio[idx]['maliyet'] = c[2].number_input("Maliyet", value=float(item['maliyet']), key=f"m_{idx}", label_visibility="collapsed")
        with c[3]: st.session_state.portfolio[idx]['guncel_fiyat'] = c[3].number_input("Güncel", value=float(item['guncel_fiyat']), key=f"g_{idx}", label_visibility="collapsed")
        with c[4]: 
            if c[4].button("🗑️", key=f"del_{idx}"):
                st.session_state.portfolio.pop(idx); st.rerun()

    st.divider()
    
    # --- ANALİZ BÖLÜMÜ ---
    df = pd.DataFrame(st.session_state.portfolio)
    df['G_Deger'] = df['adet'] * df['guncel_fiyat']
    df['T_Maliyet'] = df['adet'] * df['maliyet']
    
    t1, t2 = st.tabs(["📈 Kar/Zarar", "🔍 Varlık Dağılımı"])
    
    with t1:
        # Performans Hesaplama
        df['Getiri %'] = ((df['guncel_fiyat'] / df['maliyet']) - 1) * 100
        # Dolar Bazlı Getiri
        df['USD Bazlı %'] = ((df['G_Deger'] / u_now) / (df['T_Maliyet'] / df['u_maliyet']) - 1) * 100
        
        st.dataframe(df[['kod', 'maliyet', 'guncel_fiyat', 'Getiri %', 'USD Bazlı %']].style.format({
            'maliyet': '{:.4f}', 'guncel_fiyat': '{:.4f}', 
            'Getiri %': '% {:.2f}', 'USD Bazlı %': '% {:.2f}'
        }).background_gradient(cmap='RdYlGn'), use_container_width=True)

    with t2:
        # KAP Verisi ile Detaylı Dağılım
        all_assets = []
        for _, row in df.iterrows():
            comp = KAP_DATA.get(row['kod'], {row['kod']: 1.0})
            for asset, ratio in comp.items():
                all_assets.append({"Varlık": asset, "Değer": row['G_Deger'] * ratio})
        
        asset_df = pd.DataFrame(all_assets).groupby("Varlık").sum().reset_index()
        
        
        
        cp, cl = st.columns([1.5, 1])
        with cp: st.plotly_chart(px.pie(asset_df, values='Değer', names='Varlık', hole=0.4), use_container_width=True)
        with cl: st.dataframe(asset_df.sort_values(by="Değer", ascending=False).style.format({'Değer': '{:,.2f} ₺'}), use_container_width=True)

    # ÖZET METRİKLER
    st.divider()
    m1, m2, m3 = st.columns(3)
    total_val = df['G_Deger'].sum()
    total_cost = df['T_Maliyet'].sum()
    m1.metric("Toplam Portföy", f"{total_val:,.2f} ₺")
    m2.metric("Toplam Maliyet", f"{total_cost:,.2f} ₺")
    m3.metric("Net Kar/Zarar", f"% {((total_val/total_cost)-1)*100:.2f}", delta=f"{total_val-total_cost:,.2f} ₺")

else:
    st.info("Portföyünüz boş. Lütfen sol taraftan fon ekleyiniz.")
