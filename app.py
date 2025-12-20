import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: TEFAS Akıllı Eşleşme", layout="wide")

# --- 1. KAP VERİTABANI ---
KAP_DATA = {
    "TCD": {"TUPRS": 0.14, "KCHOL": 0.12, "ASELS": 0.11, "THYAO": 0.09, "ALTIN": 0.15, "DİĞER": 0.39},
    "MAC": {"THYAO": 0.16, "MGROS": 0.13, "EREGL": 0.11, "SAHOL": 0.10, "KCHOL": 0.08, "DİĞER": 0.32},
    "TI3": {"FROTO": 0.14, "SISE": 0.12, "TOASO": 0.11, "KCHOL": 0.10, "TUPRS": 0.07, "DİĞER": 0.46},
    "AFT": {"NVIDIA": 0.20, "APPLE": 0.16, "MICROSOFT": 0.14, "ALPHABET": 0.12, "META": 0.10, "NAKİT": 0.28},
    "ZRE": {"THYAO": 0.12, "TUPRS": 0.11, "AKBNK": 0.10, "ISCTR": 0.10, "KCHOL": 0.09, "DİĞER": 0.48},
    "NNF": {"THYAO": 0.12, "PGSUS": 0.10, "TUPRS": 0.09, "KCHOL": 0.08, "BIMAS": 0.08, "DİĞER": 0.53},
    "GMR": {"PGSUS": 0.13, "TAVHL": 0.11, "MGROS": 0.10, "YKBNK": 0.09, "BIMAS": 0.08, "DİĞER": 0.49}
}

# --- 2. VERİ MOTORU ---
@st.cache_data(ttl=3600)
def get_hist_kur(ticker, date_obj):
    try:
        data = yf.download(ticker, start=date_obj.strftime('%Y-%m-%d'), end=(date_obj + timedelta(days=7)).strftime('%Y-%m-%d'), progress=False)
        return float(data['Close'].iloc[0]) if not data.empty else 1.0
    except: return 1.0

@st.cache_data(ttl=600)
def get_current_kur(ticker):
    try:
        data = yf.download(ticker, period="1d", progress=False)
        return float(data['Close'].iloc[-1]) if not data.empty else 1.0
    except: return 1.0

# --- 3. SESSION STATE ---
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'tefas_db' not in st.session_state: st.session_state.tefas_db = {}

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("📂 TEFAS Veri Merkezi")
    uploaded_file = st.file_uploader("TEFAS Excel/CSV Yükle", type=['xlsx', 'csv'])
    
    if uploaded_file:
        try:
            df_tefas = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            
            # Sütun isimlerini temizle
            df_tefas.columns = [str(c).strip().upper() for c in df_tefas.columns]
            
            # Akıllı Sütun Bulucu
            kod_col = next((c for c in df_tefas.columns if "KOD" in c), df_tefas.columns[0])
            fiyat_keywords = ["FİYAT", "SON", "DEĞER", "PRICE", "BİRİM"]
            fiyat_col = next((c for c in df_tefas.columns if any(k in c for k in fiyat_keywords)), None)
            
            if fiyat_col:
                for _, row in df_tefas.iterrows():
                    try:
                        f_kod = str(row[kod_col]).strip().upper()
                        f_fiyat = float(row[fiyat_col])
                        st.session_state.tefas_db[f_kod] = f_fiyat
                    except: continue
                st.success(f"✅ {len(st.session_state.tefas_db)} fon güncellendi.")
            else:
                st.error("Fiyat sütunu bulunamadı!")
        except Exception as e:
            st.error(f"Hata: {e}")

    st.divider()
    st.header("➕ Fon Ekle")
    f_code = st.text_input("Fon Kodu").upper().strip()
    f_qty = st.number_input("Adet", min_value=0.0, format="%.6f")
    f_cost = st.number_input("Maliyet (TL)", min_value=0.0, format="%.6f")
    f_date = st.date_input("Alış Tarihi", value=datetime.now() - timedelta(days=30))
    
    if st.button("Kaydet", use_container_width=True):
        if f_code and f_qty > 0:
            u_old = get_hist_kur("USDTRY=X", f_date)
            g_old = get_hist_kur("GC=F", f_date)
            live = st.session_state.tefas_db.get(f_code, f_cost)
            st.session_state.portfolio.append({
                "kod": f_code, "adet": f_qty, "maliyet": f_cost, 
                "guncel_fiyat": live, "tarih": f_date, 
                "u_maliyet": u_old, "g_maliyet": (g_old/31.10)*u_old
            })
            st.rerun()

# --- 5. ANA EKRAN ---
st.title("🛡️ Zenith Pro: Otomatik Senkron")

if st.session_state.portfolio:
    if st.session_state.tefas_db and st.button("🔄 Excel Fiyatlarını Portföye Uygula", use_container_width=True):
        for i, item in enumerate(st.session_state.portfolio):
            if item['kod'] in st.session_state.tefas_db:
                st.session_state.portfolio[i]['guncel_fiyat'] = st.session_state.tefas_db[item['kod']]
        st.toast("Portföy güncellendi!")

    u_now = get_current_kur("USDTRY=X")
    g_now = (get_current_kur("GC=F") / 31.10) * u_now

    # Yönetim Tablosu
    h = st.columns([0.8, 1, 1.2, 1.2, 1.2, 0.4])
    cols = ["Fon", "Adet", "Maliyet", "Güncel", "Tarih", "Sil"]
    for i, head in enumerate(cols): h[i].write(f"**{head}**")

    for idx, item in enumerate(st.session_state.portfolio):
        c = st.columns([0.8, 1, 1.2, 1.2, 1.2, 0.4])
        with c[0]: st.write(item['kod'])
        with c[1]: st.session_state.portfolio[idx]['adet'] = c[1].number_input("", value=float(item['adet']), key=f"q_{idx}", format="%.6f", label_visibility="collapsed")
        with c[2]: st.session_state.portfolio[idx]['maliyet'] = c[2].number_input("", value=float(item['maliyet']), key=f"m_{idx}", format="%.6f", label_visibility="collapsed")
        with c[3]: st.session_state.portfolio[idx]['guncel_fiyat'] = c[3].number_input("", value=float(item.get('guncel_fiyat', item['maliyet'])), key=f"g_{idx}", format="%.6f", label_visibility="collapsed")
        with c[4]: st.session_state.portfolio[idx]['tarih'] = c[4].date_input("", value=item['tarih'], key=f"d_{idx}", label_visibility="collapsed")
        with c[5]: 
            if c[5].button("🗑️", key=f"del_{idx}"):
                st.session_state.portfolio.pop(idx); st.rerun()

    st.divider()
    df_res = pd.DataFrame(st.session_state.portfolio)
    df_res['G_Deger'] = df_res['adet'] * df_res['guncel_fiyat']
    df_res['T_Maliyet'] = df_res['adet'] * df_res['maliyet']
    
    t1, t2 = st.tabs(["📊 Analiz", "🔍 KAP Röntgeni"])
    
    with t1:
        df_res['USD %'] = ((df_res['G_Deger']/u_now)/(df_res['T_Maliyet']/df_res['u_maliyet'])-1)*100
        df_res['ALTIN %'] = ((df_res['G_Deger']/g_now)/(df_res['T_Maliyet']/df_res['g_maliyet'])-1)*100
        st.dataframe(df_res[['kod', 'tarih', 'maliyet', 'guncel_fiyat', 'USD %', 'ALTIN %']].style.format({
            'maliyet': '{:.6f}', 'guncel_fiyat': '{:.6f}', 'USD %': '% {:.2f}', 'ALTIN %': '% {:.2f}'
        }).background_gradient(cmap='RdYlGn'), use_container_width=True)

    with t2:
        all_assets = []
        for _, row in df_res.iterrows():
            comp = KAP_DATA.get(row['kod'], {row['kod']: 1.0})
            for asset, ratio in comp.items():
                all_assets.append({"Varlık": asset, "Değer": row['G_Deger'] * ratio})
        
        asset_df = pd.DataFrame(all_assets).groupby("Varlık").sum().reset_index().sort_values(by="Değer", ascending=False)
        
        c_pie, c_list = st.columns([1.5, 1])
        with c_pie: st.plotly_chart(px.pie(asset_df, values='Değer', names='Varlık', hole=0.4), use_container_width=True)
        with c_list: st.dataframe(asset_df.style.format({'Değer': '{:,.2f} ₺'}), use_container_width=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Değer", f"{df_res['G_Deger'].sum():,.2f} ₺")
    m2.metric("Net Kar/Zarar", f"% {((df_res['G_Deger'].sum()/df_res['T_Maliyet'].sum())-1)*100:.2f}")
    m3.metric("Maliyet", f"{df_res['T_Maliyet'].sum():,.2f} ₺")
else:
    st.info("👋 Başlamak için Excel yükleyin veya manuel fon ekleyin.")
