import streamlit as st
import pandas as pd
import yfinance as yf
import json
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: Kesin Çözüm", layout="wide")

# --- 1. VERİ MOTORU ---
@st.cache_data(ttl=3600)
def get_kur_data(ticker, date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        data = yf.download(ticker, start=date_obj.strftime('%Y-%m-%d'), 
                           end=(date_obj + timedelta(days=7)).strftime('%Y-%m-%d'), progress=False)
        return float(data['Close'].iloc[0]) if not data.empty else 1.0
    except: return 1.0

@st.cache_data(ttl=300)
def get_live_price(ticker):
    try:
        data = yf.download(ticker, period="1d", progress=False)
        return float(data['Close'].iloc[-1]) if not data.empty else 1.0
    except: return 1.0

def get_inflation_factor(start_date):
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    today = datetime.now()
    months_diff = (today.year - start_date.year) * 12 + (today.month - start_date.month)
    return (1 + 0.042) ** max(0, months_diff)

# --- 2. SESSION STATE BAŞLATMA ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 3. SIDEBAR (DOSYA İŞLEMLERİ) ---
with st.sidebar:
    st.header("💾 Dosya İşlemleri")
    
    # JSON YÜKLEME
    uploaded_file = st.file_uploader("📂 Yedek Dosyanızı Seçin", type=['json'], key="file_uploader_unique")
    if uploaded_file is not None:
        try:
            content = json.load(uploaded_file)
            # Tarih formatlarını düzelt
            for item in content:
                if isinstance(item['tarih'], str):
                    item['tarih'] = datetime.strptime(item['tarih'], '%Y-%m-%d').date()
            st.session_state.portfolio = content
            st.success("Yedek başarıyla yüklendi!")
        except Exception as e:
            st.error(f"Yükleme hatası: {e}")

    st.divider()
    
    # JSON İNDİRME
    if st.session_state.portfolio:
        export_list = []
        for item in st.session_state.portfolio:
            new_i = item.copy()
            if hasattr(new_i['tarih'], 'strftime'):
                new_i['tarih'] = new_i['tarih'].strftime('%Y-%m-%d')
            export_list.append(new_i)
        
        st.download_button(
            label="📥 Mevcut Verileri İndir",
            data=json.dumps(export_list),
            file_name=f"portfoy_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True
        )

# --- 4. ANA EKRAN: YENİ FON EKLEME (BURASI KRİTİK) ---
st.title("⚖️ Zenith Pro: Portföy Yönetimi")

with st.container():
    st.subheader("➕ Yeni Kayıt Ekle")
    # Form kullanarak her hücrenin görünmesini ve kaydın alınmasını garanti ediyoruz
    with st.form("new_entry_form", clear_on_submit=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        
        with c1: f_kod = st.text_input("Fon Kodu", placeholder="Örn: TCD").upper().strip()
        with c2: f_tar = st.date_input("Alış Tarihi", value=datetime.now() - timedelta(days=30))
        with c3: f_adet = st.number_input("Adet", min_value=0.0, format="%.4f", step=0.0001)
        with c4: f_alis = st.number_input("Birim Alış (₺)", min_value=0.0, format="%.4f", step=0.0001)
        with c5: f_guncel = st.number_input("Birim Güncel (₺)", min_value=0.0, format="%.4f", step=0.0001)
        
        submit_button = st.form_submit_button("✅ Portföye Ekle", use_container_width=True)
        
        if submit_button:
            if f_kod and f_adet > 0:
                with st.spinner("Hesaplanıyor..."):
                    d_str = f_tar.strftime('%Y-%m-%d')
                    u_o = get_kur_data("USDTRY=X", d_str)
                    g_o = get_kur_data("GBPTRY=X", d_str)
                    gold_o = (get_kur_data("GC=F", d_str) / 31.10) * u_o
                    
                    st.session_state.portfolio.append({
                        "kod": f_kod, "tarih": f_tar, "adet": f_adet, 
                        "maliyet": f_alis, "guncel": f_guncel if f_guncel > 0 else f_alis,
                        "usd_old": u_o, "gbp_old": g_o, "gold_old": gold_o
                    })
                    st.rerun()
            else:
                st.error("Lütfen Fon Kodu ve Adet bilgilerini eksiksiz girin!")

st.divider()

# --- 5. LİSTELEME VE ANALİZ ---
if st.session_state.portfolio:
    # MEVCUT LİSTE DÜZENLEME
    with st.expander("⚙️ Portföyü Düzenle veya Sil", expanded=True):
        temp_portfolio = st.session_state.portfolio.copy()
        to_delete = None
        
        for i, item in enumerate(temp_portfolio):
            col_list = st.columns([1, 1, 1, 1, 1, 0.5])
            with col_list[0]: st.info(f"**{item['kod']}**")
            with col_list[1]: st.write(item['tarih'].strftime('%d.%m.%Y'))
            # Düzenleme hücreleri
            st.session_state.portfolio[i]['adet'] = col_list[2].number_input("Adet", value=float(item['adet']), key=f"edit_adet_{i}", label_visibility="collapsed")
            st.session_state.portfolio[i]['maliyet'] = col_list[3].number_input("Alış", value=float(item['maliyet']), key=f"edit_alis_{i}", label_visibility="collapsed")
            st.session_state.portfolio[i]['guncel'] = col_list[4].number_input("Güncel", value=float(item['guncel']), key=f"edit_gun_{i}", label_visibility="collapsed")
            
            if col_list[5].button("🗑️", key=f"del_btn_{i}"):
                to_delete = i
        
        if to_delete is not None:
            st.session_state.portfolio.pop(to_delete)
            st.rerun()

    # ANALİZ HESAPLAMA
    u_n = get_live_price("USDTRY=X")
    g_n = get_live_price("GBPTRY=X")
    gold_n = (get_live_price("GC=F") / 31.10) * u_n
    
    rows = []
    for item in st.session_state.portfolio:
        t_mal = item['adet'] * item['maliyet']
        t_gun = item['adet'] * item['guncel']
        inf = get_inflation_factor(item['tarih'])
        
        rows.append({
            "Fon": item['kod'],
            "Ana Sermaye": t_mal,
            "Güncel Değer": t_gun,
            "Enflasyon Farkı (₺)": t_gun - (t_mal * inf),
            "Dolar Farkı ($)": (t_gun / u_n) - (t_mal / item['usd_old']),
            "Sterlin Farkı (£)": (t_gun / g_n) - (t_mal / item['gbp_old']),
            "Altın Farkı (gr)": (t_gun / gold_n) - (t_mal / item['gold_old'])
        })
    
    df = pd.DataFrame(rows)

    # TABLO GÖSTERİMİ
    st.subheader("📊 Reel Getiri Raporu")
    st.dataframe(df.style.format({
        "Ana Sermaye": "{:,.2f} ₺", "Güncel Değer": "{:,.2f} ₺",
        "Enflasyon Farkı (₺)": "{:+.2f} ₺", "Dolar Farkı ($)": "{:+.2f} $",
        "Sterlin Farkı (£)": "{:+.2f} £", "Altın Farkı (gr)": "{:+.2f} gr"
    }).applymap(lambda x: 'color: #00FF00' if (isinstance(x, (int, float)) and x > 0) else 'color: #FF4B4B', 
                subset=df.columns[3:]), use_container_width=True)

    # ÖZET METRİKLER
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Toplam Sermaye", f"{df['Ana Sermaye'].sum():,.2f} ₺")
    m2.metric("Portföy Değeri", f"{df['Güncel Değer'].sum():,.2f} ₺", delta=f"{df['Güncel Değer'].sum() - df['Ana Sermaye'].sum():,.2f} ₺")
    m3.metric("Reel Dolar Farkı", f"{df['Dolar Farkı ($)'].sum():+,.2f} $")
    m4.metric("Reel Altın Farkı", f"{df['Altın Farkı (gr)'].sum():+,.2f} gr")

else:
    st.info("👋 Başlamak için yukarıdan fon ekleyin veya sol menüden yedek yükleyin.")
