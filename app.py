import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import random
import google.generativeai as genai
from datetime import datetime

# --- 1. CORE SETTINGS (Dipindah ke atas & diubah ke collapsed) ---
st.set_page_config(
    page_title="Studio Pricing Dashboard", 
    layout="wide", 
    initial_sidebar_state="collapsed" # Sekarang tidak akan nutupin layar lagi
)

# --- 2. CONFIG & MODELS ---
try:
    DAFTAR_KUNCI = st.secrets["GEMINI_KEYS"]
    st.sidebar.success(f"Berhasil memuat {len(DAFTAR_KUNCI)} kunci!")
except:
    st.sidebar.error("Brankas Secrets kosong!")
    DAFTAR_KUNCI = ["KUNCI_CADANGAN_DISINI"]

def get_ai_response(prompt):
    kunci = random.choice(DAFTAR_KUNCI)
    genai.configure(api_key=kunci)
    
    available_models = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
    except:
        available_models = ['models/gemini-1.5-flash', 'models/gemini-pro']

    for m_name in available_models:
        if 'gemini' in m_name:
            try:
                model = genai.GenerativeModel(model_name=m_name)
                response = model.generate_content(
                    prompt,
                    safety_settings=[
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                    ]
                )
                if response and response.text:
                    return response.text
            except Exception:
                continue
    return "⚠️ Semua model gagal merespon. Cek apakah API Key di 'Secrets' sudah benar."

# --- 3. THEME & STYLING ---
def apply_styling():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    * { font-family: 'Plus Jakarta Sans', sans-serif; color: #4A4A4A; }
    .stApp { background-color: #FDFBFA; }

    /* PERBAIKAN SIDEBAR: Biar rapat saat ditutup */
    [data-testid="stSidebar"] { 
        background-color: #FFF0F3 !important; 
        border-right: 1px solid #FFD1DC; 
    }
    
    [data-testid="stSidebarNav"] { background-color: transparent !important; }

    .p-card { 
        background: white; 
        padding: 25px; 
        border-radius: 20px; 
        border: 1px solid #F3E5E9; 
        box-shadow: 0 8px 24px rgba(208, 140, 159, 0.06); 
        margin-bottom: 25px; 
    }
    
    .stButton>button { 
        border-radius: 14px !important; 
        font-weight: 600 !important; 
        width: 100%; 
    }
    </style>
    """, unsafe_allow_html=True)

apply_styling()

# --- 4. DATA ENGINE ---
if 'costs' not in st.session_state:
    st.session_state.costs = [{"item": "Bahan Utama", "price": 0, "qty": 1}]

def add_row(): st.session_state.costs.append({"item": "", "price": 0, "qty": 1})

# --- 5. PERSISTENT SIDEBAR ---
with st.sidebar:
    st.markdown("### 🌸 Strategic Assistance")
    st.caption("Bantu tentukan harga paling aman & menguntungkan untuk produkmu.")
    
    st.markdown("---")
    st.markdown("#### 1️⃣ Mau Buat Apa Hari Ini?")
    intent_type = st.selectbox("Tujuan:", ["Koleksi Fashion", "Produk Beauty", "Food & Beverage", "Custom Project"])
    prod_name = st.text_input("Nama Produk:", placeholder="e.g. Linen Dress Summer")
    
    st.markdown("---")
    st.markdown("#### 🤖 AI Analysis - Material Suggestion")
    
    if prod_name:
        if st.button("✨ Dapatkan Saran AI"):
            with st.spinner("AI sedang berpikir..."):
                prompt = f"Berikan saran singkat bahan/komponen untuk {prod_name} dalam kategori {intent_type}. Maksimal 3 poin utama dan 1 tips biaya. Bahasa santun."
                st.session_state.ai_res = get_ai_response(prompt)
        
        if 'ai_res' in st.session_state:
            st.markdown(f"""<div class="ai-card" style="background: white; border: 1px solid #FFD1DC; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                <div style="color:#D08C9F; font-weight:700; font-size:12px; margin-bottom:8px;">✨ Rekomendasi AI ({intent_type})</div>
                <div style="font-size:11px; color:#666; line-height:1.5;">{st.session_state.ai_res}</div>
            </div>""", unsafe_allow_html=True)
            
            if st.button("🪄 Gunakan sebagai Rincian Biaya"):
                st.session_state.costs = [
                    {"item": "Bahan Utama Premium", "price": 0, "qty": 1},
                    {"item": "Packaging & Label", "price": 0, "qty": 1},
                    {"item": "Ongkos Produksi", "price": 0, "qty": 1}
                ]
                st.rerun()
    else:
        st.caption("Isi nama produk untuk rekomendasi bahan ✨")

    st.markdown("---")
    st.markdown("#### 📥 Import Excel")
    up_file = st.file_uploader("Upload XLSX", type=["xlsx"])
    if up_file:
        df_up = pd.read_excel(up_file)
        st.session_state.costs = [{"item": str(r[0]), "price": int(r[1]), "qty": 1} for _, r in df_up.iterrows()]
        st.rerun()

# --- 6. MAIN CONTENT ---
st.markdown(f"## {prod_name if prod_name else 'Pricing Planner'} ☁️")

# STEP 1: COST INPUT
st.markdown("### 🧮 Step 1: Cost Input")
st.markdown("<div class='p-card'>", unsafe_allow_html=True)
total_var = 0
for i, row in enumerate(st.session_state.costs):
    c1, c2, c3, c4 = st.columns([3, 2, 1, 0.5])
    with c1: st.session_state.costs[i]['item'] = st.text_input(f"Item {i}", row['item'], key=f"nm_{i}", label_visibility="collapsed")
    with c2: st.session_state.costs[i]['price'] = st.number_input(f"Prc {i}", value=int(row['price']), step=1000, key=f"pr_{i}", label_visibility="collapsed")
    with c3: st.session_state.costs[i]['qty'] = st.number_input(f"Qty {i}", value=int(row['qty']), step=1, key=f"qt_{i}", label_visibility="collapsed")
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

# STEP 2: EXPORT
st.markdown("### 📤 Step 2: Export & Finalization")
st.markdown("<div class='p-card'>", unsafe_allow_html=True)
safe_p = int(round(hpp_unit * 1.25, -2))
sweet_p = int(round(hpp_unit * 1.45, -2))
prem_p = int(round(hpp_unit * 2.00, -2))

output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    pd.DataFrame(st.session_state.costs).to_excel(writer, sheet_name='Rincian Biaya', index=False)
st.download_button(label="📥 Unduh Laporan Excel", data=output.getvalue(), file_name="Pricing_Report.xlsx")
st.markdown("</div>", unsafe_allow_html=True)

# STEP 3: PRICING STRATEGY
st.markdown("### 💰 Step 3: Pricing Strategy")
sc1, sc2, sc3 = st.columns(3)
strats = [("SAFE", safe_p, "20%"), ("SWEET", sweet_p, "31%"), ("PREMIUM", prem_p, "50%")]
for i, (lbl, prc, mrg) in enumerate(strats):
    with [sc1, sc2, sc3][i]:
        st.markdown(f"""<div class="strat-box" style="background: white; border: 1px solid #F0F0F0; padding: 20px; border-radius: 15px; text-align: center;">
            <span class="kpi-label">{lbl}</span><br>
            <span class="kpi-val">Rp {prc:,.0f}</span><br>
            <span style="color:#8BA888; font-weight:700;">Margin: {mrg}</span>
        </div>""", unsafe_allow_html=True)

# STEP 4: VISUALS
st.markdown("### 📊 Step 4: Visual Insights")
st.markdown("<div class='p-card'>", unsafe_allow_html=True)
vi1, vi2 = st.columns(2)
with vi1:
    fig = go.Figure(data=[go.Bar(x=['Safe', 'Sweet', 'Premium'], y=[safe_p, sweet_p, prem_p], marker_color='#D08C9F')])
    st.plotly_chart(fig, use_container_width=True)
with vi2:
    x_b = np.linspace(0, target_qty*2, 20); y_r = sweet_p * x_b; y_c = fixed_cost + (total_var * x_b)
    fig2 = go.Figure(); fig2.add_trace(go.Scatter(x=x_b, y=y_r, name="Revenue")); fig2.add_trace(go.Scatter(x=x_b, y=y_c, name="Cost"))
    st.plotly_chart(fig2, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)