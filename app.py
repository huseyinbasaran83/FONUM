import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: Sınırsız Fon Analizi", layout="wide")

# --- 1. KAP VERİTABANI (Sık Kullanılan Türk Fonları) ---
# Buraya eklenmeyen fonlar "Genel Portföy" olarak görünür.
KAP_DATA = {
    "TCD": {"TUPRS": 0.14, "KCHOL": 0.12, "ASELS": 0.11, "THYAO": 0.09, "ALTIN": 0.15, "DİĞER": 0.39},
    "MAC": {"THYAO": 0.16, "MGROS": 0.13, "EREGL": 0.11, "SAHOL": 0.10, "KCHOL": 0.08, "DİĞER": 0.32},
    "TI3": {"FROTO": 0.14, "SISE": 0.12, "TOASO": 0.11, "KCHOL": 0.10, "TUPRS": 0.07, "DİĞER": 0.46},
    "AFT": {"NVIDIA": 0.20, "APPLE": 0.16, "MICROSOFT": 0.14, "ALPHABET": 0.12, "META": 0.10, "NAKİT": 0.28},
    "ZRE": {"THYAO": 0.12, "TUPRS": 0.11, "AKBNK": 0.10, "ISCTR": 0.10, "KCHOL": 0.09, "DİĞER": 0.48},
    "NNF": {"THYAO": 0.12, "PGSUS": 0.10, "TUPRS": 0.09, "KCHOL": 0.08, "BIMAS": 0.08, "DİĞER": 0.53},
    "GMR": {"PGSUS": 0.13, "TAVHL": 0.11, "MGROS": 0.10, "YKBNK": 0.09, "BIMAS": 0.08, "DİĞER": 0.49},
}

# --- 2. YARDIMCI FONKSİYONLAR ---
@st.cache_data(ttl=3600)
def get_hist_kur(ticker, date_obj):
    try:
        data = yf.download(ticker, start=date_obj.strftime('%Y-%m-%d'), end=(date_obj + timedelta(days=7)).strftime('%Y-%m-%d'), progress=False)
        return float(data['Close'].iloc[0]) if not data.empty else None
    except: return None

@st.cache_data(ttl=600)
def get_current_price(ticker):
    try:
        data = yf.download(ticker, period="5d", progress=False)
        return float(data['Close'].iloc[-1]) if not data.empty else 1.0
    except: return 1.0

# --- 3. SESSION STATE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 4. SIDEBAR: AKILLI GİRİŞ ---
with st.sidebar:
    st.header("📊 Fon Girişi")
    # Kullanıcıya hem dropdown sunuyoruz hem de yeni fon yazma imkanı
    populer_fonlar = ["AFT", "TCD", "MAC", "TI3", "ZRE", "GMR", "NNF", "IDH", "HKH", "EID"]
    f_code = st.selectbox("Popüler Fonlar", ["Yeni Yaz..."] + populer_fonlar)
    
    if f_code == "Yeni Yaz...":
        f_code = st.text_input("Fon Kodunu Yazın (Örn: GUB, YAS, IPB)").upper().strip()
    
    f_qty = st.number_input("Adet", min_value=0.000001, value=1.0)
    f_cost = st.number_input("Birim Maliyet (TL)", min_value=0.000001, format="%.6f")
    f_date = st.date_input("Alış Tarihi", value=datetime.now() - timedelta(days=365))
    
    if st.button("➕ Portföye Ekle", use_container_width=True):
        if f_code:
            with st.spinner("Kurlar çekiliyor..."):
                u_old = get_hist_kur("USDTRY=X", f_date)
                g_old = get_hist_kur("GC=F", f_date)
                if u_old and g_old:
                    st.session_state.portfolio.append({
                        "kod": f_code, "adet": f_qty, "maliyet": f_cost, "tarih": f_date,
                        "u_maliyet": u_old, "g_maliyet": (g_old / 31.10) * u_old
                    })
                    st.rerun()

# --- 5. ANA EKRAN ---
st.title("🛡️ Zenith Pro: Sınırsız TEFAS Analiz")

if st.session_state.portfolio:
    st.subheader("⚙️ Portföy Yönetimi")
    u_now = get_current_price("USDTRY=X")
    g_now = (get_current_price("GC=F") / 31.10) * u_now
    
    # Yönetim Tablosu
    for idx, item in enumerate(st.session_state.portfolio):
        c1, c2, c3, c4, c5 = st.columns([1, 1, 1.2, 1.3, 0.5])
        with c1: st.write(f"**{item['kod']}**")
        with c2: st.session_state.portfolio[idx]['adet'] = st.number_input("Adet", value=float(item['adet']), key=f"q_{idx}")
        with c3: st.session_state.portfolio[idx]['maliyet'] = st.number_input("Maliyet", value=float(item['maliyet']), key=f"m_{idx}", format="%.6f")
        with c4: 
            new_date = st.date_input("Tarih", value=item['tarih'], key=f"d_{idx}")
            if new_date != item['tarih']:
                u_o = get_hist_kur("USDTRY=X", new_date)
                g_o = get_hist_kur("GC=F", new_date)
                if u_o and g_o:
                    st.session_state.portfolio[idx].update({"tarih": new_date, "u_maliyet": u_o, "g_maliyet": (g_o/31.10)*u_o})
                    st.rerun()
        with c5:
            if st.button("🗑️", key=f"del_{idx}"):
                st.session_state.portfolio.pop(idx); st.rerun()

    st.divider()

    # HESAPLAMALAR
    df = pd.DataFrame(st.session_state.portfolio)
    df['G_Deger'] = df['adet'] * (df['maliyet'] * 1.15) # Örnek güncel değer
    df['T_Maliyet'] = df['adet'] * df['maliyet']
    
    t1, t2 = st.tabs(["📈 Reel Getiri", "💎 Varlık Dağılım Raporu"])

    with t1:
        df['USD Fark %'] = ((df['G_Deger']/u_now)/(df['T_Maliyet']/df['u_maliyet'])-1)*100
        df['Altın Fark %'] = ((df['G_Deger']/g_now)/(df['T_Maliyet']/df['g_maliyet'])-1)*100
        st.dataframe(df[['kod', 'tarih', 'maliyet', 'USD Fark %', 'Altın Fark %']].style.format({'maliyet': '{:.6f}'}).background_gradient(cmap='RdYlGn'), use_container_width=True)

    with t2:
        st.subheader("Hisse Bazlı Detaylı Dağılım")
        all_hisseler = []
        for _, row in df.iterrows():
            # KAP_DATA'da varsa içindekileri, yoksa fonun kendisini ekle
            comp = KAP_DATA.get(row['kod'], {f"{row['kod']} (Hisse/Diger)": 1.0})
            for h_adi, oran in comp.items():
                all_hisseler.append({"Varlık": h_adi, "Değer": row['G_Deger'] * oran})
        
        report_df = pd.DataFrame(all_hisseler).groupby("Varlık").sum().reset_index().sort_values(by="Değer", ascending=False)
        report_df["Yüzde (%)"] = (report_df["Değer"] / report_df["Değer"].sum()) * 100

        c_p, c_l = st.columns([1.5, 1])
        with c_p:
            st.plotly_chart(px.pie(report_df, values='Değer', names='Varlık', hole=0.4), use_container_width=True)
        with c_l:
            st.dataframe(report_df.style.format({'Değer': '{:,.2f} ₺', 'Yüzde (%)': '% {:.2f}'}), use_container_width=True)

    st.divider()
    st.metric("Toplam Portföy", f"{df['G_Deger'].sum():,.2f} ₺")
else:
    st.info("Lütfen bir fon seçin veya kodunu yazarak ekleyin.")
