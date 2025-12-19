import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Portföy Pro", layout="wide")

# --- GENİŞLETİLMİŞ VARLIK VERİTABANI (Agent Analiz Modeli) ---
# Burada her fonun içindeki gerçek varlıkları ve oranlarını tanımlıyoruz
fund_composition = {
    "AFT": {
        "detay": {"NVIDIA": 0.18, "APPLE": 0.15, "MICROSOFT": 0.12, "ALPHABET": 0.10, "NAKİT": 0.45},
        "tip": "Yabancı Hisse"
    },
    "TCD": {
        "detay": {"TÜPRAŞ": 0.12, "KKOÇ HOLDİNG": 0.10, "ALTIN": 0.15, "GÜMÜŞ": 0.10, "VADELİ/NAKİT": 0.53},
        "tip": "Değişken"
    },
    "MAC": {
        "detay": {"THY": 0.15, "BİMAS": 0.12, "EREĞLİ": 0.10, "SAHOL": 0.08, "DİĞER HİSSE": 0.55},
        "tip": "Hisse Yoğun"
    },
    "GUM": {
        "detay": {"GÜMÜŞ": 0.92, "NAKİT": 0.08},
        "tip": "Emtia"
    }
}

# --- Session State ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- PDF Rapor Fonksiyonu (Güvenli Karakterler) ---
def create_pdf(df, total_tl, asset_summary):
    pdf = FPDF()
    pdf.add_page()
    def safe_str(text):
        tr_map = str.maketrans("ğĞüÜşŞİıöÖçÇ", "gGuUsSIioOcC")
        return str(text).translate(tr_map)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, safe_str("Zenith Portfoy Derinlik Analiz Raporu"), ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, safe_str(f"Toplam Buyukluk: {total_tl:,.2f} TL"), ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(100, 10, safe_str("Varlık Adı"))
    pdf.cell(80, 10, safe_str("Tahmini Değer (TL)"))
    pdf.ln()
    
    pdf.set_font("Arial", "", 10)
    for asset, val in asset_summary.items():
        pdf.cell(100, 10, safe_str(asset))
        pdf.cell(80, 10, f"{val:,.2f} TL")
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1', errors='ignore')

# --- Sidebar ---
with st.sidebar:
    st.header("📥 Portföy Yönetimi")
    f_code = st.text_input("Fon Kodu (AFT, TCD, MAC, GUM)").upper()
    f_qty = st.number_input("Adet", min_value=1)
    f_price = st.number_input("Birim Fiyat", min_value=0.0)
    
    if st.button("➕ Portföye Ekle"):
        st.session_state.portfolio.append({"kod": f_code, "adet": f_qty, "fiyat": f_price})
        st.rerun()

    if st.button("🗑️ Portfoyu Sıfırla"):
        st.session_state.portfolio = []
        st.rerun()

# --- Ana Ekran ---
st.title("🛡️ Zenith Portföy: Derin Analiz")

if st.session_state.portfolio:
    df = pd.DataFrame(st.session_state.portfolio)
    df['Toplam TL'] = df['adet'] * df['fiyat']
    total_tl = df['Toplam TL'].sum()

    # 1. GERÇEK VARLIK DAĞILIMI HESAPLAMA (DERİN ANALİZ)
    asset_breakdown = {}

    for _, row in df.iterrows():
        fund_info = fund_composition.get(row['kod'], {"detay": {"DİĞER": 1.0}})
        for asset, ratio in fund_info['detay'].items():
            value = row['Toplam TL'] * ratio
            asset_breakdown[asset] = asset_breakdown.get(asset, 0) + value

    # Grafik Verisi Hazırlama
    breakdown_df = pd.DataFrame(list(asset_breakdown.items()), columns=['Varlık', 'Değer'])
    breakdown_df = breakdown_df.sort_values(by='Değer', ascending=False)

    # 2. GÖRSELLEŞTİRME
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.subheader("📊 Fon Bazlı Dağılım")
        st.plotly_chart(px.pie(df, values='Toplam TL', names='kod', hole=0.4), use_container_width=True)
    
    with c2:
        st.subheader("💎 Gerçek Varlık Kırılımı (Top 10)")
        fig_bar = px.bar(breakdown_df.head(10), x='Değer', y='Varlık', orientation='h', 
                         color='Değer', color_continuous_scale='Viridis')
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    # 3. DETAYLI TABLO VE RAPOR
    st.divider()
    st.subheader("🔍 Portföyün Röntgeni (Hisse & Emtia Detayı)")
    
    col_tab, col_action = st.columns([2, 1])
    
    with col_tab:
        # Tablo görünümü
        display_df = breakdown_df.copy()
        display_df['Pay (%)'] = (display_df['Değer'] / total_tl) * 100
        st.dataframe(display_df.style.format({'Değer': '{:,.2f} TL', 'Pay (%)': '{:.2f}%'}), use_container_width=True)

    with col_action:
        st.metric("Toplam Portföy", f"{total_tl:,.2f} ₺")
        st.write("---")
        # PDF ve Yedekleme
        try:
            pdf_data = create_pdf(df, total_tl, asset_breakdown)
            st.download_button("📄 PDF Derin Analiz Raporu", data=pdf_data, file_name="zenith_derin_analiz.pdf")
        except:
            st.error("Rapor oluşturma hatası.")
        
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Verileri Yedekle (CSV)", data=csv_data, file_name="portfoy.csv")

else:
    st.info("Lütfen sol panelden kodları girin (Örn: AFT, TCD, MAC, GUM)")
