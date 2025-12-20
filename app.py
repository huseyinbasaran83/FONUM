import streamlit as st
import pandas as pd
import yfinance as yf
import json
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Zenith Pro: Tam Çözüm", layout="wide")

# --- 1. VERİLERİ KURTARMA (PAYLAŞTIĞIN JSON VERİSİ) ---
# JSON dosyan bozuk olsa bile bu liste uygulamanın içinde her zaman çalışacak
V_YEDEK = [
    {"kod": "NLE", "tarih": "2025-06-04", "adet": 13922.0, "maliyet": 1.005556, "guncel": 1.259509, "usd_old": 39.1445999},
    {"kod": "NLE", "tarih": "2025-07-29", "adet": 20262.0, "maliyet": 1.243136, "guncel": 1.259509, "usd_old": 40.561698},
    {"kod": "TTE", "tarih": "2024-02-06", "adet": 14955.0, "maliyet": 0.787447, "guncel": 0.991358, "usd_old": 30.536800},
    {"kod": "DTM", "tarih": "2025-06-13", "adet": 11064.0, "maliyet": 0.994418, "guncel": 1.145821, "usd_old": 39.395599},
    {"kod": "ICZ", "tarih": "2024-02-06", "adet": 1781.0, "maliyet": 4.399736, "guncel": 5.894043, "usd_old": 30.536800},
    {"kod": "BDS", "tarih": "2025-04-09", "adet": 1180.0, "maliyet": 1.694492, "guncel": 2.370899, "usd_old": 38.007999},
    {"kod": "BDS", "tarih": "2025-09-18", "adet": 3213.0, "maliyet": 2.489381, "guncel": 2.370899, "usd_old": 41.301101},
    {"kod": "KOT", "tarih": "2025-08-26", "adet": 4004.0, "maliyet": 1.248606, "guncel": 1.22724, "usd_old": 41.003501},
    {"kod": "KOT", "tarih": "2025-11-03", "adet": 4164.0, "maliyet": 1.200711, "guncel": 1.22724, "usd_old": 42.039619},
    {"kod": "IIH", "tarih": "2024-02-06", "adet": 283.0, "maliyet": 17.322261, "guncel": 27.889396, "usd_old": 30.536800},
    {"kod": "IIH", "tarih": "2025-03-14", "adet": 76.0, "maliyet": 26.2125, "guncel": 27.889396, "usd_old": 36.679599}
]

if 'portfoy' not in st.session_state or not st.session_state.portfoy:
    for item in V_YEDEK:
        if isinstance(item['tarih'], str):
            item['tarih'] = datetime.strptime(item['tarih'], '%Y-%m-%d').date()
    st.session_state.portfoy = V_YEDEK

# --- 2. FONKSİYONLAR (HATA KORUMALI) ---
def get_safe_usd():
    try:
        data = yf.download("USDTRY=X", period="1d", progress=False)
        if not data.empty:
            # Veriyi zorla float'a çeviriyoruz (TypeError engelleyici)
            return float(data['Close'].iloc[-1])
        return 35.0 # Veri gelmezse varsayılan
    except:
        return 35.0

# --- 3. ANA ARAYÜZ ---
st.title("🛡️ Zenith Pro: Kesin Çözüm")

with st.expander("➕ Yeni Fon Ekle", expanded=False):
    c1, c2, c3, c4, c5 = st.columns(5)
    f_kod = c1.text_input("Kod").upper()
    f_tar = c2.date_input("Tarih")
    f_qty = c3.number_input("Adet", value=0.0, format="%.4f")
    f_ali = c4.number_input("Alış (₺)", value=0.0, format="%.4f")
    f_gun = c5.number_input("Güncel (₺)", value=0.0, format="%.4f")
    
    if st.button("Kaydet"):
        if f_kod and f_qty > 0:
            d_s = f_tar.strftime('%Y-%m-%d')
            try:
                u_old = float(yf.download("USDTRY=X", start=d_s, end=(f_tar + timedelta(days=5)), progress=False)['Close'].iloc[0])
            except: u_old = 30.0
            
            st.session_state.portfoy.append({
                "kod": f_kod, "tarih": f_tar, "adet": f_qty, "maliyet": f_ali, "guncel": f_gun, "usd_old": u_old
            })
            st.rerun()

# --- 4. HESAPLAMA VE TABLO ---
if st.session_state.portfoy:
    u_now = get_safe_usd()
    
    tablo_listesi = []
    for i, f in enumerate(st.session_state.portfoy):
        # Sayısal değerleri garantiye alıyoruz
        qty = float(f['adet'])
        cost = float(f['maliyet'])
        now_p = float(f['guncel'])
        u_old = float(f.get('usd_old', 1.0))
        
        m_top = qty * cost
        g_top = qty * now_p
        
        # Hata veren hesaplama kısmını basitleştirdik
        dolar_fark = (g_top / u_now) - (m_top / u_old)
        
        tablo_listesi.append({
            "FON": f['kod'],
            "ADET": qty,
            "TOPLAM MALİYET": f"{m_top:,.2f} ₺",
            "GÜNCEL DEĞER": f"{g_top:,.2f} ₺",
            "K/Z (₺)": f"{(g_top - m_top):,.2f} ₺",
            "DOLAR FARKI ($)": f"{dolar_fark:,.2f} $"
        })
        
        if st.button(f"🗑️ {f['kod']} Sil", key=f"del_{i}"):
            st.session_state.portfoy.pop(i)
            st.rerun()

    st.subheader("📊 Analiz Tablosu")
    st.table(tablo_listesi)
    
    # Metrikler
    st.divider()
    m1, m2 = st.columns(2)
    t_m = sum(float(x['adet']) * float(x['maliyet']) for x in st.session_state.portfoy)
    t_g = sum(float(x['adet']) * float(x['guncel']) for x in st.session_state.portfoy)
    m1.metric("Toplam Sermaye", f"{t_m:,.2f} ₺")
    m2.metric("Portföy Değeri", f"{t_g:,.2f} ₺", delta=f"{t_g - t_m:,.2f} ₺")
