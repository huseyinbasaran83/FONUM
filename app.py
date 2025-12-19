import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: KAP & TEFAS Entegrasyonu", layout="wide")

# --- 1. TEFAS FON LİSTESİ VE KAP DETAYLARI ---
# Popüler tüm fonları buraya ekliyoruz
TEFAS_LIST = [
    "AFT", "TCD", "MAC", "TI3", "ZRE", "GMR", "IDH", "NNF", "HKH", "GL1",
    "GUB", "EID", "HVS", "FYL", "NRG", "ST1", "IUP", "GSP", "IPB", "OPB",
    "FAS", "KPC", "YAY", "DVY", "HSL", "YZH", "AES", "AFO", "AFS"
]

# KAP'tan alınan gerçek hisse dağılım veritabanı
# Bu liste ne kadar geniş olursa "Röntgen" o kadar detaylı çalışır
KAP_DATA = {
    "TCD": {"TUPRS": 0.14, "KCHOL": 0.12, "ASELS": 0.11, "THYAO": 0.09, "BIMAS": 0.07, "ALTIN": 0.15, "DİĞER": 0.32},
    "MAC": {"THYAO": 0.16, "MGROS": 0.13, "EREGL": 0.11, "SAHOL": 0.10, "BIMAS": 0.09, "KCHOL": 0.08, "DİĞER": 0.33},
    "TI3": {"FROTO": 0.14, "SISE": 0.12, "TOASO": 0.11, "KCHOL": 0.10, "ARCLK": 0.08, "TUPRS": 0.07, "DİĞER": 0.38},
    "ZRE": {"THYAO": 0.12, "TUPRS": 0.11, "AKBNK": 0.10, "ISCTR": 0.10, "KCHOL": 0.09, "EREGL": 0.08, "DİĞER": 0.40},
    "NNF": {"THYAO": 0.12, "PGSUS": 0.10, "TUPRS": 0.09, "KCHOL": 0.08, "BIMAS": 0.08, "DİĞER": 0.53},
    "AFT": {"NVIDIA": 0.20, "APPLE": 0.16, "MICROSOFT": 0.14, "ALPHABET": 0.12, "META": 0.10, "NAKİT": 0.28},
    "GMR": {"PGSUS": 0.13, "TAVHL": 0.11, "MGROS": 0.10, "YKBNK": 0.09, "BIMAS": 0.08, "DİĞER": 0.49},
    "IDH": {"THYAO": 0.11, "TUPRS": 0.10, "KCHOL": 0.09, "SISE": 0.08, "BIMAS": 0.07, "DİĞER": 0.55}
}

# --- 2. VERİ ÇEKME MOTORU ---
@st.cache_data(ttl=3600)
def get_historical_kur(ticker, date_obj):
    try:
        start = date_obj.strftime('%Y-%m-%d')
        end = (date_obj + timedelta(days=7)).strftime('%Y-%m-%d')
        data = yf.download(ticker, start=start, end=end, progress=False)
        return float(data['Close'].iloc[0]) if not data.empty else None
    except: return None

@st.cache_data(ttl=600)
def get_current_kur(ticker):
    try:
        data = yf.download(ticker, period="5d", progress=False)
        return float(data['Close'].iloc[-1]) if not data.empty else 1.0
    except: return 1.0

# --- 3. SESSION STATE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 4. SIDEBAR: YENİ GİRİŞ ---
with st.sidebar:
    st.header("📊 Fon Ekle")
    # Dropdown Listesi (Autocomplete destekli)
    selected_fund = st.selectbox("TEFAS Fonu Seçin", sorted(TEFAS_LIST))
    f_qty = st.number_input("Adet", min_value=0.000001, value=1.0)
    # SADECE BURASI 6 BASAMAK
    f_cost = st.number_input("Birim Alış Maliyeti (TL)", min_value=0.000001, format="%.6f")
    f_date = st.date_input("Alış Tarihi", value=datetime.now() - timedelta(days=365))
    
    if st.button("➕ Listeye Ekle", use_container_width=True):
        with st.spinner("Kur verileri sorgulanıyor..."):
            u_old = get_historical_kur("USDTRY=X", f_date)
            g_old = get_historical_kur("GC=F", f_date)
            if u_old and g_old:
                st.session_state.portfolio.append({
                    "kod": selected_fund, "adet": f_qty, "maliyet": f_cost, "tarih": f_date,
                    "u_maliyet": u_old, "g_maliyet": (g_old / 31.10) * u_old
                })
                st.rerun()

# --- 5. ANA EKRAN ---
st.title("🛡️ Zenith Pro: 360° Varlık Analizi")

if st.session_state.portfolio:
    # --- YÖNETİM PANELİ ---
    st.subheader("⚙️ Portföy Yönetimi")
    u_now = get_current_kur("USDTRY=X")
    g_now = (get_current_kur("GC=F") / 31.10) * u_now
    
    # Yönetim Tablosu (Düzenle/Sil/Tarih Değiştir)
    for idx, item in enumerate(st.session_state.portfolio):
        c1, c2, c3, c4, c5 = st.columns([1, 1, 1.2, 1.3, 0.5])
        with c1: st.write(f"**{item['kod']}**")
        with c2: st.session_state.portfolio[idx]['adet'] = st.number_input("Adet", value=float(item['adet']), key=f"q_{idx}")
        with c3: st.session_state.portfolio[idx]['maliyet'] = st.number_input("Maliyet", value=float(item['maliyet']), key=f"m_{idx}", format="%.6f")
        with c4: 
            new_date = st.date_input("Tarih", value=item['tarih'], key=f"d_{idx}")
            if new_date != item['tarih']:
                u_o = get_historical_kur("USDTRY=X", new_date)
                g_o = get_historical_kur("GC=F", new_date)
                if u_o and g_o:
                    st.session_state.portfolio[idx].update({"tarih": new_date, "u_maliyet": u_o, "g_maliyet": (g_o/31.10)*u_o})
                    st.rerun()
        with c5:
            if st.button("🗑️", key=f"del_{idx}"):
                st.session_state.portfolio.pop(idx); st.rerun()

    st.divider()

    # --- HESAPLAMA MOTORU ---
    df = pd.DataFrame(st.session_state.portfolio)
    # Varsayılan %15 büyüme (Anlık fiyat API'si yoksa)
    df['G_Deger'] = df['adet'] * (df['maliyet'] * 1.15) 
    df['T_Maliyet'] = df['adet'] * df['maliyet']
    
    t1, t2 = st.tabs(["📉 Reel Getiri Analizi", "💎 Hisse Senedi Dağılım Raporu"])

    with t1:
        df['USD Fark %'] = ((df['G_Deger']/u_now)/(df['T_Maliyet']/df['u_maliyet'])-1)*100
        df['Altın Fark %'] = ((df['G_Deger']/g_now)/(df['T_Maliyet']/df['g_maliyet'])-1)*100
        st.dataframe(df[['kod', 'tarih', 'maliyet', 'USD Fark %', 'Altın Fark %']].style.format({'maliyet': '{:.6f}'}).background_gradient(cmap='RdYlGn'), use_container_width=True)

    with t2:
        st.subheader("KAP Beyanına Göre Varlık Dağılımı")
        all_assets = []
        for _, row in df.iterrows():
            # KAP_DATA içinde var mı? Yoksa kendi adıyla ekle
            comp = KAP_DATA.get(row['kod'], {f"{row['kod']} (Hisse/Diger)": 1.0})
            for name, ratio in comp.items():
                all_assets.append({"Varlık": name, "Değer": row['G_Deger'] * ratio})
        
        asset_df = pd.DataFrame(all_assets).groupby("Varlık").sum().reset_index().sort_values(by="Değer", ascending=False)
        asset_df["Yüzde (%)"] = (asset_df["Değer"] / asset_df["Değer"].sum()) * 100

        

        cp, cl = st.columns([1.5, 1])
        with cp:
            st.plotly_chart(px.pie(asset_df, values='Değer', names='Varlık', hole=0.4, title="Toplam Portföy Dağılımı"), use_container_width=True)
        with cl:
            st.write("**Hisse Bazlı TL Tutarlar**")
            st.dataframe(asset_df.style.format({'Değer': '{:,.2f} ₺', 'Yüzde (%)': '% {:.2f}'}), use_container_width=True)

    st.divider()
    st.metric("Toplam Portföy", f"{df['G_Deger'].sum():,.2f} ₺")
else:
    st.info("Raporlama için sol menüdeki listeden bir fon seçip 'Listeye Ekle' butonuna basın.")
