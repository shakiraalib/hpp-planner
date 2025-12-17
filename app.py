import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import random
import google.generativeai as genai
from datetime import datetime

# --- 1. CONFIG (HANYA SATU & COLLAPSED) ---
st.set_page_config(
    page_title="Studio Pricing Dashboard", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 2. MODELS & KEYS ---
try:
    DAFTAR_KUNCI = st.secrets["GEMINI_KEYS"]
except:
    DAFTAR_KUNCI = ["KUNCI_CADANGAN_DISINI"]

def get_ai_response(prompt):
    kunci = random.choice(DAFTAR_KUNCI)
    genai.configure(api_key=kunci)
    try:
        model = genai.GenerativeModel(model_name='gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text if response else "⚠️ Gagal"
    except:
        return "⚠️ Error API"

# --- 3. THEME & STYLING (ASLI KAMU) ---
def apply_styling():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; color: #4A4A4A; }
    .stApp { background-color: #FDFBFA; }
    [data-testid="stSidebar"] { background-color: #FFF0F3 !important; border-right: 1px solid #FFD1DC; }
    .p-card { background: white; padding: 25px; border-radius: 20px; border: 1px solid #F3E5E9; box-shadow: 0 8px 24px rgba(208, 140, 159, 0.06); margin-bottom: 25px; }
    .kpi-label { font-size: 11px; font-weight: 700; color: #BBB; text-transform: uppercase; letter-spacing: 0.8px; }
    .kpi-val { font-size: 24px; font-weight: 700; color: #D08C9F; display: block; }
    .strat-box { padding: 22px; border-radius: 18px; border: 1px solid #F0F0F0; text-align: center; height: 100%; }
    .strat-sweet { background-color: #F7F9F7; border: 2px solid #8BA888; box-shadow: 0 10px 20px rgba(139, 168, 136, 0.12); }
    .stButton>button { border-radius: 14px !important; font-weight: 600 !important; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

apply_styling()

# --- 4. DATA ENGINE ---
if 'costs' not in st.session_state:
    st.session_state.costs = [{"item": "Bahan Utama", "price": 0, "qty": 1}]

def add_row(): st.session_state.costs.append({"item": "", "price": 0, "qty": 1})

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("### 🌸 Strategic Assistance")
    intent_type = st.selectbox("Tujuan:", ["Koleksi Fashion", "Produk Beauty", "Food & Beverage", "Custom Project"])
    prod_name = st.text_input("Nama Produk:", placeholder="e.g. Linen Dress Summer")
    
    if st.button("✨ Dapatkan Saran AI"):
        with st.spinner("Berpikir..."):
            st.session_state.ai_res = get_ai_response(f"Saran bahan untuk {prod_name}")
    
    if 'ai_res' in st.session_state:
        st.info(st.session_state.ai_res)
        if st.button("🪄 Gunakan Rincian"):
            st.session_state.costs = [{"item": "Bahan Utama", "price": 0, "qty": 1}, {"item": "Packaging", "price": 0, "qty": 1}]
            st.rerun()

    st.markdown("---")
    up_file = st.file_uploader("Upload XLSX", type=["xlsx"])
    if up_file:
        df_up = pd.read_excel(up_file)
        st.session_state.costs = [{"item": str(r[0]), "price": int(r[1]), "qty": 1} for _, r in df_up.iterrows()]
        st.rerun()

# --- 6. MAIN CONTENT ---
st.markdown(f"## {prod_name if prod_name else 'Pricing Planner'} ☁️")

# STEP 1: COST INPUT (Blok putih di bawah ini sudah dihapus)
st.markdown("### 🧮 Step 1: Cost Input")
st.markdown("<div class='p-card'>", unsafe_allow_html=True)
total_var = 0
for i, row in enumerate(st.session_state.costs):
    c1, c2, c3, c4 = st.columns([3, 2, 1, 0.5])
    with c1: st.session_state.costs[i]['item'] = st.text_input(f"Item {i}", row['item'], key=f"nm_{i}", label_visibility="collapsed")
    with c2: st.session_state.costs[i]['price'] = st.number_input(f"Prc {i}", value=int(row['price']), key=f"pr_{i}", label_visibility="collapsed")
    with c3: st.session_state.costs[i]['qty'] = st.number_input(f"Qty {i}", value=int(row['qty']), key=f"qt_{i}", label_visibility="collapsed")
    with c4: 
        if st.button("✕", key=f"del_{i}"):
            st.session_state.costs.pop(i); st.rerun()
    total_var += (st.session_state.costs[i]['price'] * st.session_state.costs[i]['qty'])

st.button("➕ Tambah Baris Biaya", on_click=add_row)
st.markdown("---")
cx1, cx2 = st.columns(2)
fixed_cost = cx1.number_input("Biaya Tetap Bulanan (Rp)", value=1500000)
target_qty = cx2.number_input("Target Produksi (Unit)", value=50, min_value=1)
hpp_unit = int(total_var + (fixed_cost / target_qty))

st.markdown(f"""<div style="display: flex; gap: 20px; margin-top:15px;">
    <div style="flex:1"><span class="kpi-label">HPP Per Unit</span><span class="kpi-val">Rp {hpp_unit:,.0f}</span></div>
    <div style="flex:1"><span class="kpi-label">Total Pengeluaran</span><span class="kpi-val" style="color:#8BA888">Rp {(hpp_unit*target_qty):,.0f}</span></div>
</div>""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# STEP 2: EXPORT (Blok putih di bawah ini sudah dihapus)
st.markdown("### 📤 Step 2: Export & Finalization")
st.markdown("<div class='p-card'>", unsafe_allow_html=True)
safe_p, sweet_p, prem_p = int(round(hpp_unit*1.25,-2)), int(round(hpp_unit*1.45,-2)), int(round(hpp_unit*2.0,-2))
output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    pd.DataFrame(st.session_state.costs).to_excel(writer, index=False)
st.download_button(label="📥 Unduh Laporan Lengkap", data=output.getvalue(), file_name="Report.xlsx")
st.markdown("</div>", unsafe_allow_html=True)

# STEP 3: STRATEGY
st.markdown("### 💰 Step 3: Pricing Strategy")
sc1, sc2, sc3 = st.columns(3)
strats = [("SAFE", safe_p, "20%", "Harga aman.", ""), ("SWEET", sweet_p, "31%", "Ideal.", "strat-sweet"), ("PREMIUM", prem_p, "50%", "Eksklusif.", "")]
for i, (lbl, prc, mrg, dsc, cls) in enumerate(strats):
    with [sc1, sc2, sc3][i]:
        st.markdown(f'<div class="strat-box {cls}"><span class="kpi-label">{lbl}</span><span class="kpi-val">Rp {prc:,.0f}</span><div style="color:#8BA888; font-weight:700;">Margin: {mrg}</div></div>', unsafe_allow_html=True)

# STEP 4: VISUALS
st.markdown("### 📊 Step 4: Visual Insights")
st.markdown("<div class='p-card'>", unsafe_allow_html=True)
v1, v2 = st.columns(2)
with v1:
    fig = go.Figure(data=[go.Bar(x=['Safe', 'Sweet', 'Premium'], y=[safe_p, sweet_p, prem_p], marker_color='#D08C9F', text=[f"Rp {x:,.0f}" for x in [safe_p, sweet_p, prem_p]], textposition='auto')])
    st.plotly_chart(fig, use_container_width=True)
with v2:
    x_b = np.linspace(0, target_qty*2, 20); y_r = sweet_p * x_b; y_c = fixed_cost + (total_var * x_b)
    fig2 = go.Figure(); fig2.add_trace(go.Scatter(x=x_b, y=y_r, name="Revenue", line=dict(color='#8BA888'))); fig2.add_trace(go.Scatter(x=x_b, y=y_c, name="Cost", line=dict(color='#D08C9F')))
    st.plotly_chart(fig2, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)