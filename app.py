import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: Portföy Yönetimi", layout="wide")

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

def get_inflation_factor(start_date):
    months_diff = (datetime.now().year - start_date.year) * 12 + (datetime.now().month - start_date.month)
    monthly_rate = 0.042 # Varsayılan aylık enflasyon
    return (1 + monthly_rate) ** max(0, months_diff)

# --- 2. SESSION STATE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 3. SIDEBAR: İŞLEM GİRİŞİ ---
with st.sidebar:
    st.header("📥 Yeni Fon Ekle")
    f_code = st.text_input("Fon Kodu").upper().strip()
    f_date = st.date_input("Alış Tarihi", value=datetime.now() - timedelta(days=365))
    f_qty = st.number_input("Adet", min_value=0.0, format="%.4f")
    f_cost = st.number_input("Alış Fiyatı (TL)", min_value=0.0, format="%.4f")
    f_now = st.number_input("Güncel Birim Fiyat (TL)", min_value=0.0, value=f_cost, format="%.4f")
    
    if st.button("➕ Portföye Ekle", use_container_width=True):
        if f_code and f_qty > 0:
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
st.title("🛡️ Zenith Pro: Portföy Yönetim Paneli")

if st.session_state.portfolio:
    st.subheader("⚙️ Mevcut Fonları Düzenle veya Sil")
    
    # Başlıklar
    h_cols = st.columns([0.8, 1, 1.2, 1.2, 1.2, 0.4])
    h_labels = ["Fon", "Alış Tarihi", "Adet", "Maliyet (₺)", "Güncel (₺)", "Sil"]
    for col, label in zip(h_cols, h_labels):
        col.write(f"**{label}**")

    # Fonları listele ve düzenleme imkanı ver
    to_delete = None
    for idx, item in enumerate(st.session_state.portfolio):
        c = st.columns([0.8, 1, 1.2, 1.2, 1.2, 0.4])
        with c[0]: st.info(f"**{item['kod']}**")
        with c[1]: st.write(item['tarih'].strftime('%d.%m.%Y'))
        with c[2]: 
            st.session_state.portfolio[idx]['adet'] = c[2].number_input("Adet", value=float(item['adet']), key=f"q_{idx}", format="%.4f", label_visibility="collapsed")
        with c[3]: 
            st.session_state.portfolio[idx]['maliyet'] = c[3].number_input("Maliyet", value=float(item['maliyet']), key=f"m_{idx}", format="%.4f", label_visibility="collapsed")
        with c[4]: 
            st.session_state.portfolio[idx]['guncel'] = c[4].number_input("Güncel", value=float(item['guncel']), key=f"g_{idx}", format="%.4f", label_visibility="collapsed")
        with c[5]: 
            if c[5].button("🗑️", key=f"del_{idx}"):
                to_delete = idx

    if to_delete is not None:
        st.session_state.portfolio.pop(to_delete)
        st.rerun()

    st.divider()

    # --- ANALİZ HESAPLAMALARI ---
    u_now = get_live_price("USDTRY=X")
    g_now = get_live_price("GBPTRY=X")
    gold_now = (get_live_price("GC=F") / 31.10) * u_now
    
    rows = []
    for item in st.session_state.portfolio:
        total_maliyet = item['adet'] * item['maliyet']
        total_guncel = item['adet'] * item['guncel']
        inf_factor = get_inflation_factor(item['tarih'])
        
        diff_usd = (total_guncel / u_now) - (total_maliyet / item['usd_old'])
        diff_gbp = (total_guncel / g_now) - (total_maliyet / item['gbp_old'])
        diff_gold = (total_guncel / gold_now) - (total_maliyet / item['gold_old'])
        reel_tl_fark = total_guncel - (total_maliyet * inf_factor)
        
        rows.append({
            "Fon": item['kod'],
            "Reel Fark (Enf. ₺)": reel_tl_fark,
            "Fark ($)": diff_usd,
            "Fark (£)": diff_gbp,
            "Fark (Altın gr)": diff_gold,
            "Güncel Değer": total_guncel
        })
    
    df_reel = pd.DataFrame(rows)

    # --- SONUÇ TABLOSU VE GRAFİK ---
    t1, t2 = st.tabs(["📈 Reel Performans", "📊 Görsel Analiz"])
    
    with t1:
        st.dataframe(df_reel.style.format({
            "Reel Fark (Enf. ₺)": "{:+.2f} ₺", "Fark ($)": "{:+.2f} $",
            "Fark (£)": "{:+.2f} £", "Fark (Altın gr)": "{:+.2f} gr", "Güncel Değer": "{:,.2f} ₺"
        }).applymap(lambda x: 'color: #00FF00' if (isinstance(x, (int, float)) and x > 0) else 'color: #FF4B4B', 
                    subset=df_reel.columns[1:5]), use_container_width=True)

    with t2:
        df_melted = df_reel.melt(id_vars=["Fon"], value_vars=["Fark ($)", "Fark (£)", "Fark (Altın gr)"], 
                                 var_name="Varlık", value_name="Miktar")
        fig = px.bar(df_melted, x="Fon", y="Miktar", color="Varlık", barmode="group",
                     title="Varlık Bazında Reel Kazanç/Kayıp")
        st.plotly_chart(fig, use_container_width=True)

    # --- ÖZET METRİKLER ---
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Enflasyon Karşısı", f"{df_reel['Reel Fark (Enf. ₺)'].sum():+,.2f} ₺")
    m2.metric("Toplam USD Farkı", f"{df_reel['Fark ($)'].sum():+,.2f} $")
    m3.metric("Toplam GBP Farkı", f"{df_reel['Fark (£)'].sum():+,.2f} £")
    m4.metric("Toplam Altın Farkı", f"{df_reel['Fark (Altın gr)'].sum():+,.2f} gr")

else:
    st.info("Sol taraftan fon ekleyerek analizi başlatabilirsiniz.")
