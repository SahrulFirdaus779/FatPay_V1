# info.py

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from utils import db_functions as db

# ======================================================================================
# CSS KUSTOM UNTUK HALAMAN INFO & DASHBOARD
# ======================================================================================
def inject_custom_css():
    st.markdown("""
        <style>
            /* Latar belakang utama */
            .main, [data-testid="stAppViewContainer"] {
                background-color: #FFF7E8;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            /* Judul Halaman */
            h1, h2, h3 {
                color: #AF640D;
                font-weight: 600;
            }
            /* Styling untuk container filter dan KPI */
            .st-emotion-cache-q8sbsg, div[data-testid="stMetric"] {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 12px;
                padding: 15px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            }
            div[data-testid="stMetric"] {
                border-left: 6px solid #007BFF;
            }
            /* Styling untuk grafik dan tabel */
            .stPlotlyChart, .stDataFrame {
                background-color: #FFFFFF;
                border-radius: 12px;
                padding: 15px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            }
            /* Tombol Cepat di Filter */
            .stButton > button {
                background-color: #007BFF !important;
                color: white !important;
                font-weight: bold;
                border-radius: 8px !important;
                border: none !important;
                padding: 0.75rem 1.5rem !important; /* Diperbesar */
                font-size: 1rem !important;       /* Diperbesar */
                width: auto !important;           /* Lebar otomatis */
                float: right;                     /* Rata kanan */
            }
        </style>
    """, unsafe_allow_html=True)

# ======================================================================================
# FUNGSI-FUNGSI DATA (dengan cache)
# ======================================================================================
@st.cache_data(ttl=300) # Cache data selama 5 menit
def get_filter_options():
    """Mengambil opsi untuk widget filter dari database."""
    conn = db.create_connection()
    try:
        angkatan_list = ["Semua Angkatan"] + db.get_semua_angkatan(conn)
        kelas_list = db.get_semua_kelas(conn)
        kelas_options = {"Semua Kelas": None}
        kelas_options.update({f"{angkatan} - {nama}": id_k for id_k, angkatan, nama, _ in kelas_list})
        return angkatan_list, kelas_options
    finally:
        conn.close()

# ======================================================================================
# FUNGSI RENDER UTAMA
# ======================================================================================
def render():
    inject_custom_css()
    st.title("ℹ️ Informasi & Dashboard")
    
    if st.button("⬅️ Kembali ke Menu Utama"):
        st.session_state.page = 'home'
        st.rerun()
    st.markdown("---")

    tab1, tab2 = st.tabs(["📊 Dashboard Interaktif", "📜 Tentang Aplikasi"])

    # --- TAB 1: DASHBOARD INTERAKTIF ---
    with tab1:
        angkatan_options, kelas_options = get_filter_options()

        with st.container(border=True):
            st.subheader("⚙️ Panel Filter Interaktif")
            
            # Inisialisasi state untuk filter
            if 'start_date' not in st.session_state:
                st.session_state.start_date = datetime.now().date().replace(day=1)
            if 'end_date' not in st.session_state:
                st.session_state.end_date = datetime.now().date()
            
            c1, c2, c3, c4 = st.columns([1, 1, 2, 3])
            st.session_state.start_date = c1.date_input("🗓️ Tanggal Mulai", st.session_state.start_date)
            st.session_state.end_date = c2.date_input("🗓️ Tanggal Akhir", st.session_state.end_date)
            
            with c4:
                btn_cols = st.columns(2)
                if btn_cols[0].button("Bulan Ini", use_container_width=True):
                    today = datetime.now().date()
                    st.session_state.start_date = today.replace(day=1)
                    st.session_state.end_date = today
                    st.rerun()
                if btn_cols[1].button("30 Hari Terakhir", use_container_width=True):
                    st.session_state.start_date = datetime.now().date() - timedelta(days=29)
                    st.session_state.end_date = datetime.now().date()
                    st.rerun()

            c5, c6 = st.columns(2)
            selected_angkatan = c5.selectbox("🎓 Filter Angkatan", options=angkatan_options)
            
            if selected_angkatan != "Semua Angkatan":
                filtered_kelas = {k: v for k, v in kelas_options.items() if selected_angkatan in k or k == "Semua Kelas"}
            else:
                filtered_kelas = kelas_options
                
            selected_kelas_nama = c6.selectbox("🏫 Filter Kelas", options=filtered_kelas.keys())

        # Konversi filter untuk dikirim ke fungsi DB
        angkatan_filter = selected_angkatan if selected_angkatan != "Semua Angkatan" else None
        kelas_id_filter = filtered_kelas.get(selected_kelas_nama)
        start_date_str = st.session_state.start_date.strftime('%Y-%m-%d')
        end_date_str = st.session_state.end_date.strftime('%Y-%m-%d')

        # Memuat dan menampilkan data sesuai filter
        conn = db.create_connection()
        try:
            kpi_data = db.get_kpi_data(conn, start_date_str, end_date_str, angkatan_filter, kelas_id_filter)
            st.markdown("---")
            kpi_cols = st.columns(3)
            kpi_cols[0].metric("Pendapatan (Periode Terpilih)", f"Rp {kpi_data['total_pendapatan']:,.0f}")
            kpi_cols[1].metric("Total Tunggakan (Filter)", f"Rp {kpi_data['total_tunggakan']:,.0f}")
            kpi_cols[2].metric("Siswa Aktif (Filter)", f"{kpi_data['total_siswa_aktif']} Siswa")

            st.markdown("---")

            chart_cols = st.columns(2, gap="large")
            with chart_cols[0]:
                st.subheader("📈 Tren Pendapatan")
                trend_data = db.get_revenue_trend(conn, start_date_str, end_date_str, angkatan_filter, kelas_id_filter)
                if trend_data:
                    df_trend = pd.DataFrame(trend_data, columns=['Periode', 'Pendapatan'])
                    fig_trend = px.area(df_trend, x='Periode', y='Pendapatan', markers=True)
                    st.plotly_chart(fig_trend, use_container_width=True)
                else:
                    st.info("Tidak ada data pendapatan pada periode/filter ini.")

            with chart_cols[1]:
                st.subheader("💰 Pendapatan per Jenis POS")
                pos_data = db.get_revenue_by_pos(conn, start_date_str, end_date_str, angkatan_filter, kelas_id_filter)
                if pos_data:
                    df_pos = pd.DataFrame(pos_data, columns=['Jenis POS', 'Pendapatan'])
                    fig_pos = px.pie(df_pos, names='Jenis POS', values='Pendapatan', hole=0.4)
                    fig_pos.update_traces(textposition='inside', textinfo='percent+label')
                    fig_pos.update_layout(showlegend=False)
                    st.plotly_chart(fig_pos, use_container_width=True)
                else:
                    st.info("Tidak ada data pendapatan pada periode/filter ini.")
        finally:
            conn.close()

    # --- TAB 2: INFORMASI APLIKASI ---
    with tab2:
        with st.container(border=True):
            st.subheader("Tentang FatPay")
            st.write(
                """
                **FatPay** adalah aplikasi pembayaran sekolah digital yang dirancang khusus untuk 
                memudahkan manajemen keuangan di **Pondok Pesantren Fathan Mubina**.
                """
            )
            st.write("**Versi:** 1.0.0")
            st.write("**Pengembang:** Dibuat dengan bantuan Gemini")
        
        with st.container(border=True):
            st.subheader("Petunjuk Singkat Modul")
            st.info(
                """
                - **Data Siswa**: Mengelola semua data siswa dan kelas.
                - **Pembayaran**: Modul utama untuk membuat tagihan dan memproses transaksi.
                - **Laporan & Buku Kas**: Berisi laporan keuangan detail.
                - **Admin**: Halaman khusus admin untuk mengelola pengguna dan sistem.
                - **Info**: Halaman ini, berisi dashboard interaktif dan info aplikasi.
                """
            )
        
        with st.container(border=True):
            st.subheader("Bantuan atau Kontak")
            st.warning("Jika mengalami kendala teknis, silakan hubungi administrator.")