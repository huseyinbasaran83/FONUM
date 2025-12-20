import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: Canlı Portföy", layout="wide")

# --- 1. KAP VERİTABANI (Hisse Dağılımları) ---
KAP_DATA = {
    "TCD": {"TUPRS": 0.14, "KCHOL": 0.12, "ASELS": 0.11, "THYAO": 0.09, "ALTIN": 0.15, "DİĞER": 0.39},
    "MAC": {"THYAO": 0.16, "MGROS": 0.13, "EREGL": 0.11, "SAHOL": 0.10, "KCHOL": 0.08, "DİĞER": 0.32},
    "TI3": {"FROTO": 0.14, "SISE": 0.12, "TOASO": 0.11, "KCHOL": 0.10, "TUPRS": 0.07, "DİĞER": 0.46},
    "AFT": {"NVIDIA": 0.20, "APPLE": 0.16, "MICROSOFT": 0.14, "ALPHABET": 0.12, "META": 0.10, "NAKİT": 0.28},
    "ZRE": {"THYAO": 0.12, "TUPRS": 0.11, "AKBNK": 0.10, "ISCTR": 0.10, "KCHOL": 0.09, "DİĞER": 0.48},
    "NNF": {"THYAO": 0.12, "PGSUS": 0.10, "TUPRS": 0.09, "KCHOL": 0.08, "BIMAS": 0.08, "DİĞER": 0.53},
    "GMR": {"PGSUS": 0.13, "TAVHL": 0.11, "MGROS": 0.10, "YKBNK": 0.09, "BIMAS": 0.08, "DİĞER": 0.49},
}

# --- 2. VERİ MOTORU ---
@st.cache_data(ttl=3600)
def get_hist_kur(ticker, date_obj):
    try:
        data = yf.download(ticker, start=date_obj.strftime('%Y-%m-%d'), end=(date_obj + timedelta(days=7)).strftime('%Y-%m-%d'), progress=False)
        return float(data['Close'].iloc[0]) if not data.empty else None
    except: return None

@st.cache_data(ttl=600)
def get_current_price(ticker):
    try:
        data = yf.download(ticker, period="1d", progress=False)
        return float(data['Close'].iloc[-1]) if not data.empty else 1.0
    except: return 1.0

# --- 3. SESSION STATE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 4. SIDEBAR: GİRİŞ ---
with st.sidebar:
    st.header("📊 Fon Girişi")
    populer_fonlar = ["AFT", "TCD", "MAC", "TI3", "ZRE", "GMR", "NNF", "IDH", "HKH", "EID"]
    f_code = st.selectbox("Fon Seçin", ["Yeni Yaz..."] + populer_fonlar)
    
    if f_code == "Yeni Yaz...":
        f_code = st.text_input("Fon Kodu (GUB, YAS vb.)").upper().strip()
    
    f_qty = st.number_input("Adet", min_value=0.000001, value=1.0, format="%.6f")
    f_cost = st.number_input("Birim Maliyet (TL)", min_value=0.000001, format="%.6f")
    # Kullanıcıya güncel fiyatı manuel girme veya sistemden çekme imkanı veriyoruz
    f_live = st.number_input("Güncel Birim Fiyat (TL)", min_value=0.000000, value=f_cost * 1.1, format="%.6f")
    f_date = st.date_input("Alış Tarihi", value=datetime.now() - timedelta(days=365))
    
    if st.button("➕ Portföye Ekle", use_container_width=True):
        if f_code:
            with st.spinner("Kurlar alınıyor..."):
                u_old = get_hist_kur("USDTRY=X", f_date)
                g_old = get_hist_kur("GC=F", f_date)
                if u_old and g_old:
                    st.session_state.portfolio.append({
                        "kod": f_code, "adet": f_qty, "maliyet": f_cost, "guncel_fiyat": f_live,
                        "tarih": f_date, "u_maliyet": u_old, "g_maliyet": (g_old / 31.10) * u_old
                    })
                    st.rerun()

# --- 5. ANA EKRAN ---
st.title("🛡️ Zenith Pro: Canlı Portföy Takibi")

if st.session_state.portfolio:
    st.subheader("⚙️ Portföy Yönetim Tablosu")
    
    # Canlı USD ve Altın Kurları
    u_now = get_current_price("USDTRY=X")
    g_now = (get_current_price("GC=F") / 31.10) * u_now
    
    # Tablo Başlıkları
    h1, h2, h3, h4, h5, h6 = st.columns([0.8, 1, 1.2, 1.2, 1.3, 0.4])
    h1.write("**Fon**")
    h2.write("**Adet**")
    h3.write("**Maliyet (TL)**")
    h4.write("**Güncel Fiyat (TL)**")
    h5.write("**Alış Tarihi**")
    h6.write("**Sil**")

    # Satırları Oluşturma
    for idx, item in enumerate(st.session_state.portfolio):
        c1, c2, c3, c4, c5, c6 = st.columns([0.8, 1, 1.2, 1.2, 1.3, 0.4])
        
        with c1:
            st.write(f"**{item['kod']}**")
        with c2:
            st.session_state.portfolio[idx]['adet'] = st.number_input("", value=float(item['adet']), key=f"q_{idx}", format="%.6f", label_visibility="collapsed")
        with c3:
            st.session_state.portfolio[idx]['maliyet'] = st.number_input("", value=float(item['maliyet']), key=f"m_{idx}", format="%.6f", label_visibility="collapsed")
        with c4:
            # GÜNCEL FİYAT BURADA DÜZENLENEBİLİR
            st.session_state.portfolio[idx]['guncel_fiyat'] = st.number_input("", value=float(item['guncel_fiyat']), key=f"g_{idx}", format="%.6f", label_visibility="collapsed")
        with c5:
            new_date = st.date_input("", value=item['tarih'], key=f"d_{idx}", label_visibility="collapsed")
            if new_date != item['tarih']:
                u_o = get_hist_kur("USDTRY=X", new_date)
                g_o = get_hist_kur("GC=F", new_date)
                if u_o and g_o:
                    st.session_state.portfolio[idx].update({"tarih": new_date, "u_maliyet": u_o, "g_maliyet": (g_o/31.10)*u_o})
                    st.rerun()
        with c6:
            if st.button("🗑️", key=f"del_{idx}"):
                st.session_state.portfolio.pop(idx)
                st.rerun()

    st.divider()

    # --- HESAPLAMALAR ---
    df = pd.DataFrame(st.session_state.portfolio)
    df['G_Deger'] = df['adet'] * df['guncel_fiyat']
    df['T_Maliyet'] = df['adet'] * df['maliyet']
    
    t1, t2 = st.tabs(["📈 Kar/Zarar ve Reel Getiri", "💎 Varlık Dağılım Röntgeni"])

    with t1:
        # Kar Zarar Hesaplama
        df['Kar/Zarar %'] = ((df['guncel_fiyat'] / df['maliyet']) - 1) * 100
        df['USD Fark %'] = ((df['G_Deger']/u_now)/(df['T_Maliyet']/df['u_maliyet'])-1)*100
        df['Altın Fark %'] = ((df['G_Deger']/g_now)/(df['T_Maliyet']/df['g_maliyet'])-1)*100
        
        st.write("### Detaylı Performans Raporu")
        st.dataframe(df[['kod', 'tarih', 'maliyet', 'guncel_fiyat', 'Kar/Zarar %', 'USD Fark %', 'Altın Fark %']].style.format({
            'maliyet': '{:.6f}', 
            'guncel_fiyat': '{:.6f}',
            'Kar/Zarar %': '% {:.2f}',
            'USD Fark %': '% {:.2f}',
            'Altın Fark %': '% {:.2f}'
        }).background_gradient(cmap='RdYlGn', subset=['Kar/Zarar %', 'USD Fark %', 'Altın Fark %']), use_container_width=True)

    with t2:
        st.subheader("Hisse Bazlı Şirket Dağılımı")
        all_hisseler = []
        for _, row in df.iterrows():
            comp = KAP_DATA.get(row['kod'], {f"{row['kod']} (Hisse/Diger)": 1.0})
            for h_adi, oran in comp.items():
                all_hisseler.append({"Varlık": h_adi, "Değer": row['G_Deger'] * oran})
        
        report_df = pd.DataFrame(all_hisseler).groupby("Varlık").sum().reset_index().sort_values(by="Değer", ascending=False)
        report_df["Yüzde (%)"] = (report_df["Değer"] / report_df["Değer"].sum()) * 100

        cp, cl = st.columns([1.5, 1])
        with cp:
            st.plotly_chart(px.pie(report_df, values='Değer', names='Varlık', hole=0.4), use_container_width=True)
        with cl:
            st.dataframe(report_df.style.format({'Değer': '{:,.2f} ₺', 'Yüzde (%)': '% {:.2f}'}), use_container_width=True)

    st.divider()
    
    # Alt Toplam Paneli
    total_val = df['G_Deger'].sum()
    total_cost = df['T_Maliyet'].sum()
    total_profit = ((total_val / total_cost) - 1) * 100
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Portföy Değeri", f"{total_val:,.2f} ₺")
    m2.metric("Toplam Maliyet", f"{total_cost:,.2f} ₺")
    m3.metric("Toplam Kar/Zarar", f"% {total_profit:.2f}", delta=f"{total_val - total_cost:,.2f} ₺")

else:
    st.info("Portföyünüzü oluşturmak için sol menüden fon ekleyin.")
