import streamlit as st
import pandas as pd
import yfinance as yf
import json
from datetime import datetime, timedelta

# --- AYARLAR ---
st.set_page_config(page_title="Zenith Pro: Final Çözüm", layout="wide")

# --- BELLEK BAŞLATMA ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- FON EKLEME FONKSİYONU ---
def add_to_portfolio(k, t, a, m, g):
    # Geçmiş kurları çek
    d_s = t.strftime('%Y-%m-%d')
    u = yf.download("USDTRY=X", start=d_s, end=(t + timedelta(days=5)).strftime('%Y-%m-%d'), progress=False)
    u_old = float(u['Close'].iloc[0]) if not u.empty else 1.0
    
    new_data = {
        "kod": k, "tarih": t, "adet": a, "maliyet": m, "guncel": g, "usd_old": u_old
    }
    st.session_state.portfolio.append(new_data)

# --- SIDEBAR: YÜKLE / İNDİR ---
st.sidebar.header("DOSYA İŞLEMLERİ")
up = st.sidebar.file_uploader("Yedek JSON Yükle", type=['json'])
if up:
    try:
        data = json.load(up)
        for i in data: 
            if isinstance(i['tarih'], str): i['tarih'] = datetime.strptime(i['tarih'], '%Y-%m-%d').date()
        st.session_state.portfolio = data
        st.sidebar.success("Yüklendi!")
    except: pass

if st.session_state.portfolio:
    save = []
    for i in st.session_state.portfolio:
        tmp = i.copy()
        tmp['tarih'] = tmp['tarih'].strftime('%Y-%m-%d') if hasattr(tmp['tarih'], 'strftime') else tmp['tarih']
        save.append(tmp)
    st.sidebar.download_button("İndir", json.dumps(save), "yedek.json")

# --- ANA EKRAN: GİRİŞ ALANLARI ---
st.title("🛡️ Zenith Pro: Kesin Kayıt")

# HİÇBİR SÜTUN VEYA FORM KULLANMADAN, ALT ALTA EN GÜVENLİ GİRİŞ
st.warning("Aşağıdaki tüm kutuları doldurup 'KAYDET' butonuna basın.")

kod_input = st.text_input("1. FON KODU (Örn: TCD, USDTRY=X, BTC-USD)").upper()
tar_input = st.date_input("2. ALIŞ TARİHİ", value=datetime.now() - timedelta(days=30))
adet_input = st.number_input("3. ADET (Miktar)", value=0.0, format="%.4f")
alis_input = st.number_input("4. BİRİM ALIŞ FİYATI (TL)", value=0.0, format="%.4f")
gun_input = st.number_input("5. BİRİM GÜNCEL FİYAT (TL)", value=0.0, format="%.4f")

if st.button("✅ PORTFÖYE KAYDET"):
    if kod_input and adet_input > 0:
        add_to_portfolio(kod_input, tar_input, adet_input, alis_input, gun_input)
        st.success(f"{kod_input} eklendi! Sayfa yenileniyor...")
        st.rerun()
    else:
        st.error("Kod ve Adet boş olamaz!")

st.divider()

# --- TABLO ---
if st.session_state.portfolio:
    st.subheader("📊 Mevcut Kayıtlar")
    
    # Mevcut verileri tabloya dönüştür
    u_now = yf.download("USDTRY=X", period="1d", progress=False)['Close'].iloc[-1]
    
    rows = []
    for i, item in enumerate(st.session_state.portfolio):
        m_toplam = item['adet'] * item['maliyet']
        g_toplam = item['adet'] * item['guncel']
        
        rows.append({
            "Kod": item['kod'],
            "Adet": item['adet'],
            "Maliyet (₺)": m_toplam,
            "Güncel (₺)": g_toplam,
            "K/Z (₺)": g_toplam - m_toplam,
            "Dolar Farkı ($)": (g_toplam / u_now) - (m_toplam / item['usd_old'])
        })
        
        # SİLME BUTONU (Her satırın altına küçük bir buton)
        if st.button(f"🗑️ {item['kod']} Sil", key=f"del_{i}"):
            st.session_state.portfolio.pop(i)
            st.rerun()
            
    st.table(pd.DataFrame(rows)) # En basit tablo formatı

else:
    st.info("Kayıt bulunamadı. Lütfen yukarıdan fon ekleyin.")
