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

            # Tambahkan kolom 'Pengeluaran (Rp)' dan 'Saldo' yang sudah diformat
            df['Pengeluaran (Rp)'] = "Rp 0"
            df['Saldo'] = df['Saldo Raw'].apply(lambda x: f"Rp {x:,.0f}")
            # Format kolom 'Penerimaan (Rp)' yang asli
            df['Penerimaan (Rp)'] = df['Penerimaan (Rp) Raw'].apply(lambda x: f"Rp {x:,.0f}")


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
    #  df_export = pd.DataFrame(rekap_data, columns=['Jenis POS', 'Saldo'])
    #  return df_export.to_csv(index=False).encode('utf-8')
    # csv_data = convert_df_to_csv(df_rekap)
    # st.download_button(
    #  label="📥 Unduh Data Rekap Saldo (CSV)",
    #  data=csv_data,
    #  file_name=f"rekap_saldo_per_pos_{datetime.now().strftime('%Y%m%d')}.csv",
    #  mime="text/csv",
    #  help="Unduh data rekapitulasi saldo ke format CSV."
    # )

    # Hapus juga fungsi create_rekap_saldo_pdf dan panggilannya
    # function create_rekap_saldo_pdf (dihapus)


# --- FUNGSI RENDER UTAMA MODUL (DENGAN GAYA BARU) ---
def render():
    """
    Merender seluruh antarmuka untuk Modul Buku Kas dengan memuat ikon SVG
    langsung dari file dan menggunakan CSS untuk styling.
    """

    @st.cache_data
    def load_svg(filepath):
        """Membuka file SVG dan mengembalikannya sebagai string XML."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                svg = f.read()
            return svg 
        except FileNotFoundError:
            st.error(f"Ikon tidak ditemukan di: {filepath}")
            return '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="red" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'

    # --- Path ke Ikon SVG di Folder Assets ---
    path_buku_kas = "assets/buku_kas/bukukas.svg"
    path_rekap_saldo = "assets/buku_kas/rekap_saldo.svg"
    
    # --- Injeksi CSS Baru ---
    st.markdown("""
        <style>
            /* Latar belakang utama */
            .main, [data-testid="stAppViewContainer"] {
                background-color: #FFF7E8;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            
            /* Styling untuk kartu menu */
            div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] > div[data-testid="stBorderedSticker"] {
                background-color: #FFFFFF;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                transition: all 0.3s ease-in-out;
                display: flex; 
                flex-direction: column; 
                padding: 1.5rem;
                max-width: 280px;
                margin: auto;
            }

            /* Efek hover pada kartu menu */
            div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] > div[data-testid="stBorderedSticker"]:hover {
                transform: translateY(-5px); 
                box-shadow: 0 8px 16px rgba(0,0,0,0.12); 
                border-color: #007BFF;
            }
            
            /* --- PERUBAHAN UTAMA DI SINI --- */
            /* Konten di dalam kartu */
            .menu-item-content { 
                text-align: center; 
                margin-bottom: 1.5rem; /* Beri jarak bawah agar tidak terlalu mepet dengan tombol */
                /* flex-grow: 1; <-- Properti ini dihapus untuk menghilangkan ruang kosong */
            }

            /* Kontainer Ikon */
            .menu-icon-container svg { width: 60px; height: 60px; } /* Ukuran ikon */
            
            /* Judul menu */
            .menu-item-content h5 { font-size: 1.1rem; font-weight: 600; color: #343A40; margin-top: 0.5rem; }
            
            /* Tombol utama di dalam kartu */
            .stButton > button {
                background-color: #007BFF !important; color: white !important; font-weight: bold;
                border-radius: 8px !important; border: none !important; width: 100% !important;
                padding: 0.75rem 0 !important; font-size: 1rem !important;
                margin-top: auto; /* Mendorong tombol ke bagian bawah jika ada ruang lebih */
            }
            .stButton > button:hover { background-color: #0056b3 !important; }
        </style>
        """, unsafe_allow_html=True)
    
    # --- Penanganan State Halaman ---
    if 'buku_kas_view' not in st.session_state:
        st.session_state.buku_kas_view = 'menu'
    if 'show_report_data' not in st.session_state:
        st.session_state.show_report_data = False
        
    # --- HEADER: Judul dan Tombol Kembali ---
    col_title, col_button = st.columns([3, 1])
    with col_title:
        st.title("📚 Modul Buku Kas")
    with col_button:
        st.markdown('<div style="height: 2.5rem;"></div>', unsafe_allow_html=True)
        if st.session_state.buku_kas_view != 'menu':
            if st.button("⬅️ Kembali ke Menu", key="bukukas_back_to_menu", use_container_width=True):
                st.session_state.buku_kas_view = 'menu'
                st.session_state.show_report_data = False
                if 'report_params' in st.session_state:
                    del st.session_state['report_params']
                st.rerun()
        else:
            if st.button("⬅️ Menu Utama", key="bukukas_back_to_main", use_container_width=True):
                st.session_state.page = 'home'
                if 'page' in st.query_params: st.query_params.clear()
                st.rerun()

    st.markdown("---")

    # --- RENDER KONTEN: Menu atau Sub-halaman ---
    if st.session_state.buku_kas_view == 'menu':
        menu_options = {
            'buku_kas_umum': {"label": "Buku Kas Umum", "path": path_buku_kas},
            'rekap_saldo': {"label": "Rekap Saldo per POS", "path": path_rekap_saldo}
        }
        
        items = list(menu_options.items())
        cols = st.columns(len(items)) 
        
        for i, (view, content) in enumerate(items):
            with cols[i]:
                with st.container(border=True): # Tidak perlu mengatur tinggi, biarkan otomatis
                    st.markdown(f"""
                        <div class="menu-item-content">
                            <div class="menu-icon-container">
                                {load_svg(content['path'])}
                            </div>
                            <h5>{content['label']}</h5>
                        </div>
                        """, unsafe_allow_html=True)

                    # Ganti teks tombol
                    if st.button("Pilih Menu", key=f"btn_bukukas_{view}"):
                        st.session_state.buku_kas_view = view
                        st.rerun()
    else:
        view_function_map = {
            'buku_kas_umum': show_buku_kas_umum,
            'rekap_saldo': show_rekap_saldo
        }
        render_function = view_function_map.get(st.session_state.buku_kas_view)
        if render_function:
            render_function()