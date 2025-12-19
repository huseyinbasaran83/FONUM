import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Portföy Agent", layout="wide")

# --- CSS ile Finansal Arayüz Özelleştirme ---
st.markdown("""
    <style>
    .main { background-color: #0f172a; }
    .stMetric { background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; }
    .stButton>button { width: 100%; border-radius: 8px; }
    .delete-btn { color: #ef4444 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. ÖNERİ: Gerçek Zamanlı Kurlar (Simüle Edilmiş API Bağlantısı) ---
# Not: Gerçek API için döviz sağlayıcı anahtarı gerekebilir, şimdilik otomatik güncel yapı kuruyoruz.
@st.cache_data(ttl=3600)
def get_live_rates():
    # Burası ileride bir API'ye (örn: fixer.io) bağlanabilir
    return {"USD_TRY": 32.85, "GRAM_GOLD_TRY": 2680.0, "GBP_TRY": 41.50}

rates = get_live_rates()

# --- 3. ÖNERİ: Fon İçerik Kütüphanesi (Agent Verisi) ---
fund_db = {
    "AFT": {"ad": "Ak Portföy Yeni Teknolojiler", "risk": 6, "usd_etki": 0.90},
    "TCD": {"ad": "Tacirler Değişken Fon", "risk": 7, "usd_etki": 0.40},
    "MAC": {"ad": "Marmara Capital Hisse", "risk": 6, "usd_etki": 0.10},
    "GUM": {"ad": "Gümüş Serbest Fon", "risk": 7, "usd_etki": 0.80}
}

# --- Session State Başlatma ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- Sidebar: Fon Girişi ---
with st.sidebar:
    st.header("📥 Portföy Yönetimi")
    f_code = st.text_input("Fon Kodu", placeholder="Örn: AFT").upper()
    f_qty = st.number_input("Adet", min_value=0, value=1)
    f_price = st.number_input("Birim Fiyat (TL)", min_value=0.0, value=10.0, step=0.1)
    
    if st.button("➕ Portföye Ekle"):
        if f_code:
            st.session_state.portfolio.append({
                "id": len(st.session_state.portfolio),
                "kod": f_code, 
                "adet": f_qty, 
                "fiyat": f_price
            })
            st.success(f"{f_code} eklendi!")

# --- Ana Panel ---
st.title("🛡️ Zenith Portföy Analiz Agent")

if st.session_state.portfolio:
    df = pd.DataFrame(st.session_state.portfolio)
    df['Toplam TL'] = df['adet'] * df['fiyat']
    total_tl = df['Toplam TL'].sum()

    # Üst Metrikler
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Toplam Büyüklük", f"{total_tl:,.0f} ₺")
    m2.metric("USD Karşılığı", f"${total_tl/rates['USD_TRY']:,.2f}")
    m3.metric("Altın Karşılığı", f"{total_tl/rates['GRAM_GOLD_TRY']:,.2f} gr")
    m4.metric("Güncel Kur (USD)", f"{rates['USD_TRY']} ₺")

    st.divider()

    # --- 2. ÖNERİ: Grafikler & Analiz ---
    col_chart, col_scenario = st.columns([1, 1])

    with col_chart:
        st.subheader("📊 Varlık Dağılımı")
        fig = px.pie(df, values='Toplam TL', names='kod', hole=0.4,
                     color_discrete_sequence=px.colors.sequential.RdBu)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig, use_container_width=True)

    with col_scenario:
        st.subheader("🧪 Senaryo Analizi")
        usd_change = st.slider("USD Değişimi (%)", -20, 50, 0)
        
        # Agent Mantığı: Fon kütüphanesinden USD etkisini çek, yoksa 0.5 kabul et
        weighted_usd_impact = 0
        for p in st.session_state.portfolio:
            impact_ratio = fund_db.get(p['kod'], {"usd_etki": 0.5})["usd_etki"]
            weighted_usd_impact += (p['adet'] * p['fiyat'] / total_tl) * impact_ratio
        
        sim_val = total_tl * (1 + (usd_change/100 * weighted_usd_impact))
        diff = sim_val - total_tl
        
        st.metric("Senaryo Sonucu", f"{sim_val:,.0f} ₺", f"{diff:,.0f} ₺")
        st.info(f"**Agent Notu:** Portföyünüzün USD hassasiyeti %{weighted_usd_impact*100:.1f}. Kur artışından bu oranda etkilenirsiniz.")

    # --- FON SİLME ÖZELLİĞİ ---
    st.subheader("📋 Fon Listesi ve Yönetim")
    
    # Listeyi kullanıcıya göster ve her satıra silme butonu koy
    for index, row in df.iterrows():
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        c1.write(f"**{row['kod']}**")
        c2.write(f"{row['adet']} Adet")
        c3.write(f"{row['Toplam TL']:,.2f} ₺")
        if c4.button("❌ Sil", key=f"del_{index}"):
            st.session_state.portfolio.pop(index)
            st.rerun() # Sayfayı yenileyerek listeyi günceller

else:
    st.warning("Henüz fon eklenmedi. Lütfen sol taraftaki panelden fon girişlerini yapın.")
    st.image("https://images.unsplash.com/photo-1611974717482-58a25a3d1d3e?auto=format&fit=crop&q=80&w=1000", caption="Analize başlamak için veri girişi yapın.")
