import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import base64

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Portföy Pro", layout="wide")

# --- Agent Veri Modeli (Gelişmiş İçerik Dağılımı) ---
fund_details = {
    "AFT": {"hisse": 0.95, "nakit": 0.05, "emtia": 0.00, "sektor": "Teknoloji", "bolge": "ABD"},
    "TCD": {"hisse": 0.60, "nakit": 0.20, "emtia": 0.20, "sektor": "Karma", "bolge": "Türkiye"},
    "MAC": {"hisse": 0.90, "nakit": 0.10, "emtia": 0.00, "sektor": "Hisse Yoğun", "bolge": "Türkiye"},
    "GUM": {"hisse": 0.00, "nakit": 0.10, "emtia": 0.90, "sektor": "Değerli Maden", "bolge": "Küresel"}
}

# --- Session State ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- PDF Rapor Fonksiyonu ---
def create_pdf(df, total_tl, summary_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Zenith Portfoy Analiz Raporu", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, f"Toplam Portfoy Degeri: {total_tl:,.2f} TL", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(50, 10, "Fon Kodu")
    pdf.cell(50, 10, "Adet")
    pdf.cell(50, 10, "Toplam Değer")
    pdf.ln()
    
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        pdf.cell(50, 10, str(row['kod']))
        pdf.cell(50, 10, str(row['adet']))
        pdf.cell(50, 10, f"{row['Toplam TL']:,.2f} TL")
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

# --- Sidebar ---
with st.sidebar:
    st.header("📥 Portföy Girişi")
    f_code = st.text_input("Fon Kodu").upper()
    f_qty = st.number_input("Adet", min_value=1)
    f_price = st.number_input("Birim Fiyat", min_value=0.0)
    
    if st.button("➕ Ekle"):
        st.session_state.portfolio.append({"kod": f_code, "adet": f_qty, "fiyat": f_price})
        st.rerun()

    st.divider()
    if st.button("🗑️ Tümünü Temizle"):
        st.session_state.portfolio = []
        st.rerun()

# --- Ana Ekran ---
st.title("🛡️ Zenith Portföy Pro: Analiz & Rapor")

if st.session_state.portfolio:
    df = pd.DataFrame(st.session_state.portfolio)
    df['Toplam TL'] = df['adet'] * df['fiyat']
    total_tl = df['Toplam TL'].sum()

    # 1. VARLIK DAĞILIMI HESAPLAMA (AGENT)
    hisse_toplam = 0
    emtia_toplam = 0
    nakit_toplam = 0

    for _, row in df.iterrows():
        detail = fund_details.get(row['kod'], {"hisse": 0.5, "nakit": 0.3, "emtia": 0.2})
        hisse_toplam += row['Toplam TL'] * detail['hisse']
        emtia_toplam += row['Toplam TL'] * detail['emtia']
        nakit_toplam += row['Toplam TL'] * detail['nakit']

    summary_data = pd.DataFrame({
        "Enstrüman": ["Hisse Senedi", "Emtia", "Nakit/Diğer"],
        "Değer": [hisse_toplam, emtia_toplam, nakit_toplam]
    })

    # 2. GÖRSELLEŞTİRME
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Fon Dağılımı")
        fig1 = px.pie(df, values='Toplam TL', names='kod', hole=0.3)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.subheader("🔍 Gerçek Enstrüman Maruziyeti")
        fig2 = px.pie(summary_data, values='Değer', names='Enstrüman', 
                     color_discrete_sequence=px.colors.sequential.Teal)
        st.plotly_chart(fig2, use_container_width=True)

    # 3. RAPORLAMA BUTONLARI
    st.divider()
    c1, c2, c3 = st.columns(3)
    
    # CSV Kayıt (Veritabanı Alternatifi)
    csv = df.to_csv(index=False).encode('utf-8')
    c1.download_button("💾 Verileri Yedekle (CSV)", data=csv, file_name="portfoy_yedek.csv")
    
    # PDF Raporu
    pdf_bytes = create_pdf(df, total_tl, summary_data)
    c2.download_button("📄 PDF Raporu İndir", data=pdf_bytes, file_name="zenith_rapor.pdf", mime="application/pdf")
    
    # Sağlık Skoru
    c3.metric("Portföy Sağlık Skoru", "82/100", "Güçlü")

    # Detaylı Tablo
    st.subheader("📋 Fon Detayları")
    st.table(df)

else:
    st.info("Analiz için sol taraftan fon ekleyin.")
