import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: TEFAS Senkron", layout="wide")

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
    except:
        return 1.0

@st.cache_data(ttl=600)
def get_current_kur(ticker):
    try:
        data = yf.download(ticker, period="1d", progress=False)
        return float(data['Close'].iloc[-1]) if not data.empty else 1.0
    except:
        return 1.0

# --- 3. SESSION STATE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []
if 'tefas_db' not in st.session_state:
    st.session_state.tefas_db = {}

# --- 4. SIDEBAR: DOSYA YÜKLEME VE GİRİŞ ---
with st.sidebar:
    st.header("📂 TEFAS Veri Merkezi")
    uploaded_file = st.file_uploader("Fiyat Listesi Yükle (Excel/CSV)", type=['xlsx', 'csv'])
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                tefas_df = pd.read_csv(uploaded_file)
            else:
                tefas_df = pd.read_excel(uploaded_file)
            
            tefas_df.columns = [str(c).strip().upper() for c in tefas_df.columns]
            for _, row in tefas_df.iterrows():
                kod = str(row.iloc[0]).strip().upper()
                fiyat = float(row.iloc[1])
                st.session_state.tefas_db[kod] = fiyat
            st.success(f"✅ {len(tefas_df)} fon fiyatı tanımlandı.")
        except Exception as e:
            st.error(f"⚠️ Dosya hatası: {e}")

    st.divider()
    st.header("➕ Fon Ekle")
    f_code = st.text_input("Fon Kodu").upper().strip()
    f_qty = st.number_input("Adet", min_value=0.0, format="%.6f")
    f_cost = st.number_input("Birim Maliyet (TL)", min_value=0.0, format="%.6f")
    f_date = st.date_input("Alış Tarihi", value=datetime.now() - timedelta(days=30))
    
    if st.button("Portföye Kaydet", use_container_width=True):
        if f_code and f_qty > 0:
            u_old = get_hist_kur("USDTRY=X", f_date)
            g_old = get_hist_kur("GC=F", f_date)
            live_val = st.session_state.tefas_db.get(f_code, f_cost)
            st.session_state.portfolio.append({
                "kod": f_code, "adet": f_qty, "maliyet": f_cost, 
                "guncel_fiyat": live_val, "tarih": f_date, 
                "u_maliyet": u_old, "g_maliyet": (g_old/31.10)*u_old
            })
            st.rerun()

# --- 5. ANA EKRAN ---
st.title("🛡️ Zenith Pro: Akıllı Portföy Yönetimi")

if st.session_state.portfolio:
    if st.session_state.tefas_db:
        if st.button("🔄 Tüm Portföyü Güncel Excel Verileriyle Senkronize Et", use_container_width=True):
            for i, item in enumerate(st.session_state.portfolio):
                if item['kod'] in st.session_state.tefas_db:
                    st.session_state.portfolio[i]['guncel_fiyat'] = st.session_state.tefas_db[item['kod']]
            st.toast("Fiyatlar güncellendi!")

    st.subheader("⚙️ Portföy Yönetimi")
    u_now = get_current_kur("USDTRY=X")
    g_now = (get_current_kur("GC=F") / 31.10) * u_now

    # Tablo Başlıkları
    h_cols = st.columns([0.8, 1, 1.2, 1.2, 1.2, 0.4])
    h_labels = ["Fon", "Adet", "Maliyet", "Güncel Fiyat", "Tarih", "Sil"]
    for col, label in zip(h_cols, h_labels):
        col.write(f"**{label}**")

    # Satır Verileri
    for idx, item in enumerate(st.session_state.portfolio):
        c1, c2, c3, c4, c5, c6 = st.columns([0.8, 1, 1.2, 1.2, 1.2, 0.4])
        with c1: st.write(f"**{item['kod']}**")
        with c2: st.session_state.portfolio[idx]['adet'] = c2.number_input("", value=float(item['adet']), key=f"q_{idx}", format="%.6f", label_visibility="collapsed")
        with c3: st.session_state.portfolio[idx]['maliyet'] = c3.number_input("", value=float(item['maliyet']), key=f"m_{idx}", format="%.6f", label_visibility="collapsed")
        with c4: st.session_state.portfolio[idx]['guncel_fiyat'] = c4.number_input("", value=float(item.get('guncel_fiyat', item['maliyet'])), key=f"g_{idx}", format="%.6f", label_visibility="collapsed")
        with c5: st.session_state.portfolio[idx]['tarih'] = c5.date_input("", value=item['tarih'], key=f"d_{idx}", label_visibility="collapsed")
        with c6: 
            if c6.button("🗑️", key=f"del_{idx}"):
                st.session_state.portfolio.pop(idx)
                st.rerun()

    st.divider()
    df_calc = pd.DataFrame(st.session_state.portfolio)
    df_calc['G_Deger'] = df_calc['adet'] * df_calc['guncel_fiyat']
    df_calc['T_Maliyet'] = df_calc['adet'] * df_calc['maliyet']
    
    t1, t2 = st.tabs(["📊 Kar/Zarar Performansı", "🔍 Varlık Röntgeni (KAP)"])
    
    with t1:
        df_calc['USD Bazlı %'] = ((df_calc['G_Deger']/u_now)/(df_calc['T_Maliyet']/df_calc['u_maliyet'])-1)*100
        df_calc['Altın Bazlı %'] = ((df_calc['G_Deger']/g_now)/(df_calc['T_Maliyet']/df_calc['g_maliyet'])-1)*100
        df_calc['Kar/Zarar %'] = ((df_calc['guncel_fiyat']/df_calc['maliyet'])-1)*100
        
        st.dataframe(df_calc[['kod', 'tarih', 'maliyet', 'guncel_fiyat', 'Kar/Zarar %', 'USD Bazlı %', 'Altın Bazlı %']].style.format({
            'maliyet': '{:.6f}', 'guncel_fiyat': '{:.6f}', 'Kar/Zarar %': '% {:.2f}', 
            'USD Bazlı %': '% {:.2f}', 'Altın Bazlı %': '% {:.2f}'
        }).background_gradient(cmap='RdYlGn', subset=['Kar/Zarar %', 'USD Bazlı %', 'Altın Bazlı %']), use_container_width=True)

    with t2:
        all_assets = []
        for _, row in df_calc.iterrows():
            comp = KAP_DATA.get(row['kod'], {row['kod']: 1.0})
            for asset, ratio in comp.items():
                all_assets.append({"Varlık": asset, "Değer": row['G_Deger'] * ratio})
        
        asset_df = pd.DataFrame(all_assets).groupby("Varlık").sum().reset_index().sort_values(by="Değer", ascending=False)
        asset_df["Yüzde (%)"] = (asset_df["Değer"] / asset_df["Değer"].sum()) * 100
        
        
        
        cp, cl = st.columns([1.5, 1])
        with cp:
            st.plotly_chart(px.pie(asset_df, values='Değer', names='Varlık', hole=0.4), use_container_width=True)
        with cl:
            st.dataframe(asset_df.style.format({'Değer': '{:,.2f} ₺', 'Yüzde (%)': '% {:.2f}'}), use_container_width=True)

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Portföy", f"{df_calc['G_Deger'].sum():,.2f} ₺")
    m2.metric("Toplam Maliyet", f"{df_calc['T_Maliyet'].sum():,.2f} ₺")
    m3.metric("Net Getiri", f"% {((df_calc['G_Deger'].sum()/df_calc['T_Maliyet'].sum())-1)*100:.2f}")
else:
    st.info("👋 Hoş geldiniz! Başlamak için TEFAS Excel dosyasını yükleyin veya manuel fon girişi yapın.")
