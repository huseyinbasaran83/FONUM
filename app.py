import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: Esnek TEFAS Senkron", layout="wide")

# --- 1. KAP VERİTABANI ---
KAP_DATA = {
    "TCD": {"TUPRS": 0.14, "KCHOL": 0.12, "ASELS": 0.11, "THYAO": 0.09, "ALTIN": 0.15, "DİĞER": 0.39},
    "MAC": {"THYAO": 0.16, "MGROS": 0.13, "EREGL": 0.11, "SAHOL": 0.10, "KCHOL": 0.08, "DİĞER": 0.32},
    "AFT": {"NVIDIA": 0.20, "APPLE": 0.16, "MICROSOFT": 0.14, "ALPHABET": 0.12, "META": 0.10, "NAKİT": 0.28},
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
    uploaded_file = st.file_uploader("Excel/CSV Yükle", type=['xlsx', 'csv'])
    
    if uploaded_file:
        df_tefas = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        st.write("---")
        st.info("Sütunları Eşleştirin:")
        
        # Kullanıcıya hangi sütunun ne olduğunu seçtiriyoruz
        all_cols = list(df_tefas.columns)
        col_code = st.selectbox("Fon Kodu Sütunu", all_cols, index=0)
        col_price = st.selectbox("Fiyat Sütunu", all_cols, index=min(1, len(all_cols)-1))
        
        if st.button("Verileri Belleğe Al"):
            try:
                temp_db = {}
                for _, row in df_tefas.iterrows():
                    k = str(row[col_code]).strip().upper()
                    try:
                        p = float(str(row[col_price]).replace(',', '.'))
                        temp_db[k] = p
                    except: continue
                st.session_state.tefas_db = temp_db
                st.success(f"✅ {len(temp_db)} fon kaydedildi!")
            except Exception as e:
                st.error(f"Eşleştirme hatası: {e}")

    st.divider()
    st.header("➕ Manuel Giriş")
    f_code = st.text_input("Fon Kodu").upper().strip()
    f_qty = st.number_input("Adet", min_value=0.0, format="%.6f")
    f_cost = st.number_input("Maliyet (TL)", min_value=0.0, format="%.6f")
    f_date = st.date_input("Alış Tarihi", value=datetime.now() - timedelta(days=30))
    
    if st.button("Portföye Ekle"):
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
st.title("🛡️ Zenith Pro: Kesintisiz Veri Akışı")

if st.session_state.portfolio:
    if st.session_state.tefas_db:
        if st.button("🔄 Portföyü Yüklenen Fiyatlarla Güncelle", use_container_width=True):
            for i, item in enumerate(st.session_state.portfolio):
                if item['kod'] in st.session_state.tefas_db:
                    st.session_state.portfolio[i]['guncel_fiyat'] = st.session_state.tefas_db[item['kod']]
            st.toast("Fiyatlar güncellendi!")

    u_now = get_current_kur("USDTRY=X")
    g_now = (get_current_kur("GC=F") / 31.10) * u_now

    # Tablo Gösterimi
    df_res = pd.DataFrame(st.session_state.portfolio)
    df_res['G_Deger'] = df_res['adet'] * df_res['guncel_fiyat']
    df_res['T_Maliyet'] = df_res['adet'] * df_res['maliyet']

    # Düzenleme Alanı
    for idx, item in enumerate(st.session_state.portfolio):
        c = st.columns([0.8, 1, 1, 1, 1.2, 0.4])
        with c[0]: st.write(f"**{item['kod']}**")
        with c[1]: st.session_state.portfolio[idx]['adet'] = c[1].number_input("Adet", value=float(item['adet']), key=f"q_{idx}", label_visibility="collapsed")
        with c[2]: st.session_state.portfolio[idx]['maliyet'] = c[2].number_input("Maliyet", value=float(item['maliyet']), key=f"m_{idx}", label_visibility="collapsed")
        with c[3]: st.session_state.portfolio[idx]['guncel_fiyat'] = c[3].number_input("Güncel", value=float(item['guncel_fiyat']), key=f"g_{idx}", label_visibility="collapsed")
        with c[4]: st.write(item['tarih'].strftime('%d.%m.%Y'))
        with c[5]: 
            if c[5].button("🗑️", key=f"del_{idx}"):
                st.session_state.portfolio.pop(idx); st.rerun()

    st.divider()
    
    t1, t2 = st.tabs(["📈 Analiz", "🔍 Varlık Dağılımı"])
    with t1:
        df_res['Kar %'] = ((df_res['guncel_fiyat']/df_res['maliyet'])-1)*100
        df_res['USD Reel %'] = ((df_res['G_Deger']/u_now)/(df_res['T_Maliyet']/df_res['u_maliyet'])-1)*100
        st.dataframe(df_res[['kod', 'Kar %', 'USD Reel %', 'G_Deger']].style.format({'Kar %': '% {:.2f}', 'USD Reel %': '% {:.2f}', 'G_Deger': '{:,.2f} ₺'}).background_gradient(cmap='RdYlGn'), use_container_width=True)

    with t2:
        all_assets = []
        for _, row in df_res.iterrows():
            comp = KAP_DATA.get(row['kod'], {row['kod']: 1.0})
            for asset, ratio in comp.items():
                all_assets.append({"Varlık": asset, "Değer": row['G_Deger'] * ratio})
        asset_df = pd.DataFrame(all_assets).groupby("Varlık").sum().reset_index()
        
        
        
        c_pie, c_table = st.columns([1.5, 1])
        with c_pie: st.plotly_chart(px.pie(asset_df, values='Değer', names='Varlık', hole=0.4), use_container_width=True)
        with c_table: st.dataframe(asset_df.sort_values(by="Değer", ascending=False), use_container_width=True)

    st.metric("Toplam Portföy", f"{df_res['G_Deger'].sum():,.2f} ₺", delta=f"{df_res['G_Deger'].sum() - df_res['T_Maliyet'].sum():,.2f} ₺")
else:
    st.info("Sol taraftan Excel yükleyin ve sütunları seçin.")
