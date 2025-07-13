import streamlit as st
import pandas as pd
from utils import db_functions as db
from datetime import datetime

def show_buku_kas_umum():
    st.subheader("Laporan Buku Kas Umum")
    
    # Filter Laporan dibungkus dalam container
    with st.container(border=True):
        st.write("**Filter Laporan**")
        with st.spinner("Memuat data filter..."):
            conn = db.create_connection()
            list_pos = db.get_semua_pos_pembayaran(conn)
            conn.close()
        
        pos_dict = {nama: id_pos for id_pos, nama, _ in list_pos}
        pilihan_pos = ["Semua"] + list(pos_dict.keys())
        
        col1, col2, col3 = st.columns(3)
        tgl_mulai = col1.date_input("Tanggal Mulai", value=datetime.now().date())
        tgl_sampai = col2.date_input("Tanggal Sampai", value=datetime.now().date())
        selected_pos_nama = col3.selectbox("Filter Jenis POS", options=pilihan_pos)
        
        if st.button("Tampilkan Laporan", type="primary", use_container_width=True):
            st.session_state.run_report = True
            st.session_state.report_params = (tgl_mulai, tgl_sampai, selected_pos_nama)

    if st.session_state.get('run_report', False):
        tgl_mulai, tgl_sampai, selected_pos_nama = st.session_state.report_params
        
        id_pos_filter = None
        if selected_pos_nama != "Semua":
            id_pos_filter = pos_dict[selected_pos_nama]
            
        with st.spinner("Membuat laporan..."):
            conn = db.create_connection()
            laporan_data = db.get_laporan_kas_umum(conn, tgl_mulai, tgl_sampai, id_pos=id_pos_filter)
            conn.close()
        
        if not laporan_data:
            st.warning("Tidak ada data transaksi pada periode atau filter yang dipilih.")
        else:
            df = pd.DataFrame(laporan_data, columns=['No. Bukti', 'Tanggal', 'Jenis POS', 'Uraian', 'Penerimaan (Rp)'])
            
            # Formatting dan kalkulasi
            df['Pengeluaran (Rp)'] = 0 
            df['Saldo'] = df['Penerimaan (Rp)'].cumsum()
            total_pemasukan = df['Penerimaan (Rp)'].sum()
            saldo_akhir = total_pemasukan
            
            # Format kolom angka menjadi Rupiah
            for col in ['Penerimaan (Rp)', 'Pengeluaran (Rp)', 'Saldo']:
                df[col] = df[col].apply(lambda x: f"Rp {x:,.0f}")

            st.markdown("---")
            st.write(f"**Laporan Kas Umum Periode {tgl_mulai.strftime('%d-%m-%Y')} s/d {tgl_sampai.strftime('%d-%m-%Y')}**")
            st.dataframe(df[['Tanggal', 'Uraian', 'Penerimaan (Rp)', 'Pengeluaran (Rp)', 'Saldo']], use_container_width=True, hide_index=True)
            
            st.markdown("---")
            with st.container(border=True):
                st.write("**Ringkasan Laporan**")
                summary_col1, summary_col2, summary_col3 = st.columns(3)
                summary_col1.metric("Total Pemasukan", f"Rp {total_pemasukan:,.0f}")
                summary_col2.metric("Total Pengeluaran", "Rp 0")
                summary_col3.metric("SALDO AKHIR", f"Rp {saldo_akhir:,.0f}")

def show_rekap_saldo():
    st.subheader("Rekap Saldo per Jenis POS")
    
    with st.spinner("Memuat rekapitulasi saldo..."):
        conn = db.create_connection()
        rekap_data = db.get_rekap_saldo_per_pos(conn)
        conn.close()

    if not rekap_data:
        st.info("Belum ada data pembayaran yang tercatat untuk direkap.")
        return
        
    df = pd.DataFrame(rekap_data, columns=['Jenis POS', 'Saldo'])
    total_saldo = df['Saldo'].sum()
    
    # Format kolom saldo
    df['Saldo'] = df['Saldo'].apply(lambda x: f"Rp {x:,.0f}")
    
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    with st.container(border=True):
        st.metric("Total Saldo dari Semua POS", f"Rp {total_saldo:,.0f}")


def render():
    st.markdown("""
        <style>
            /* CSS Lengkap untuk UI Konsisten */
            .main, [data-testid="stAppViewContainer"] { background-color: #FFF7E8; font-family: 'Segoe UI', sans-serif; }
            body, p, li, h1, h2, h3, h4, h5, h6, label, div[data-testid="stText"] { color: #343A40; }
            .st-emotion-cache-1d8vwwt, [data-testid="stForm"], div[data-testid="stExpander"], .st-container[border="true"] {
                background-color: rgba(0, 0, 0, 0.7) !important;
                border: 1px solid #495057 !important; border-radius: 12px !important;
                padding: 1.5rem !important; box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            }
            .st-emotion-cache-1d8vwwt:hover { border-color: #007BFF !important; transform: translateY(-5px); }
            
            /* Penyesuaian Warna Teks di Dalam Kotak Gelap */
            .st-emotion-cache-1d8vwwt h5, [data-testid="stForm"] h6, div[data-testid="stExpander"] summary, 
            [data-testid="stForm"] label, .st-container[border="true"] div[data-testid="stText"], 
            [data-testid="stMetricLabel"] > div,
            div[data-testid="stMetricValue"] /* <-- UPDATE: Menambahkan selector untuk nilai metric */ {
                color: #FFFFFF !important;
                font-weight: 600;
            }

            .st-emotion-cache-1d8vwwt h5::before { content: ''; position: absolute; left: 0; top: 50%; transform: translateY(-50%); width: 8px; height: 100%; background-color: #007BFF; border-radius: 4px; }
            .st-emotion-cache-1d8vwwt h5 { position: relative; padding-left: 20px; }
            .st-emotion-cache-1d8vwwt p, div[data-testid="stExpander"] p, div[data-testid="stExpander"] li { color: #E0E0E0 !important; }
            .st-emotion-cache-1d8vwwt p { flex-grow: 1; }
            [data-testid="stForm"] input, [data-testid="stForm"] textarea, [data-testid="stForm"] .stSelectbox > div, .st-container[border="true"] .stSelectbox > div, [data-testid="stDateInput"] input {
                color: #495057 !important; background-color: #FFFFFF !important;
            }
            .stButton > button, [data-testid="stDownloadButton"] > button, [data-testid="stForm"] button { background-color: #007BFF !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; }
            .stButton > button:hover, [data-testid="stDownloadButton"] > button:hover, [data-testid="stForm"] button:hover { background-color: #0056b3 !important; }
            
            /* Penyesuaian Warna Tabel */
            table { border-collapse: collapse; width: 100%; }
            th { background-color: #343A40; color: #FFFFFF; border: 1px solid #495057; }
            td { background-color: #FFFFFF; color: #343A40; border: 1px solid #dee2e6; }
        </style>
        """, unsafe_allow_html=True)
    
    st.title("📚 Modul Buku Kas")

    if 'buku_kas_view' not in st.session_state:
        st.session_state.buku_kas_view = 'menu'

    if st.session_state.buku_kas_view != 'menu':
        if st.button("⬅️ Kembali ke Menu Buku Kas"):
            st.session_state.buku_kas_view = 'menu'
            # Hapus state laporan agar tidak otomatis jalan lagi
            if 'run_report' in st.session_state:
                del st.session_state['run_report']
            st.rerun()
        st.markdown("---")

    if st.session_state.buku_kas_view == 'menu':
        st.markdown("---")
        menu_options = {
            'buku_kas_umum': {"label": "Buku Kas Umum", "desc": "Lihat laporan pemasukan harian dengan filter tanggal dan jenis POS."},
            'rekap_saldo': {"label": "Rekap Saldo per POS", "desc": "Lihat rekapitulasi total saldo dari semua jenis pembayaran."}
        }
        items = list(menu_options.items())
        cols = st.columns(len(items))
        for i, (view, content) in enumerate(items):
            with cols[i]:
                container = st.container(border=True)
                container.markdown(f"<h5>{content['label']}</h5>", unsafe_allow_html=True)
                container.markdown(f"<p>{content['desc']}</p>", unsafe_allow_html=True)
                if container.button("Pilih Menu", key=f"btn_bukukas_{view}", use_container_width=True):
                    st.session_state.buku_kas_view = view
                    st.rerun()
        st.markdown("---")
        if st.button("⬅️ Kembali ke Menu Utama"):
            st.session_state.page = 'home'
            if 'page' in st.query_params:
                st.query_params.clear()
            st.rerun()
    
    elif st.session_state.buku_kas_view == 'buku_kas_umum':
        show_buku_kas_umum()
    elif st.session_state.buku_kas_view == 'rekap_saldo':
        show_rekap_saldo()