import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px  # <--- TAMBAHKAN BARIS INI
import io
import random
import google.generativeai as genai
import re

# --- 1. CONFIG ---
st.set_page_config(
    page_title="Studio Pricing Dashboard", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. MODELS & KEYS ---
def get_ai_response(prompt):
    try:
        keys = st.secrets["GEMINI_KEYS"]
        if isinstance(keys, str): keys = [keys]
    except:
        return "❌ Kunci tidak ditemukan di Secrets!"

    kunci = random.choice(keys)
    
    try:
        genai.configure(api_key=kunci)
        available_models = [m.name for m in genai.list_models() 
                           if 'generateContent' in m.supported_generation_methods]
        
        model_to_use = 'models/gemini-1.5-flash'
        if model_to_use not in available_models:
            gemini_models = [m for m in available_models if 'gemini' in m]
            model_to_use = gemini_models[0] if gemini_models else available_models[0]
        
        model = genai.GenerativeModel(model_name=model_to_use)
        response = model.generate_content(
            prompt,
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )
        return response.text if response and response.text else "⚠️ AI tidak memberikan jawaban."
    except Exception as e:
        return f"⚠️ Masalah teknis: {str(e)}"

# --- 3. THEME & STYLING ---
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

# --- 4. DATA ENGINE & STATE ---
if 'costs' not in st.session_state:
    st.session_state.costs = [{"item": "Bahan Utama", "price": 0, "qty": 1}]

def add_row(): 
    st.session_state.costs.append({"item": "", "price": 0, "qty": 1})

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("### 🌸 Strategic Assistance")
    st.caption("Bantu tentukan harga paling aman & menguntungkan.")
    st.markdown("---")
    
    st.markdown("#### 1️⃣ Mau Buat Apa Hari Ini?")
    intent_type = st.selectbox("Tujuan:", ["Koleksi Fashion", "Produk Beauty", "Food & Beverage", "Custom Project"])
    prod_name = st.text_input("Nama Produk:", placeholder="e.g. Linen Dress Summer")
    
    st.markdown("---")
    st.markdown("#### 🤖 AI Analysis")
    
    if prod_name:
        if st.button("✨ Dapatkan Saran AI"):
            with st.spinner("Sedang menghitung..."):
                prompt = f"Berapa estimasi biaya produksi {prod_name}? Sebutkan dalam format: 1. Bahan Utama: Rp... 2. Bahan Pendukung: Rp... 3. Packaging: Rp... 4. Ongkos Kerja: Rp..."
                st.session_state.ai_res = get_ai_response(prompt)
                st.rerun()

        if 'ai_res' in st.session_state:
            st.info(st.session_state.ai_res)
            if st.button("🪄 Gunakan sebagai Rincian Biaya"):
                clean_text = st.session_state.ai_res.replace('.', '').replace(',', '').replace('Rp', '')
                angka = re.findall(r'\d+', clean_text)
                prices = [int(a) for a in angka if int(a) > 500]
                
                st.session_state.costs = [
                    {"item": "Bahan Utama (AI)", "price": prices[0] if len(prices) > 0 else 0, "qty": 1},
                    {"item": "Bahan Pendukung (AI)", "price": prices[1] if len(prices) > 1 else 0, "qty": 1},
                    {"item": "Packaging (AI)", "price": prices[2] if len(prices) > 2 else 0, "qty": 1},
                    {"item": "Ongkos Kerja (AI)", "price": prices[3] if len(prices) > 3 else 0, "qty": 1}
                ]
                st.success("Tabel biaya berhasil diisi!")
                st.rerun()

    st.markdown("---")
    st.markdown("#### 📥 Import Excel")
    up_file = st.file_uploader("Upload XLSX", type=["xlsx"])
    if up_file:
        @st.cache_data(show_spinner=False)
        def load_excel(file):
            return pd.read_excel(file)
        try:
            df_up = load_excel(up_file)
            st.session_state.costs = [{"item": str(r[0]), "price": int(r[1]), "qty": 1} for _, r in df_up.iterrows()]
            st.success("Data Excel berhasil dimuat!")
        except Exception as e:
            st.error(f"Gagal membaca Excel: {e}")

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
to_delete = None
for i, row in enumerate(st.session_state.costs):
    c1, c2, c3, c4 = st.columns([3, 2, 1, 0.5])
    with c1: st.session_state.costs[i]['item'] = st.text_input(f"n_{i}", row['item'], key=f"nm_{i}", label_visibility="collapsed")
    with c2: st.session_state.costs[i]['price'] = st.number_input(f"p_{i}", value=int(row['price']), step=1000, key=f"pr_{i}", label_visibility="collapsed")
    with c3: st.session_state.costs[i]['qty'] = st.number_input(f"q_{i}", value=int(row['qty']), step=1, key=f"qt_{i}", label_visibility="collapsed")
    with c4: 
        if st.button("✕", key=f"del_{i}"):
            to_delete = i
    total_var += (st.session_state.costs[i]['price'] * st.session_state.costs[i]['qty'])

if to_delete is not None:
    st.session_state.costs.pop(to_delete)
    st.rerun()

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

# HARGA STRATEGI
safe_p, sweet_p, prem_p = int(round(hpp_unit * 1.25, -2)), int(round(hpp_unit * 1.45, -2)), int(round(hpp_unit * 2.0, -2))

# --- STEP 2 ---
st.markdown("### 📤 Step 2: Export & Finalization")
st.markdown("<div class='p-card'>", unsafe_allow_html=True)
output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    pd.DataFrame(st.session_state.costs).to_excel(writer, index=False)
st.download_button(label="📥 Unduh Laporan Lengkap", data=output.getvalue(), file_name=f"Pricing_{prod_name}.xlsx")
st.markdown("</div>", unsafe_allow_html=True)

# --- STEP 3: Pricing Strategy ---
st.markdown("### 💰 Step 3: Pricing Strategy")
st.markdown("<div class='flower-spacer'>🌸 Pilih Strategi Harga 🌸</div>", unsafe_allow_html=True)

# 1. Pilihan Strategi
selected_strat = st.radio(
    "Pilih strategi untuk visualisasi BEP:",
    ["SAFE (Margin 20%)", "SWEET (Margin 31%)", "PREMIUM (Margin 50%)"],
    horizontal=True
)

# 2. Definisi final_p agar tidak NameError di Step 4
if "SAFE" in selected_strat:
    final_p = safe_p
elif "SWEET" in selected_strat:
    final_p = sweet_p
else:
    final_p = prem_p

# Tampilan Kartu Strategi
sc1, sc2, sc3 = st.columns(3)
strats = [("SAFE", safe_p, "20%"), ("SWEET", sweet_p, "31%"), ("PREMIUM", prem_p, "50%")]
for i, (lbl, prc, mrg) in enumerate(strats):
    is_sel = lbl in selected_strat
    cls = "strat-sweet" if is_sel else ""
    with [sc1, sc2, sc3][i]:
        st.markdown(f"""<div class="strat-box {cls}">
            <span class="kpi-label">{lbl} {'✅' if is_sel else ''}</span>
            <span class="kpi-val">Rp {prc:,.0f}</span>
            <div style="color:#8BA888; font-weight:700;">Margin: {mrg}</div>
        </div>""", unsafe_allow_html=True)

# --- STEP 4: Visual Insights ---
st.markdown("### 📊 Step 4: Visual Insights")
st.markdown("<div class='p-card'>", unsafe_allow_html=True)

vcol1, vcol2 = st.columns(2)

with vcol1:
    st.markdown("#### Struktur Biaya Produksi (%)")
    # Menggunakan total biaya variabel (HPP x Target) vs Biaya Tetap
    df_pie = pd.DataFrame({
        'Kategori': ['Modal Bahan (Variabel)', 'Biaya Operasional (Tetap)'],
        'Nilai': [total_var * target_qty, fixed_cost]
    })
    fig_pie = px.pie(
        df_pie, values='Nilai', names='Kategori', hole=0.5,
        color_discrete_sequence=['#D08C9F', '#FFD1DC']
    )
    fig_pie.update_layout(height=350, margin=dict(t=30, b=0, l=0, r=0))
    st.plotly_chart(fig_pie, use_container_width=True)

with vcol2:
    st.markdown("#### Analisis Break Even Point (BEP)")
    # Logika BEP Awal: Garis Revenue vs Garis Cost
    x_bep = np.linspace(0, target_qty * 2, 20)
    y_revenue = final_p * x_bep # Mengikuti pilihan di Step 3
    y_total_cost = fixed_cost + (total_var * x_bep)
    
    fig_bep = go.Figure()
    fig_bep.add_trace(go.Scatter(x=x_bep, y=y_revenue, name="Revenue", line=dict(color='#8BA888', width=3)))
    fig_bep.add_trace(go.Scatter(x=x_bep, y=y_total_cost, name="Total Cost", line=dict(color='#D08C9F', width=2)))
    
    fig_bep.update_layout(
        height=350, 
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title="Unit Terjual",
        yaxis_title="Rupiah",
        margin=dict(t=30, b=0, l=0, r=0)
    )
    st.plotly_chart(fig_bep, use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)