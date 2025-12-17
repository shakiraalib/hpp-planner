import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import random
import google.generativeai as genai
from datetime import datetime

# --- 1. CONFIG ---
st.set_page_config(
    page_title="Studio Pricing Dashboard", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 2. MODELS & KEYS (VERSI TAHAN BANTING) ---
def get_ai_response(prompt):
    try:
        keys = st.secrets["GEMINI_KEYS"]
        if isinstance(keys, str): keys = [keys]
    except:
        return "❌ Kunci tidak ditemukan di Secrets!"

    for kunci in keys:
        try:
            genai.configure(api_key=kunci)
            # Pakai model flash terbaru yang lebih ringan & stabil
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            response = model.generate_content(
                prompt,
                # INI PENTING: Supaya AI tidak gampang memblokir jawaban
                safety_settings={
                    "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                }
            )
            
            if response.text:
                return response.text
            else:
                return "⚠️ AI merespon tapi tidak ada teks (mungkin terfilter)."
        except Exception as e:
            # Jika error karena kunci (Invalid API Key), kita lanjut ke kunci berikutnya
            if "API_KEY_INVALID" in str(e):
                continue
            # Jika error karena limit, kita beri tahu alasannya
            return f"⚠️ Masalah teknis: {str(e)[:50]}..."
            
    return "⚠️ Semua kunci gagal. Pastikan API Key di Secrets sudah benar (copy-paste lengkap)."

# --- 3. THEME & STYLING ---
def apply_styling():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; color: #4A4A4A; }
    .stApp { background-color: #FDFBFA; }
    [data-testid="stSidebar"] { background-color: #FFF0F3 !important; border-right: 1px solid #FFD1DC; }
    .p-card { background: white; padding: 25px; border-radius: 20px; border: 1px solid #F3E5E9; box-shadow: 0 8px 24px rgba(208, 140, 159, 0.06); margin-bottom: 25px; }
    .stButton>button { border-radius: 14px !important; font-weight: 600 !important; width: 100%; }
    .kpi-label { font-size: 11px; font-weight: 700; color: #BBB; text-transform: uppercase; }
    .kpi-val { font-size: 24px; font-weight: 700; color: #D08C9F; display: block; }
    .strat-box { padding: 22px; border-radius: 18px; border: 1px solid #F0F0F0; text-align: center; height: 100%; }
    .strat-sweet { background-color: #F7F9F7; border: 2px solid #8BA888; box-shadow: 0 10px 20px rgba(139, 168, 136, 0.12); }
    
    .table-header { font-size: 12px; font-weight: 700; color: #D08C9F; margin-bottom: 8px; }
    .flower-spacer { 
        background: rgba(255, 240, 243, 0.4); padding: 8px; border-radius: 12px; 
        text-align: center; color: #D08C9F; font-size: 13px; margin-bottom: 15px; border: 1px dashed #FFD1DC;
    }
    </style>
    """, unsafe_allow_html=True)

apply_styling()

# --- 4. DATA ENGINE ---
if 'costs' not in st.session_state:
    st.session_state.costs = [{"item": "Bahan Utama", "price": 0, "qty": 1}]

def add_row(): 
    st.session_state.costs.append({"item": "", "price": 0, "qty": 1})

# --- 5. SIDEBAR (FITUR LENGKAP KEMBALI) ---
with st.sidebar:
    st.markdown("### 🌸 Strategic Assistance")
    st.caption("Bantu tentukan harga paling aman & menguntungkan.")
    st.markdown("---")
    st.markdown("#### 1️⃣ Mau Buat Apa Hari Ini?")
    intent_type = st.selectbox("Tujuan:", ["Koleksi Fashion", "Produk Beauty", "Food & Beverage", "Custom Project"])
    prod_name = st.text_input("Nama Produk:", placeholder="e.g. Linen Dress Summer")
    st.markdown("---")
    st.markdown("#### 🤖 AI Analysis - Material Suggestion")
    
    if prod_name:
        if st.button("✨ Dapatkan Saran AI"):
            with st.spinner("AI berpikir..."):
                prompt = f"Berikan saran singkat bahan untuk {prod_name} dalam kategori {intent_type}."
                st.session_state.ai_res = get_ai_response(prompt)
        
        if 'ai_res' in st.session_state:
            st.markdown(f"""<div style="background: white; border: 1px solid #D08C9F; padding: 15px; border-radius: 15px; margin-bottom: 10px;">
                <div style="color:#D08C9F; font-weight:700; font-size:12px; margin-bottom:8px;">✨ Rekomendasi AI</div>
                <div style="font-size:11px; color:#666; line-height:1.5;">{st.session_state.ai_res}</div>
            </div>""", unsafe_allow_html=True)
            
            if st.button("🪄 Gunakan sebagai Rincian Biaya"):
                st.session_state.costs = [
                    {"item": "Bahan Utama Premium", "price": 0, "qty": 1}, 
                    {"item": "Packaging & Label", "price": 0, "qty": 1}, 
                    {"item": "Ongkos Produksi", "price": 0, "qty": 1}
                ]
                st.rerun()
    
    st.markdown("---")
    st.markdown("#### 📥 Import Excel")
    up_file = st.file_uploader("Upload XLSX", type=["xlsx"])
    if up_file:
        df_up = pd.read_excel(up_file)
        st.session_state.costs = [{"item": str(r[0]), "price": int(r[1]), "qty": 1} for _, r in df_up.iterrows()]
        st.rerun()

# --- 6. MAIN CONTENT ---
st.markdown(f"## {prod_name if prod_name else 'Pricing Planner'} ☁️")

# --- STEP 1 ---
st.markdown("### 🧮 Step 1: Cost Input")
st.markdown("<div class='flower-spacer'>🌸 ✨ ☁️ Studio Pricing Mode ☁️ ✨ 🌸</div>", unsafe_allow_html=True)

st.markdown("<div class='p-card'>", unsafe_allow_html=True)
h1, h2, h3, h4 = st.columns([3, 2, 1, 0.5])
h1.markdown("<div class='table-header'>Nama Item</div>", unsafe_allow_html=True)
h2.markdown("<div class='table-header'>Harga Satuan</div>", unsafe_allow_html=True)
h3.markdown("<div class='table-header'>Qty</div>", unsafe_allow_html=True)

total_var = 0
for i, row in enumerate(st.session_state.costs):
    c1, c2, c3, c4 = st.columns([3, 2, 1, 0.5])
    with c1: st.session_state.costs[i]['item'] = st.text_input(f"n_{i}", row['item'], key=f"nm_{i}", label_visibility="collapsed")
    with c2: st.session_state.costs[i]['price'] = st.number_input(f"p_{i}", value=int(row['price']), step=1000, key=f"pr_{i}", label_visibility="collapsed")
    with c3: st.session_state.costs[i]['qty'] = st.number_input(f"q_{i}", value=int(row['qty']), step=1, key=f"qt_{i}", label_visibility="collapsed")
    with c4: 
        if st.button("✕", key=f"del_{i}"):
            st.session_state.costs.pop(i); st.rerun()
    total_var += (st.session_state.costs[i]['price'] * st.session_state.costs[i]['qty'])

st.button("➕ Tambah Baris Biaya", on_click=add_row)
st.markdown("---")
cx1, cx2 = st.columns(2)
fixed_cost = cx1.number_input("Biaya Tetap Bulanan (Rp)", value=1500000, step=50000)
target_qty = cx2.number_input("Target Produksi (Unit)", value=50, min_value=1)
hpp_unit = int(total_var + (fixed_cost / target_qty))

st.markdown(f"""<div style="display: flex; gap: 20px; margin-top:15px;">
    <div style="flex:1"><span class="kpi-label">HPP Per Unit</span><span class="kpi-val">Rp {hpp_unit:,.0f}</span></div>
    <div style="flex:1"><span class="kpi-label">Total Pengeluaran</span><span class="kpi-val" style="color:#8BA888">Rp {(hpp_unit*target_qty):,.0f}</span></div>
</div>""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# PERHITUNGAN HARGA (DITARUH DI SINI AGAR VARIABELNYA TERSEDIA UNTUK SEMUA STEP)
safe_p = int(round(hpp_unit * 1.25, -2))
sweet_p = int(round(hpp_unit * 1.45, -2))
prem_p = int(round(hpp_unit * 2.0, -2))

# --- STEP 2 ---
st.markdown("### 📤 Step 2: Export & Finalization")
st.markdown("<div class='flower-spacer'>✨ 📥 Simpan Laporan Cantikmu 📥 ✨</div>", unsafe_allow_html=True)
st.markdown("<div class='p-card'>", unsafe_allow_html=True)
output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    pd.DataFrame(st.session_state.costs).to_excel(writer, index=False)
st.download_button(label="📥 Unduh Laporan Lengkap", data=output.getvalue(), file_name=f"Pricing_{prod_name}.xlsx")
st.markdown("</div>", unsafe_allow_html=True)

# --- STEP 3 ---
st.markdown("### 💰 Step 3: Pricing Strategy")
st.markdown("<div class='flower-spacer'>🌸 Pilih Strategi Harga Terbaikmu 🌸</div>", unsafe_allow_html=True)
sc1, sc2, sc3 = st.columns(3)
strats = [
    ("SAFE", safe_p, "20%", "Harga aman tanpa rugi."), 
    ("SWEET", sweet_p, "31%", "Harga ideal & seimbang."), 
    ("PREMIUM", prem_p, "50%", "Positioning eksklusif.")
]
for i, (lbl, prc, mrg, dsc) in enumerate(strats):
    cls = "strat-sweet" if lbl == "SWEET" else ""
    with [sc1, sc2, sc3][i]:
        st.markdown(f"""<div class="strat-box {cls}">
            <span class="kpi-label">{lbl}</span>
            <span class="kpi-val">Rp {prc:,.0f}</span>
            <div style="color:#8BA888; font-weight:700;">Margin: {mrg}</div>
            <div style="font-size:11px; color:#999; margin-top:8px;">{dsc}</div>
        </div>""", unsafe_allow_html=True)

# --- STEP 4 ---
st.markdown("### 📊 Step 4: Visual Insights")
st.markdown("<div class='flower-spacer'>✨ Analisis Grafik Produksi ✨</div>", unsafe_allow_html=True)
st.markdown("<div class='p-card'>", unsafe_allow_html=True)
vi1, vi2 = st.columns(2)
with vi1:
    fig = go.Figure(data=[go.Bar(
        x=['Safe', 'Sweet', 'Premium'], 
        y=[safe_p, sweet_p, prem_p], 
        marker_color='#D08C9F', 
        text=[f"Rp {x:,.0f}" for x in [safe_p, sweet_p, prem_p]], 
        textposition='auto'
    )])
    fig.update_layout(title="Proyeksi Harga Jual", height=350, plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)
with vi2:
    x_b = np.linspace(0, target_qty*2, 20)
    y_r = sweet_p * x_b
    y_c = fixed_cost + (total_var * x_b)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=x_b, y=y_r, name="Revenue", line=dict(color='#8BA888', width=3)))
    fig2.add_trace(go.Scatter(x=x_b, y=y_c, name="Cost", line=dict(color='#D08C9F', width=2)))
    fig2.update_layout(title="Analisis BEP", height=350, plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig2, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)