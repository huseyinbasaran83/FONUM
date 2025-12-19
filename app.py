import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Portföy Pro", layout="wide")

# --- GENİŞLETİLMİŞ VE DETAYLANDIRILMIŞ VARLIK VERİTABANI ---
# Yerli ve yabancı fonların en güncel yaklaşık portföy dağılımları
fund_composition = {
    "AFT": {
        "detay": {"NVIDIA": 0.18, "APPLE": 0.15, "MICROSOFT": 0.12, "ALPHABET": 0.10, "META": 0.08, "NAKİT/DİĞER": 0.37},
        "tip": "Yabancı Teknoloji"
    },
    "TCD": {
        "detay": {"TÜPRAŞ": 0.15, "KOÇ HOLDİNG": 0.12, "ASELSAN": 0.10, "THY": 0.08, "ALTIN": 0.15, "GÜMÜŞ": 0.10, "PPZ/NAKİT": 0.30},
        "tip": "Değişken"
    },
    "MAC": {
        "detay": {"THY": 0.18, "BİMAS": 0.14, "EREĞLİ": 0.12, "SAHOL": 0.10, "MGROS": 0.08, "KCHOL": 0.08, "DİĞER HİSSE": 0.30},
        "tip": "Hisse Yoğun"
    },
    "GUM": {
        "detay": {"GÜMÜŞ (SPOT)": 0.85, "GÜMÜŞ VADELİ": 0.10, "NAKİT": 0.05},
        "tip": "Emtia"
    },
    "TI3": { # İş Portföy İhracatçı Şirketler
        "detay": {"FROTO": 0.15, "SISE": 0.12, "TOASO": 0.10, "ARCLK": 0.08, "KCHOL": 0.08, "DİĞER": 0.47},
        "tip": "Hisse Yoğun"
    },
    "ZRE": { # Ziraat Portföy BIST30
        "detay": {"THY": 0.10, "TUPRS": 0.09, "AKBNK": 0.08, "ISCTR": 0.08, "KCHOL": 0.07, "EREGL": 0.06, "DİĞER": 0.52},
        "tip": "Endeks"
    }
}

# --- Session State Yönetimi ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- Yardımcı Fonksiyonlar ---
def safe_str(text):
    tr_map = str.maketrans("ğĞüÜşŞİıöÖçÇ", "gGuUsSIioOcC")
    return str(text).translate(tr_map)

# --- Sidebar: Yeni Fon Ekleme ---
with st.sidebar:
    st.header("📥 Yeni Fon Ekle")
    f_code = st.text_input("Fon Kodu", placeholder="AFT, TCD, MAC, TI3, ZRE...").upper()
    f_qty = st.number_input("Adet", min_value=1, value=100)
    f_price = st.number_input("Birim Fiyat (TL)", min_value=0.0, value=15.0)
    
    if st.button("➕ Portföye Ekle", use_container_width=True):
        if f_code:
            st.session_state.portfolio.append({"kod": f_code, "adet": f_qty, "fiyat": f_price})
            st.rerun()

    st.divider()
    if st.session_state.portfolio:
        if st.checkbox("⚠️ Portföyü Sıfırla (Onay)"):
            if st.button("🚨 TÜMÜNÜ SİL"):
                st.session_state.portfolio = []
                st.rerun()

# --- Ana Ekran ---
st.title("🛡️ Zenith Portföy: Yerli & Yabancı Derin Analiz")

if st.session_state.portfolio:
    st.subheader("⚙️ Portföy Yönetimi")
    
    # Düzenleme Paneli
    for idx, item in enumerate(st.session_state.portfolio):
        c1, c2, c3, c4, c5 = st.columns([1, 1.5, 1.5, 1.5, 0.7])
        with c1: st.write(f"**{item['kod']}**")
        with c2: st.session_state.portfolio[idx]['adet'] = st.number_input("Adet", value=float(item['adet']), key=f"q_{idx}")
        with c3: st.session_state.portfolio[idx]['fiyat'] = st.number_input("Fiyat", value=float(item['fiyat']), key=f"p_{idx}")
        with c4: st.write(f"Değer: **{item['adet'] * item['fiyat']:,.2f} ₺**")
        with c5: 
            if st.button("🗑️", key=f"d_{idx}"):
                st.session_state.portfolio.pop(idx)
                st.rerun()

    st.divider()

    # --- ANALİZ VE HESAPLAMALAR ---
    df = pd.DataFrame(st.session_state.portfolio)
    df['Toplam TL'] = df['adet'] * df['fiyat']
    total_tl = df['Toplam TL'].sum()

    asset_breakdown = {}
    for _, row in df.iterrows():
        # Veritabanında yoksa genel 'DİĞER' olarak ata
        fund_info = fund_composition.get(row['kod'], {"detay": {f"{row['kod']} - DİĞER": 1.0}})
        for asset, ratio in fund_info['detay'].items():
            asset_breakdown[asset] = asset_breakdown.get(asset, 0) + (row['Toplam TL'] * ratio)

    breakdown_df = pd.DataFrame(list(asset_breakdown.items()), columns=['Varlık', 'Değer']).sort_values(by='Değer', ascending=False)

    # --- GÖRSELLEŞTİRME ---
    
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("📊 Fon Dağılımı")
        st.plotly_chart(px.pie(df, values='Toplam TL', names='kod', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel), use_container_width=True)
    with col_right:
        st.subheader("💎 Hisse/Emtia Bazlı Röntgen")
        st.plotly_chart(px.bar(breakdown_df.head(12), x='Değer', y='Varlık', orientation='h', color='Değer', color_continuous_scale='Bluered_r'), use_container_width=True)

    # --- TABLO VE RAPOR ---
    st.subheader("🔍 Tüm Varlıkların Listesi")
    display_df = breakdown_df.copy()
    display_df['Pay (%)'] = (display_df['Değer'] / total_tl) * 100
    st.dataframe(display_df.style.format({'Değer': '{:,.2f} TL', 'Pay (%)': '{:.2f}%'}), use_container_width=True)

    # Rapor ve Yedekleme
    m1, m2 = st.columns(2)
    csv_data = df.to_csv(index=False).encode('utf-8')
    m1.download_button("💾 Verileri Yedekle (CSV)", data=csv_data, file_name="zenith_portfoy.csv", use_container_width=True)
    m2.info(f"Toplam Portföy Değeri: {total_tl:,.2f} ₺")

else:
    st.info("Analiz için fon ekleyin. Örnek kodlar: AFT, TCD, MAC, TI3, ZRE, GUM")
