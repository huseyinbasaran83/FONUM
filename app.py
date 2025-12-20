import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith: Reel Birim Analizi", layout="wide")

# --- 1. VERİ MOTORU ---
@st.cache_data(ttl=3600)
def get_kur_data(ticker, date_obj):
    try:
        data = yf.download(ticker, start=date_obj.strftime('%Y-%m-%d'), 
                           end=(date_obj + timedelta(days=7)).strftime('%Y-%m-%d'), progress=False)
        return float(data['Close'].iloc[0]) if not data.empty else None
    except: return None

@st.cache_data(ttl=600)
def get_live_price(ticker):
    try:
        data = yf.download(ticker, period="1d", progress=False)
        return float(data['Close'].iloc[-1]) if not data.empty else 1.0
    except: return 1.0

# --- 2. SESSION STATE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("📥 İşlem Girişi")
    f_code = st.text_input("Fon Kodu").upper().strip()
    f_date = st.date_input("Alış Tarihi", value=datetime.now() - timedelta(days=180))
    f_qty = st.number_input("Adet", min_value=0.0, format="%.4f")
    f_cost = st.number_input("Alış Fiyatı (TL)", min_value=0.0, format="%.4f")
    f_now = st.number_input("Güncel Birim Fiyat (TL)", min_value=0.0, value=f_cost, format="%.4f")
    
    if st.button("➕ Portföye Ekle", use_container_width=True):
        with st.spinner("Kurlar hesaplanıyor..."):
            usd_old = get_kur_data("USDTRY=X", f_date)
            gbp_old = get_kur_data("GBPTRY=X", f_date)
            gold_old = (get_kur_data("GC=F", f_date) / 31.10) * (usd_old if usd_old else 1)
            
            st.session_state.portfolio.append({
                "kod": f_code, "tarih": f_date, "adet": f_qty, 
                "maliyet": f_cost, "guncel": f_now,
                "usd_old": usd_old, "gbp_old": gbp_old, "gold_old": gold_old
            })
            st.rerun()

# --- 4. ANA EKRAN ---
st.title("⚖️ Zenith: Satın Alma Gücü Analizi")

if st.session_state.portfolio:
    # Güncel Kurlar
    u_now = get_live_price("USDTRY=X")
    g_now = get_live_price("GBPTRY=X")
    gold_now = (get_live_price("GC=F") / 31.10) * u_now
    
    rows = []
    for item in st.session_state.portfolio:
        total_maliyet = item['adet'] * item['maliyet']
        total_guncel = item['adet'] * item['guncel']
        
        # O günkü sermaye ile alınabilecek birimler
        units_usd_then = total_maliyet / item['usd_old']
        units_gbp_then = total_maliyet / item['gbp_old']
        units_gold_then = total_maliyet / item['gold_old']
        
        # Bugün o parayla (fonun güncel değeriyle) alınabilecek birimler
        units_usd_now = total_guncel / u_now
        units_gbp_now = total_guncel / g_now
        units_gold_now = total_guncel / gold_now
        
        # Reel Fark (Adet/Birim Bazında)
        diff_usd = units_usd_now - units_usd_then
        diff_gbp = units_gbp_now - units_gbp_then
        diff_gold = units_gold_now - units_gold_then
        
        rows.append({
            "Fon": item['kod'],
            "Alış Tarihi": item['tarih'],
            "Güncel Değer (₺)": total_guncel,
            "Fark ($)": diff_usd,
            "Fark (£)": diff_gbp,
            "Fark (Gram Altın)": diff_gold
        })
    
    df_diff = pd.DataFrame(rows)
    
    # 1. TABLO: BİRİM BAZLI FARK
    st.subheader("🛡️ Reel Kazanç/Kayıp (Birim Bazında)")
    st.markdown("> **Açıklama:** Eğer değer pozitifse, fonunuz o yatırım aracını yenmiş demektir. Negatifse, o yatırım aracına göre kaç birim (Dolar, Sterlin, Altın) kaybettiğinizi gösterir.")
    
    st.dataframe(df_diff.style.format({
        "Güncel Değer (₺)": "{:,.2f}",
        "Fark ($)": "{:+.2f} $",
        "Fark (£)": "{:+.2f} £",
        "Fark (Gram Altın)": "{:+.2f} gr"
    }).applymap(lambda x: 'color: green' if (isinstance(x, float) and x > 0) else 'color: red', 
                subset=["Fark ($)", "Fark (£)", "Fark (Gram Altın)"]), use_container_width=True)

    st.divider()

    # 2. GRAFİK: REEL KAYIP/KAZANÇ RÖNTGENİ
    st.subheader("📊 Birim Bazlı Kar/Zarar Grafiği")
    
    # Görselleştirme için eritme
    df_melted = df_diff.melt(id_vars=["Fon"], value_vars=["Fark ($)", "Fark (£)", "Fark (Gram Altın)"], 
                             var_name="Varlık", value_name="Miktar")
    
    fig = px.bar(df_melted, x="Fon", y="Miktar", color="Varlık", barmode="group",
                 title="Fonların Alternatif Yatırımlara Karşı Birim Performansı",
                 labels={"Miktar": "Kazanılan/Kaybedilen Birim"},
                 color_discrete_map={"Fark ($)": "#008744", "Fark (£)": "#0057e7", "Fark (Gram Altın)": "#ffa700"})
    
    # Sıfır çizgisini belirginleştir
    fig.add_hline(y=0, line_dash="dash", line_color="white")
    st.plotly_chart(fig, use_container_width=True)

    

    # 3. ÖZET PANELİ
    st.subheader("🏁 Toplam Satın Alma Gücü Değişimi")
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Dolar Farkı", f"{df_diff['Fark ($)'].sum():+,.2f} $")
    c2.metric("Toplam Sterlin Farkı", f"{df_diff['Fark (£)'].sum():+,.2f} £")
    c3.metric("Toplam Altın Farkı", f"{df_diff['Fark (Gram Altın)'].sum():+,.2f} gr")

else:
    st.info("Kıyaslama için sol taraftan fon ekleyin.")
