import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import random
import google.generativeai as genai
from datetime import datetime

# --- 0. CONFIG UTAMA (HANYA BOLEH ADA SATU DI PALING ATAS) ---
st.set_page_config(
    page_title="Studio Pricing Dashboard", 
    layout="wide", 
    initial_sidebar_state="collapsed" # Biar HP & Laptop rapi saat dibuka
)

# --- 1. CONFIG & MODELS ---
try:
    DAFTAR_KUNCI = st.secrets["GEMINI_KEYS"]
except:
    DAFTAR_KUNCI = []

def get_ai_response(prompt):
    if not DAFTAR_KUNCI:
        return "❌ Kunci API belum terpasang di Secrets."
    
    kunci = random.choice(DAFTAR_KUNCI)
    genai.configure(api_key=kunci)
    
    # Coba model terbaru dulu
    for m_name in ['gemini-1.5-flash', 'gemini-pro']:
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
        except:
            continue
    return "⚠️ AI sedang sibuk. Coba lagi sebentar lagi ya."

# --- 2. THEME & STYLING ---
def apply_styling():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; color: #4A4A4A; }
    .stApp { background-color: #FDFBFA; }

    /* CSS SideBar agar menutup RAPAT */
    [data-testid="stSidebar"] { 
        background-color: #FFF0F3 !important; 
        border-right: 1px solid #FFD1DC; 
    }
    
    /* Menghilangkan sisa bayangan sidebar */
    [data-testid="stSidebarNav"] { background-color: transparent !important; }

    .p-card { 
        background: white; 
        padding: 25px; 
        border-radius: 20px; 
        border: 1px solid #F3E5E9; 
        box-shadow: 0 8px 24px rgba(208, 140, 159, 0.06); 
        margin-bottom: 25px; 
    }
    .ai-card { background: #FFFFFF; border: 1.5px solid #D08C9F; border-radius: 18px; padding: 15px; margin-top: 10px; }
    .strat-box { padding: 22px; border-radius: 18px; border: 1px solid #F0F0F0; text-align: center; height: 100%; transition: 0.3s; }
    .strat-sweet { background-color: #F7F9F7; border: 2px solid #8BA888; box-shadow: 0 10px 20px rgba(139, 168, 136, 0.12); }
    .kpi-label { font-size: 11px; font-weight: 700; color: #BBB; text-transform: uppercase; letter-spacing: 0.8px; }
    .kpi-val { font-size: 24px; font-weight: 700; color: #D08C9F; display: block; }
    .stButton>button { border-radius: 14px !important; font-weight: 600 !important; width: 100%; }
    .main-cta button { background-color: #D08C9F !important; color: white !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

apply_styling()

# --- 3. DATA ENGINE ---
if 'costs' not in st.session_state:
    st.session_state.costs = [{"item": "Bahan Utama", "price": 0, "qty": 1}]

def add_row(): 
    st.session_state.costs.append({"item": "", "price": 0, "qty": 1})

# --- 4. PERSISTENT SIDEBAR ---
with st.sidebar:
    st.markdown("### 🌸 Strategic Assistance")
    st.caption("Bantu tentukan harga paling aman & menguntungkan.")
    st.markdown("---")
    intent_type = st.selectbox("Tujuan:", ["Koleksi Fashion", "Produk Beauty", "Food & Beverage", "Custom Project"])
    prod_name = st.text_input("Nama Produk:", placeholder="e.g. Linen Dress Summer")
    
    if prod_name:
        if st.button("✨ Dapatkan Saran AI"):
            with st.spinner("AI sedang berpikir..."):
                prompt = f"Berikan saran singkat bahan untuk {prod_name} dalam kategori {intent_type}. Maks 3 poin & 1 tips biaya."
                st.session_state.ai_res = get_ai_response(prompt)
        
        if 'ai_res' in st.session_state:
            st.markdown(f"""<div class="ai-card">
                <div style="color:#D08C9F; font-weight:700; font-size:12px; margin-bottom:8px;">✨ Rekomendasi AI</div>
                <div style="font-size:11px; color:#666; line-height:1.5;">{st.session_state.ai_res}</div>
            </div>""", unsafe_allow_html=True)

# --- 5. MAIN CONTENT ---
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

# STEP 2 & 3: STRATEGY & EXPORT
st.markdown("### 💰 Step 2: Pricing Strategy")
sc1, sc2, sc3 = st.columns(3)
safe_p, sweet_p, prem_p = int(round(hpp_unit*1.25, -2)), int(round(hpp_unit*1.45, -2)), int(round(hpp_unit*2.00, -2))
strats = [("SAFE", safe_p, "25%"), ("SWEET", sweet_p, "45%"), ("PREMIUM", prem_p, "100%")]

for i, (lbl, prc, mrg) in enumerate(strats):
    with [sc1, sc2, sc3][i]:
        st.markdown(f"""<div class="strat-box">
            <span class="kpi-label">{lbl}</span>
            <span class="kpi-val">Rp {prc:,.0f}</span>
            <div style="color:#8BA888; font-weight:700;">Margin: {mrg}</div>
        </div>""", unsafe_allow_html=True)

# STEP 4: VISUALS
st.markdown("### 📊 Step 3: Visual Insights")
st.markdown("<div class='p-card'>", unsafe_allow_html=True)
fig2 = go.Figure()
x_b = np.linspace(0, target_qty*2, 20)
fig2.add_trace(go.Scatter(x=x_b, y=sweet_p*x_b, name="Revenue", line=dict(color='#8BA888', width=3)))
fig2.add_trace(go.Scatter(x=x_b, y=fixed_cost+(total_var*x_b), name="Cost", line=dict(color='#D08C9F', width=2)))
fig2.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig2, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)