import streamlit as st
import pandas as pd
from utils import db_functions as db
from datetime import datetime
import base64
import io
import os
import plotly.express as px
# import plotly.io as pio # Hapus atau komen baris ini jika tidak ada lagi ekspor gambar

# Hapus import fpdf dan img2pdf
# from fpdf import FPDF
# import img2pdf

# --- Fungsi Utility untuk SVG ---
def get_svg_as_base64(filepath):
    """Membaca file SVG dan mengembalikan string Base64."""
    try:
        with open(filepath, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except FileNotFoundError:
        st.error(f"Error: File SVG tidak ditemukan di {filepath}. Pastikan path benar.")
        return "" # Mengembalikan string kosong jika file tidak ditemukan

# --- Fungsi Tampilan Laporan Buku Kas Umum ---
def show_buku_kas_umum():
    st.subheader("Laporan Buku Kas Umum")

    # Filter Laporan dibungkus dalam expander
    with st.expander("Filter Laporan Kas Umum", expanded=True):
        st.markdown("##### Opsi Filter Laporan")

        # Menggunakan st.cache_data untuk data filter yang statis
        @st.cache_data
        def get_cached_filter_data():
            conn = db.create_connection()
            pos = db.get_semua_pos_pembayaran(conn)
            angkatan = db.get_semua_angkatan(conn)
            kelas = db.get_semua_kelas(conn)
            conn.close()
            return pos, angkatan, kelas

        list_pos, list_angkatan, list_kelas = get_cached_filter_data()

        pos_dict = {nama: id_pos for id_pos, nama, _ in list_pos}
        pilihan_pos = ["Semua"] + list(pos_dict.keys())

        angkatan_dict = {angkatan: angkatan for angkatan in list_angkatan}
        pilihan_angkatan = ["Semua"] + list(angkatan_dict.keys())

        kelas_dict = {f"{nama_kelas} ({angkatan})": id_kelas for id_kelas, angkatan, nama_kelas, _ in list_kelas}
        pilihan_kelas = ["Semua"] + sorted(list(kelas_dict.keys()))

        col_date1, col_date2 = st.columns(2)
        tgl_mulai = col_date1.date_input("Tanggal Mulai", value=datetime.now().date(), help="Pilih tanggal awal periode laporan.")
        tgl_sampai = col_date2.date_input("Tanggal Sampai", value=datetime.now().date(), help="Pilih tanggal akhir periode laporan.")

        # Validasi Rentang Tanggal
        if tgl_mulai > tgl_sampai:
            st.error("Tanggal Mulai tidak boleh lebih dari Tanggal Sampai.")
            # Jangan tampilkan tombol Tampilkan Laporan jika tanggal tidak valid
            disable_button = True
        else:
            disable_button = False

        st.markdown("---") # Pemisah visual

        col_filter_data1, col_filter_data2, col_filter_data3 = st.columns(3)
        selected_pos_nama = col_filter_data1.selectbox("Jenis POS", options=pilihan_pos, help="Filter berdasarkan jenis POS pembayaran.")
        selected_angkatan = col_filter_data2.selectbox("Angkatan", options=pilihan_angkatan, help="Filter berdasarkan angkatan siswa.")
        selected_kelas_nama = col_filter_data3.selectbox("Kelas", options=pilihan_kelas, help="Filter berdasarkan kelas siswa.")

        search_term = st.text_input("Cari Siswa (Nama / NIS)", placeholder="Masukkan nama atau NIS siswa...", help="Cari siswa berdasarkan nama lengkap atau Nomor Induk Siswa.")

        st.markdown("---") # Separator for button
        # Tombol "Tampilkan Laporan"
        if st.button("Tampilkan Laporan", type="primary", use_container_width=True, disabled=disable_button):
            st.session_state.report_params = (tgl_mulai, tgl_sampai, selected_pos_nama, selected_angkatan, selected_kelas_nama, search_term)
            st.session_state.show_report_data = True # Set flag untuk menampilkan data
            st.rerun() # Rerun untuk langsung menampilkan laporan setelah klik

    # Placeholder untuk pesan laporan
    report_message_placeholder = st.empty()

    if st.session_state.get('show_report_data', False) and 'report_params' in st.session_state:
        tgl_mulai, tgl_sampai, selected_pos_nama, selected_angkatan, selected_kelas_nama, search_term = st.session_state.report_params

        id_pos_filter = None
        if selected_pos_nama != "Semua":
            id_pos_filter = pos_dict[selected_pos_nama]

        angkatan_filter = None
        if selected_angkatan != "Semua":
            angkatan_filter = selected_angkatan

        id_kelas_filter = None
        if selected_kelas_nama != "Semua":
            id_kelas_filter = kelas_dict[selected_kelas_nama]

        with st.spinner("Mempersiapkan laporan kas umum..."):
            conn = db.create_connection()
            laporan_data = db.get_laporan_kas_umum(conn, tgl_mulai, tgl_sampai, id_pos=id_pos_filter,
                                                    angkatan=angkatan_filter, kelas_id=id_kelas_filter,
                                                    search_term=search_term)
            conn.close()

        if not laporan_data:
            report_message_placeholder.warning("Tidak ada data transaksi ditemukan untuk periode dan filter yang dipilih. Coba sesuaikan rentang tanggal atau filter lainnya.")
        else:
            report_message_placeholder.empty() # Kosongkan placeholder jika ada data
            # Add 'Nama Siswa' and 'Kelas' to columns for display
            df = pd.DataFrame(laporan_data, columns=['No. Bukti', 'Tanggal', 'NIS Siswa', 'Nama Siswa', 'Angkatan', 'Kelas', 'Jenis POS', 'Uraian', 'Penerimaan (Rp)'])

            # Formatting dan kalkulasi
            # Simpan nilai numerik untuk perhitungan sebelum diformat
            df['Penerimaan (Rp) Raw'] = pd.to_numeric(df['Penerimaan (Rp)'], errors='coerce').fillna(0)
            df['Pengeluaran (Rp) Raw'] = 0 # Placeholder for now, adjust if you add expenditure tracking
            df['Saldo Raw'] = df['Penerimaan (Rp) Raw'].cumsum()

            total_pemasukan = df['Penerimaan (Rp) Raw'].sum()
            saldo_akhir = df['Saldo Raw'].iloc[-1] if not df.empty else 0

            # Format kolom angka menjadi Rupiah untuk display
            for col_name in ['Penerimaan (Rp)', 'Pengeluaran (Rp)', 'Saldo']:
                df[col_name] = df[col_name + ' Raw'].apply(lambda x: f"Rp {x:,.0f}")

            st.markdown("---")
            st.markdown(f"**Laporan Kas Umum Periode {tgl_mulai.strftime('%d %B %Y')} s/d {tgl_sampai.strftime('%d %B %Y')}**")
            st.info(f"Data terakhir diperbarui pada: {datetime.now().strftime('%d %B %Y %H:%M:%S')}")

            # Display all relevant columns for the report
            st.dataframe(
                df[['Tanggal', 'NIS Siswa', 'Nama Siswa', 'Angkatan', 'Kelas', 'Jenis POS', 'Uraian', 'Penerimaan (Rp)', 'Pengeluaran (Rp)', 'Saldo']],
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")
            with st.container(border=True):
                st.markdown("##### Ringkasan Laporan")
                summary_col1, summary_col2, summary_col3 = st.columns(3)
                summary_col1.metric("Total Pemasukan", f"Rp {total_pemasukan:,.0f}", help="Total uang masuk dari semua transaksi.")
                summary_col2.metric("Total Pengeluaran", "Rp 0", help="Total uang keluar. (Saat ini belum ada data pengeluaran)", delta_color="inverse") # Indicate it's currently zero
                summary_col3.metric("SALDO AKHIR", f"Rp {saldo_akhir:,.0f}", help="Total saldo kas pada akhir periode laporan.")

# --- Fungsi Tampilan Rekap Saldo ---
def show_rekap_saldo():
    st.subheader("Rekap Saldo per Jenis POS")
    st.markdown("Laporan ini menyajikan ringkasan saldo akumulatif untuk setiap jenis Pos Pembayaran yang tercatat dalam sistem.")

    with st.spinner("Memuat rekapitulasi saldo..."):
        conn = db.create_connection()
        rekap_data = db.get_rekap_saldo_per_pos(conn)
        conn.close()

    if not rekap_data:
        st.info("Belum ada data pembayaran yang tercatat untuk direkap. Masukkan beberapa transaksi terlebih dahulu.")
        return

    # Convert to DataFrame immediately for easier manipulation
    df_rekap = pd.DataFrame(rekap_data, columns=['Jenis POS', 'Saldo'])

    # Ensure 'Saldo' is numeric for calculations and plotting
    df_rekap['Saldo'] = pd.to_numeric(df_rekap['Saldo'], errors='coerce').fillna(0)

    total_saldo = df_rekap['Saldo'].sum()

    st.markdown("---")
    with st.container(border=True):
        st.markdown("##### Ringkasan Total Saldo")
        st.metric("Total Saldo dari Semua POS", f"Rp {total_saldo:,.0f}", help="Total akumulasi saldo dari semua jenis POS pembayaran.")

    st.markdown("---")
    st.markdown("##### Detail Saldo per Jenis POS")

    # Visualisasi Data: Bar Chart
    if not df_rekap.empty:
        # Sort data for better visualization
        df_rekap_sorted = df_rekap.sort_values(by='Saldo', ascending=False)
        
        # Create Bar Chart
        fig = px.bar(df_rekap_sorted, 
                     x='Jenis POS', 
                     y='Saldo',
                     title='Distribusi Saldo per Jenis POS',
                     labels={'Jenis POS': 'Jenis POS Pembayaran', 'Saldo': 'Saldo (Rp)'},
                     color='Saldo', # Color bars based on saldo value
                     color_continuous_scale=px.colors.sequential.Viridis, # Choose a color scale
                     text=df_rekap_sorted['Saldo'].apply(lambda x: f"Rp {x:,.0f}")) # Display formatted value on bars
        
        fig.update_layout(xaxis_title="Jenis POS",
                          yaxis_title="Saldo (Rp)",
                          title_x=0.5, # Center the title
                          plot_bgcolor='rgba(0,0,0,0)', # Transparent background for plot area
                          paper_bgcolor='rgba(0,0,0,0)', # Transparent background for entire figure
                          font_family='Poppins',
                          font_color='#333333',
                          xaxis_tickangle=-45) # Angle x-axis labels if they are long
        
        fig.update_traces(texttemplate='Rp %{y:,.0f}', textposition='outside') # Format text on bars
        fig.update_yaxes(rangemode="tozero") # Start y-axis from zero
        st.plotly_chart(fig, use_container_width=True)

    # Tampilan Tabel
    # Create a copy for display to avoid modifying the numeric 'Saldo' column needed for plotting
    df_display = df_rekap.copy()
    df_display['Saldo'] = df_display['Saldo'].apply(lambda x: f"Rp {x:,.0f}")

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # st.markdown("---") # Hapus garis pemisah jika tidak ada lagi tombol download
    # Hapus semua logika untuk tombol download CSV
    # @st.cache_data
    # def convert_df_to_csv(df):
    #    df_export = pd.DataFrame(rekap_data, columns=['Jenis POS', 'Saldo'])
    #    return df_export.to_csv(index=False).encode('utf-8')
    # csv_data = convert_df_to_csv(df_rekap)
    # st.download_button(
    #    label="📥 Unduh Data Rekap Saldo (CSV)",
    #    data=csv_data,
    #    file_name=f"rekap_saldo_per_pos_{datetime.now().strftime('%Y%m%d')}.csv",
    #    mime="text/csv",
    #    help="Unduh data rekapitulasi saldo ke format CSV."
    # )

    # Hapus juga fungsi create_rekap_saldo_pdf dan panggilannya
    # function create_rekap_saldo_pdf (dihapus)

# --- Fungsi Render Utama Modul Buku Kas (tetap sama, atau disesuaikan jika ada perubahan global) ---
def render():
    # Pastikan path ke file SVG sudah benar
    buku_kas_svg_base64 = get_svg_as_base64(os.path.join("assets", "buku_kas", "bukukas.svg"))
    rekap_saldo_svg_base64 = get_svg_as_base64(os.path.join("assets", "buku_kas", "rekap_saldo.svg"))

    # INJEKSI CSS BARU UNTUK UKURAN JUDUL DAN POSISI IKON (Sama seperti yang Anda berikan)
    st.markdown("""
        <style>
            /* Import Google Fonts for a modern look */
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

            /* Mengatur lebar container utama */
            .main .block-container {
                max-width: 900px; /* Lebar maksimum konten */
                padding-top: 2rem;
                padding-right: 1rem;
                padding-left: 1rem;
                padding-bottom: 2rem;
            }

            /* Warna background yang lebih lembut dan elegan */
            .stApp {
                background-color: #FFF7E8; /* Warna krem terang */
            }

            /* Global font dan warna teks */
            body, p, li, h1, h2, h3, h4, h5, h6, label, div[data-testid="stText"] {
                font-family: 'Poppins', sans-serif;
                color: #333333; /* Abu-abu gelap untuk teks utama */
            }

            /* Container dan Bordered Containers (cards, forms, expanders) */
            .st-emotion-cache-1d8vwwt, [data-testid="stForm"], div[data-testid="stExpander"], .st-container[border="true"] {
                background-color: #ffffff; /* Putih bersih */
                border: 1px solid #e0e0e0; /* Border abu-abu terang */
                border-radius: 12px;
                padding: 1.5rem;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05); /* Shadow lebih lembut */
                transition: all 0.2s ease-in-out; /* Transisi untuk hover */
            }
            .st-emotion-cache-1d8vwwt:hover, .st-container[border="true"]:hover {
                border-color: #007bff; /* Warna biru saat hover */
                box-shadow: 0 6px 16px rgba(0,0,0,0.1); /* Shadow lebih tebal saat hover */
                transform: translateY(-3px); /* Efek angkat sedikit */
            }

            /* Penyesuaian Warna Teks di Dalam Kotak */
            .st-emotion-cache-1d8vwwt h3,
            .st-emotion-cache-1d8vwwt h5,
            [data-testid="stForm"] h6,
            div[data-testid="stExpander"] summary,
            [data-testid="stForm"] label,
            .st-container[border="true"] div[data-testid="stText"],
            [data-testid="stMetricLabel"] > div {
                color: #495057 !important; /* Abu-abu gelap sedang */
                font-weight: 600;
            }

            /* Judul Utama Modul (di luar kartu menu) */
            h1 {
                text-align: left;
                color: #2c3e50; /* Biru kehitaman */
                margin-bottom: 1.5rem;
                font-size: 2.5rem;
                font-weight: 700;
            }
            h2 {
                color: #2c3e50;
                font-size: 2rem;
                border-bottom: 2px solid #e0e0e0;
                padding-bottom: 0.5rem;
                margin-bottom: 1.5rem;
            }
            h3 {
                color: #34495e;
                font-size: 1.6rem;
                margin-bottom: 1rem;
            }
            h4 {
                color: #555555;
                font-size: 1.3rem;
                margin-bottom: 0.8rem;
            }
            h5 {
                color: #666666;
                font-size: 1.1rem;
                margin-bottom: 0.5rem;
            }

            /* Penyesuaian Warna Nilai Metrik SALDO AKHIR */
            [data-testid="stMetric"] div[data-testid="stMetricValue"] {
                color: #28a745 !important; /* Hijau cerah */
                font-weight: bold !important;
                font-size: 2.5rem !important;
            }

            /* Untuk Total Pemasukan dan Pengeluaran di ringkasan */
            [data-testid="stMetric"]:nth-child(1) div[data-testid="stMetricValue"] {
                color: #17a2b8 !important; /* Biru muda */
                font-size: 2rem !important;
            }
            [data-testid="stMetric"]:nth-child(2) div[data-testid="stMetricValue"] {
                color: #dc3545 !important; /* Merah */
                font-size: 2rem !important;
            }
            [data-testid="stMetric"]:nth-child(3) div[data-testid="stMetricValue"] {
                color: #28a745 !important; /* Hijau (saldo akhir) */
                font-size: 2.5rem !important;
            }

            /* CSS untuk menengahkan dan memperbesar judul menu di cards */
            /* Perubahan: target h3 di dalam .menu-card dengan font-size yang lebih kecil */
            .menu-card h3 {
                text-align: center !important;
                font-size: 1.2rem !important; /* Ukuran font lebih kecil */
                margin-top: 0.5rem; /* Tambahkan sedikit margin atas */
                margin-bottom: 0.5rem;
                padding-left: 0 !important;
                color: #34495e !important;
            }

            /* Menghapus pseudo-element 'before' untuk h3 di menu */
            .menu-card h3::before {
                content: none !important;
            }

            /* CSS for the image in menu cards */
            /* Perubahan: tambahkan margin-bottom agar ada jarak ke judul */
            .menu-icon {
                display: block;
                margin: 0px auto; /* Hapus margin-top yang asli, ikon sudah di atas */
                width: 50px; /* Ukuran ikon lebih besar */
                height: 80px;
                opacity: 0.8; /* Sedikit transparan */
                transition: transform 0.2s ease-in-out;
                margin-bottom: 10px; /* Jarak antara ikon dan judul */
            }
            .st-emotion-cache-1d8vwwt:hover .menu-icon {
                transform: scale(1.1); /* Sedikit membesar saat hover */
            }

            /* Input fields (text, date, selectbox) */
            [data-testid="stForm"] input,
            [data-testid="stForm"] textarea,
            [data-testid="stForm"] .stSelectbox > div,
            .st-container[border="true"] .stSelectbox > div,
            [data-testid="stDateInput"] input {
                color: #333333 !important;
                background-color: #f8f9fa !important; /* Latar belakang input lebih terang */
                border: 1px solid #ced4da !important;
                border-radius: 8px !important;
                padding: 0.75rem 1rem !important;
                box-shadow: inset 0 1px 2px rgba(0,0,0,0.03); /* Shadow dalam */
            }
            [data-testid="stForm"] input:focus,
            [data-testid="stForm"] textarea:focus,
            [data-testid="stForm"] .stSelectbox > div:focus-within,
            .st-container[border="true"] .stSelectbox > div:focus-within,
            [data-testid="stDateInput"] input:focus {
                border-color: #007bff !important;
                box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25) !important;
            }

            /* Buttons */
            .stButton > button,
            [data-testid="stDownloadButton"] > button,
            [data-testid="stForm"] button {
                background-color: #007bff !important; /* Biru utama */
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
                padding: 0.75rem 1.25rem !important;
                transition: background-color 0.2s ease-in-out, transform 0.1s ease-in-out;
            }
            .stButton > button:hover,
            [data-testid="stDownloadButton"] > button:hover,
            [data-testid="stForm"] button:hover {
                background-color: #0056b3 !important; /* Biru lebih gelap saat hover */
                transform: translateY(-1px); /* Efek angkat sedikit */
            }
            .stButton > button:active,
            [data-testid="stDownloadButton"] > button:active,
            [data-testid="stForm"] button:active {
                transform: translateY(0); /* Kembali ke posisi semula saat diklik */
            }

            /* Tombol kembali ke menu (khusus untuk tombol yang spesifik) */
            .st-emotion-cache-lgl08a.e1g8pov61 button,
            .st-emotion-cache-pxri24 button { /* Streamlit's internal class for a button that fills a column */
                background-color: #6c757d !important; /* Abu-abu untuk tombol sekunder */
            }
            .st-emotion-cache-lgl08a.e1g8pov61 button:hover,
            .st-emotion-cache-pxri24 button:hover {
                background-color: #5a6268 !important;
            }

            /* Penyesuaian Warna Tabel */
            .st-emotion-cache-zq5wmm { /* Main table container */
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                overflow: hidden; /* Ensure rounded corners for table */
                max-height: 500px; /* Batasi tinggi tabel */
                overflow-y: auto; /* Tambahkan scroll vertikal */
            }
            table {
                border-collapse: collapse;
                width: 100%;
            }
            th {
                background-color: #495057; /* Header abu-abu gelap */
                color: #FFFFFF;
                border: 1px solid #6c757d; /* Border antar header */
                padding: 12px 15px;
                text-align: left;
                font-weight: 600;
                position: sticky; /* Agar header tetap saat scroll */
                top: 0;
                z-index: 1; /* Pastikan header di atas konten */
            }
            td {
                background-color: #FFFFFF;
                color: #333333;
                border: 1px solid #e9ecef; /* Border antar sel lebih tipis */
                padding: 10px 15px;
            }
            tr:nth-child(even) td {
                background-color: #f8f9fa; /* Warna latar belakang sel genap */
            }
            
            /* Warning/Info messages */
            .stAlert {
                border-radius: 8px;
                padding: 1rem 1.5rem;
                margin-top: 1rem;
            }
            .stAlert.warning {
                background-color: #fff3cd;
                color: #856404;
                border-color: #ffeeba;
            }
            .stAlert.info {
                background-color: #d1ecf1;
                color: #0c5460;
                border-color: #bee5eb;
            }

            /* Spinner styling */
            [data-testid="stSpinner"] .st-cd { /* Streamlit spinner message */
                color: #007bff;
            }
            
            /* Hide Streamlit header/footer default */
            #MainMenu, footer { visibility: hidden; }
            header { visibility: hidden; }

        </style>
        """, unsafe_allow_html=True)

    if 'buku_kas_view' not in st.session_state:
        st.session_state.buku_kas_view = 'menu'
    
    if 'show_report_data' not in st.session_state:
        st.session_state.show_report_data = False

    # Buat kolom untuk judul dan tombol kembali
    col_title, col_back_button = st.columns([0.7, 0.3])

    with col_title:
        st.title("📚 Modul Buku Kas")
    
    with col_back_button:
        # Tampilkan tombol "Kembali ke Menu Buku Kas" jika tidak di menu utama buku kas
        if st.session_state.buku_kas_view != 'menu':
            # Untuk menyelaraskan tombol ke kanan secara flex
            st.markdown("<div style='display: flex; justify-content: flex-end;'>", unsafe_allow_html=True)
            if st.button("⬅️ Kembali ke Menu Buku Kas", type="secondary", key="back_to_buku_kas_menu"):
                st.session_state.buku_kas_view = 'menu'
                if 'report_params' in st.session_state:
                    del st.session_state['report_params']
                st.session_state.show_report_data = False
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        # Tampilkan tombol "Kembali ke Menu Utama Aplikasi" jika di menu utama buku kas
        elif st.session_state.buku_kas_view == 'menu':
            st.markdown("<div style='display: flex; justify-content: flex-end;'>", unsafe_allow_html=True)
            if st.button("⬅️ Kembali ke Menu Utama Aplikasi", type="secondary", key="back_to_main_app_menu"):
                st.session_state.page = 'home'
                if 'page' in st.query_params:
                    st.query_params.clear()
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)


    st.markdown("---") # Separator setelah judul/tombol kembali

    if st.session_state.buku_kas_view == 'menu':
        st.markdown("### Pilih Laporan yang Ingin Anda Lihat")
        
        menu_options = {
            'buku_kas_umum': {
                "label": "Buku Kas Umum",
                "icon": buku_kas_svg_base64,
            },
            'rekap_saldo': {
                "label": "Rekap Saldo per POS",
                "icon": rekap_saldo_svg_base64,
            }
        }
        items = list(menu_options.items())
        cols = st.columns(len(items)) # Create columns dynamically based on number of menu items

        for i, (view, content) in enumerate(items):
            with cols[i]:
                # Apply a custom class for styling individual menu cards
                container = st.container(border=True)
                container.markdown(f"""
                    <div class='menu-card'>
                        <img src='data:image/svg+xml;base64,{content['icon']}' class='menu-icon'>
                        <h3>{content['label']}</h3>
                        <p style='text-align: center; color: #777; font-size: 0.9em; margin-top: -10px; margin-bottom: 15px;'></p>
                    </div>
                """, unsafe_allow_html=True)
                if container.button("Lihat Laporan", key=f"btn_bukukas_{view}", use_container_width=True, type="primary"):
                    st.session_state.buku_kas_view = view
                    st.session_state.show_report_data = False # Reset this flag when changing view
                    st.rerun()

    elif st.session_state.buku_kas_view == 'buku_kas_umum':
        show_buku_kas_umum()
    elif st.session_state.buku_kas_view == 'rekap_saldo':
        show_rekap_saldo()