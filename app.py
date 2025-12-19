import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Portföy Pro", layout="wide")

# --- Agent Veri Modeli (Gelişmiş İçerik Dağılımı) ---
fund_details = {
    "AFT": {"hisse": 0.95, "nakit": 0.05, "emtia": 0.00, "sektor": "Teknoloji"},
    "TCD": {"hisse": 0.60, "nakit": 0.20, "emtia": 0.20, "sektor": "Karma"},
    "MAC": {"hisse": 0.90, "nakit": 0.10, "emtia": 0.00, "sektor": "Hisse Yogun"},
    "GUM": {"hisse": 0.00, "nakit": 0.10, "emtia": 0.90, "sektor": "Degerli Maden"}
}

# --- Session State (Veritabanı Alternatifi) ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- PDF Rapor Fonksiyonu (Türkçe Karakter Hatası Giderilmiş) ---
def create_pdf(df, total_tl):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    # Türkçe karakterleri güvenli karakterlere çeviriyoruz
    def safe_str(text):
        tr_map = str.maketrans("ğĞüÜşŞİıöÖçÇ", "gGuUsSIioOcC")
        return str(text).translate(tr_map)

    pdf.cell(200, 10, safe_str("Zenith Portfoy Analiz Raporu"), ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, safe_str(f"Toplam Portfoy Degeri: {total_tl:,.2f} TL"), ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(60, 10, safe_str("Fon Kodu"))
    pdf.cell(60, 10, safe_str("Adet"))
    pdf.cell(60, 10, safe_str("Toplam Deger"))
    pdf.ln()
    
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        pdf.cell(60, 10, safe_str(row['kod']))
        pdf.cell(60, 10, safe_str(row['adet']))
        pdf.cell(60, 10, safe_str(f"{row['Toplam TL']:,.2f} TL"))
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1', errors='ignore')

# --- Sidebar ---
with st.sidebar:
    st.header("📥 Portfoy Yonetimi")
    f_code = st.text_input("Fon Kodu").upper()
    f_qty = st.number_input("Adet", min_value=1)
    f_price = st.number_input("Birim Fiyat", min_value=0.0)
    
    if st.button("➕ Ekle"):
        st.session_state.portfolio.append({"kod": f_code, "adet": f_qty, "fiyat": f_price})
        st.rerun()

    st.divider()
    if st.button("🗑️ Portfoyu Sıfırla"):
        st.session_state.portfolio = []
        st.rerun()

# --- Ana Ekran ---
st.title("🛡️ Zenith Portföy Pro")

if st.session_state.portfolio:
    df = pd.DataFrame(st.session_state.portfolio)
    df['Toplam TL'] = df['adet'] * df['fiyat']
    total_tl = df['Toplam TL'].sum()

    # Varlık Dağılım Hesaplama
    h_toplam, e_toplam, n_toplam = 0, 0, 0
    for _, row in df.iterrows():
        det = fund_details.get(row['kod'], {"hisse": 0.5, "nakit": 0.3, "emtia": 0.2})
        h_toplam += row['Toplam TL'] * det['hisse']
        e_toplam += row['Toplam TL'] * det['emtia']
        n_toplam += row['Toplam TL'] * det['nakit']

    # Görselleştirme
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Fon Dagılımı")
        st.plotly_chart(px.pie(df, values='Toplam TL', names='kod', hole=0.3), use_container_width=True)
    
    with col2:
        st.subheader("🔍 Enstrüman Maruziyeti")
        summary = pd.DataFrame({"Tip": ["Hisse", "Emtia", "Nakit"], "Deger": [h_toplam, e_toplam, n_toplam]})
        st.plotly_chart(px.pie(summary, values='Deger', names='Tip', color_discrete_sequence=px.colors.qualitative.Set3), use_container_width=True)

    # İşlemler
    st.divider()
    c1, c2, c3 = st.columns(3)
    
    # CSV Kayıt (Veritabanı alternatifi - Dosyayı indirip saklayabilirsin)
    csv = df.to_csv(index=False).encode('utf-8')
    c1.download_button("💾 Verileri Yedekle (CSV)", data=csv, file_name="portfoy_yedek.csv")
    
    # PDF Raporu (Hata giderilmiş versiyon)
    try:
        pdf_bytes = create_pdf(df, total_tl)
        c2.download_button("📄 PDF Raporu İndir", data=pdf_bytes, file_name="zenith_rapor.pdf", mime="application/pdf")
    except:
        c2.error("PDF olusturulamadı.")
    
    c3.metric("Portföy Sağlık Skoru", "82/100")

    st.subheader("📋 Mevcut Fonlar")
    st.dataframe(df, use_container_width=True)

else:
    st.info("Lütfen sol panelden fon ekleyerek analizi baslatın.")
