import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import io
import re

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Studio Pricing Dashboard", layout="wide")

# --- 2. FUNGSI AI ---
def get_ai_response(prompt):
    try:
        # Mengambil key dari Streamlit Secrets
        api_key = st.secrets["GEMINI_KEYS"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)}"

# --- 3. INISIALISASI STATE ---
if 'costs' not in st.session_state:
    st.session_state.costs = []
if 'ai_res' not in st.session_state:
    st.session_state.ai_res = ""

# Variabel default agar tidak NameError
prod_name = ""

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("### 🌸 Strategic Assistance")
    st.caption("Bantu tentukan harga paling aman & menguntungkan.")
    st.markdown("---")
    
    st.markdown("#### 1️⃣ Produk")
    intent_type = st.selectbox("Kategori:", ["Koleksi Fashion", "Produk Beauty", "Food & Beverage", "Custom Project"])
    prod_name = st.text_input("Nama Produk:", placeholder="e.g. Linen Dress")
    
    st.markdown("---")
    st.markdown("#### 🤖 AI Analysis")
    
    if prod_name:
        if st.button("✨ Dapatkan Saran AI"):
            with st.spinner("Sedang menghitung..."):
                prompt = f"Berapa estimasi biaya produksi {prod_name} untuk bisnis {intent_type}? Berikan angka dalam format Rp... untuk Bahan Utama, Bahan Pendukung, Packaging, dan Ongkos Kerja."
                st.session_state.ai_res = get_ai_response(prompt)
        
        if st.session_state.ai_res:
            st.info(st.session_state.ai_res)
            
            if st.button("🪄 Gunakan sebagai Rincian Biaya"):
                # Mencari angka dalam teks AI
                raw_text = st.session_state.ai_res.replace('.', '').replace(',', '')
                angka = re.findall(r'\d+', raw_text)
                prices = [int(a) for a in angka if int(a) > 500] # Ambil angka yang masuk akal sebagai harga
                
                st.session_state.costs = [
                    {"item": "Bahan Utama (AI)", "price": prices[0] if len(prices) > 0 else 0, "qty": 1},
                    {"item": "Bahan Pendukung (AI)", "price": prices[1] if len(prices) > 1 else 0, "qty": 1},
                    {"item": "Packaging (AI)", "price": prices[2] if len(prices) > 2 else 0, "qty": 1},
                    {"item": "Ongkos Kerja (AI)", "price": prices[3] if len(prices) > 3 else 0, "qty": 1}
                ]
                st.rerun()

    st.markdown("---")
    st.markdown("#### 📥 Import Excel")
    up_file = st.file_uploader("Upload File Biaya", type=["xlsx"])
    if up_file:
        df_up = pd.read_excel(up_file)
        st.session_state.costs = [{"item": str(r[0]), "price": int(r[1]), "qty": 1} for _, r in df_up.iterrows()]
        st.rerun()

# --- 5. MAIN CONTENT ---
st.markdown(f"## {prod_name if prod_name else 'Pricing Planner'} ☁️")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Step 1: Rincian Biaya Produksi")
    # Tabel Input Biaya
    edited_costs = st.data_editor(
        st.session_state.costs,
        num_rows="dynamic",
        column_config={
            "item": "Nama Komponen",
            "price": st.column_config.NumberColumn("Harga Satuan (Rp)", format="Rp %d"),
            "qty": "Jumlah"
        },
        key="cost_editor"
    )
    st.session_state.costs = edited_costs

    # Fitur Download ke Excel
    if st.session_state.costs:
        df_export = pd.DataFrame(st.session_state.costs)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False)
        
        st.download_button(
            label="📥 Download Data Biaya ke Excel",
            data=buffer.getvalue(),
            file_name=f"Rincian_Biaya_{prod_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Kalkulasi Total
total_hpp = sum(item['price'] * item['qty'] for item in st.session_state.costs if item['price'])

with col2:
    st.markdown("### Step 2: Analisis Harga")
    st.metric("Total HPP per Pcs", f"Rp {total_hpp:,}")
    
    target_margin = st.slider("Target Margin Keuntungan (%)", 10, 80, 30)
    suggested_price = total_hpp / (1 - (target_margin / 100)) if total_hpp > 0 else 0
    
    st.success(f"Saran Harga Jual: **Rp {suggested_price:,.0f}**")

# --- 6. GRAFIK ---
if total_hpp > 0:
    st.markdown("---")
    st.markdown("### Step 3: Visualisasi Struktur Biaya")
    df_chart = pd.DataFrame(st.session_state.costs)
    fig = px.pie(df_chart, values='price', names='item', hole=0.4, color_discrete_sequence=px.colors.sequential.RdPu)
    st.plotly_chart(fig, use_container_width=True)