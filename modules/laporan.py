import streamlit as st
import pandas as pd
from utils import db_functions as db
from datetime import datetime, timedelta
import calendar
import os # Tambahkan import os untuk path yang lebih robust
import math 

# --- Fungsi Bantuan untuk Memuat Ikon SVG dari File ---
def load_svg(filepath):
    """Membaca dan mengembalikan konten file SVG sebagai string."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        st.error(f"Error: File ikon tidak ditemukan di '{filepath}'")
        return "" # Mengembalikan string kosong jika file tidak ada

# --- Definisi Ikon SVG dari File Lokal ---
# PASTIKAN nama file 'laporan.svg' dan 'rekap.svg' sesuai dengan file Anda
# di folder 'assets/laporan/'
LAPORAN_ICON_PATH = os.path.join("assets", "laporan", "tunggakan.svg")
REKAP_ICON_PATH = os.path.join("assets", "laporan", "pemasukan.svg")

SVG_ICONS = {
    "laporan": load_svg(LAPORAN_ICON_PATH),
    "rekap": load_svg(REKAP_ICON_PATH)
}


# --- Fungsi Bantuan CSS ---
def inject_custom_css():
    """Menyuntikkan CSS kustom untuk halaman."""
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
                height: 100%; display: flex; flex-direction: column; justify-content: space-between; padding: 1.5rem;
            }
            div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] > div[data-testid="stBorderedSticker"]:hover {
                transform: translateY(-5px); box-shadow: 0 8px 16px rgba(0,0,0,0.12); border: 1px solid #007BFF;
            }
            .menu-item-content { text-align: center; flex-grow: 1; }
            .menu-icon-container { color: #343A40; margin-bottom: 1rem; transition: color 0.3s ease-in-out; }
            .menu-icon-container svg { width: 50px; height: 50px; }
            div[data-testid="stBorderedSticker"]:hover .menu-icon-container { color: #007BFF; }
            .menu-item-content h5 { font-size: 1.1rem; font-weight: 600; color: #343A40; margin: 0; }
            
            /* Styling untuk tombol utama di kartu dan form */
            .stButton > button {
                background-color: #007BFF !important; color: white !important; font-weight: bold;
                border-radius: 8px !important; border: none !important; width: 100% !important;
                padding: 0.75rem 0 !important; font-size: 1rem !important; margin-top: 1rem;
            }
            .stButton > button:hover { background-color: #0056b3 !important; }

            /* Styling untuk container filter dan hasil */
            div[data-testid="stForm"], div[data-testid="stExpander"], .st-container[border="true"] {
                background-color: #FFFFFF !important; border: 1px solid #DEE2E6 !important;
                border-radius: 12px !important; padding: 1.5rem !important;
            }
            [data-testid="stForm"] label, div[data-testid="stExpander"] summary, .st-container[border="true"] div[data-testid="stText"] {
                color: #343A40 !important; font-weight: 600;
            }
            div[data-testid="stExpander"] > details > summary {
                font-size: 1.1rem;
            }
        </style>
        """, unsafe_allow_html=True)

# --- Fungsi Terpusat (Diperbaiki) ---
def render_filter_widgets(key_prefix="default"):
    """Fungsi terpusat untuk menampilkan widget filter di dalam container."""
    with st.container(border=True):
        st.write("**⚙️ Filter Laporan**")
        
        conn = db.create_connection()
        # Fungsi ini akan jauh lebih cepat jika menggunakan @st.cache_data
        list_kelas = db.get_semua_kelas(conn)
        conn.close()
        
        kelas_dict = {f"{angkatan} - {nama} ({tahun})": id_kelas for id_kelas, angkatan, nama, tahun in list_kelas}
        pilihan_kelas = ["Semua Kelas"] + list(kelas_dict.keys())
        
        col_filter1, col_filter2 = st.columns(2)
        selected_kelas_nama = col_filter1.selectbox("Filter per Kelas", options=pilihan_kelas, key=f"{key_prefix}_filter_kelas")
        search_term = col_filter2.text_input("Cari Nama Siswa / NIS", key=f"{key_prefix}_search", placeholder="Ketik di sini...")
        
        id_kelas_filter = None
        if selected_kelas_nama != "Semua Kelas":
            id_kelas_filter = kelas_dict[selected_kelas_nama]
            
        return id_kelas_filter, search_term

def display_rekap_data(title, tgl_mulai, tgl_sampai, id_kelas=None, search_term=None):
    """Fungsi terpusat untuk menampilkan data rekap."""
    conn = db.create_connection()
    data_rekap = db.get_rekap_pembayaran(conn, tgl_mulai, tgl_sampai, id_kelas, search_term)
    conn.close()

    st.markdown("---")
    st.subheader("📊 Hasil Rekapitulasi")

    if not data_rekap:
        st.warning("Tidak ada data rekap yang cocok dengan filter Anda.")
        return
    
    with st.container(border=True):
        df = pd.DataFrame(data_rekap, columns=['Jenis POS', 'Total Pemasukan (Rp)'])
        df['Total Pemasukan (Rp)'] = pd.to_numeric(df['Total Pemasukan (Rp)'])
        
        st.write(f"**{title}**")
        st.dataframe(df, use_container_width=True)
        
        total_pemasukan = df['Total Pemasukan (Rp)'].sum()
        st.metric("💰 Grand Total Pemasukan Sesuai Filter", f"Rp {total_pemasukan:,.0f}")

# --- Halaman Utama untuk Rekap Pembayaran (UI/UX Diperbaiki dengan st.form) ---
def show_rekap_pembayaran():
    """
    Menampilkan halaman rekapitulasi pembayaran dengan UI/UX yang disempurnakan.
    Pilihan jenis rekap dipisah dari form untuk interaktivitas langsung.
    """
    st.subheader("💳 Rekapitulasi Pemasukan")
    st.write("Pilih jenis rekap di bawah ini. Untuk rentang tanggal spesifik, pilih 'Periode Kustom'.")

    # LANGKAH 1: Pilihan jenis rekap diletakkan DI LUAR form.
    # Perubahan di sini akan langsung me-render ulang halaman dan mengaktifkan/menonaktifkan input tanggal.
    jenis_rekap = st.selectbox(
        "Pilih Jenis Rekapitulasi",
        options=["Harian", "Mingguan", "Bulanan", "Triwulan", "Semesteran", "Tahunan", "Periode Kustom"],
        key="pilihan_rekap",
        help="Memilih opsi selain 'Periode Kustom' akan mengisi tanggal secara otomatis."
    )

    # Logika untuk menentukan tanggal default berdasarkan jenis rekap
    today = datetime.now().date()
    tgl_mulai_default = today
    tgl_sampai_default = today

    if jenis_rekap == "Mingguan":
        start_of_this_week = today - timedelta(days=today.weekday())
        tgl_mulai_default = start_of_this_week - timedelta(days=7)
        tgl_sampai_default = tgl_mulai_default + timedelta(days=6)
    elif jenis_rekap == "Bulanan":
        first_day_current_month = today.replace(day=1)
        last_day_last_month = first_day_current_month - timedelta(days=1)
        tgl_mulai_default = last_day_last_month.replace(day=1)
        tgl_sampai_default = last_day_last_month
    elif jenis_rekap == "Triwulan":
        current_quarter_start_month = 3 * ((today.month - 1) // 3) + 1
        current_quarter_start_date = today.replace(month=current_quarter_start_month, day=1)
        last_quarter_end_date = current_quarter_start_date - timedelta(days=1)
        last_quarter_start_month = 3 * ((last_quarter_end_date.month - 1) // 3) + 1
        tgl_mulai_default = last_quarter_end_date.replace(month=last_quarter_start_month, day=1)
        tgl_sampai_default = last_quarter_end_date
    elif jenis_rekap == "Semesteran":
        if today.month <= 6:
            tgl_mulai_default = today.replace(year=today.year - 1, month=7, day=1)
            tgl_sampai_default = today.replace(year=today.year - 1, month=12, day=31)
        else:
            tgl_mulai_default = today.replace(month=1, day=1)
            tgl_sampai_default = today.replace(month=6, day=30)
    elif jenis_rekap == "Tahunan":
        tgl_mulai_default = today.replace(year=today.year - 1, month=1, day=1)
        tgl_sampai_default = today.replace(year=today.year - 1, month=12, day=31)

    # LANGKAH 2: Gunakan form hanya untuk mengelompokkan input yang perlu dikirim bersamaan.
    with st.form(key="rekap_form"):
        st.write("**Atur Periode dan Filter Laporan**")
        
        # Tentukan apakah input tanggal harus dinonaktifkan
        is_disabled = jenis_rekap != "Periode Kustom"
        
        col1, col2 = st.columns(2)
        # Input tanggal sekarang berada di dalam form, tetapi status disabled-nya
        # dikontrol oleh selectbox yang berada di luar form.
        tgl_mulai = col1.date_input("Tanggal Mulai", value=tgl_mulai_default, disabled=is_disabled)
        tgl_sampai = col2.date_input("Tanggal Sampai", value=tgl_sampai_default, disabled=is_disabled)

        st.markdown("---")
        
        # Filter tambahan (kelas dan nama)
        id_kelas_filter, search_term = render_filter_widgets(key_prefix="rekap")

        st.markdown("---")
        
        # Tombol submit untuk form
        submitted = st.form_submit_button("🚀 Tampilkan Rekapitulasi", type="primary", use_container_width=True)

    # LANGKAH 3: Logika setelah form disubmit tetap sama.
    if submitted:
        # Jika periode bukan kustom, pastikan kita menggunakan tanggal default yang benar
        final_tgl_mulai = tgl_mulai_default if is_disabled else tgl_mulai
        final_tgl_sampai = tgl_sampai_default if is_disabled else tgl_sampai

        if final_tgl_mulai > final_tgl_sampai:
            st.error("Tanggal mulai tidak boleh lebih akhir dari tanggal sampai.")
        else:
            title = f"Rekap Pemasukan {jenis_rekap}: {final_tgl_mulai.strftime('%d-%m-%Y')} s/d {final_tgl_sampai.strftime('%d-%m-%Y')}"
            
            display_rekap_data(
                title,
                final_tgl_mulai, 
                final_tgl_sampai, 
                id_kelas_filter, 
                search_term
            )
# --- Laporan Tunggakan (Dengan Paginasi) ---
def show_laporan_tunggakan():
    st.subheader("Laporan Tunggakan Siswa")

    # --- Bagian 1: Widget Filter & Tombol Aksi ---
    id_kelas_filter, search_term = render_filter_widgets(key_prefix="tunggakan")

    def fetch_data_tunggakan():
        conn = db.create_connection()
        data_tunggakan = db.get_semua_tunggakan(conn, kelas_id=id_kelas_filter, search_term=search_term)
        conn.close()
        
        # Reset ke halaman 1 setiap kali ada pencarian baru
        st.session_state.current_page = 1 
        
        if not data_tunggakan:
            st.session_state.df_tunggakan = None
            st.warning("Tidak ada data tunggakan yang ditemukan untuk filter ini.")
            return

        df = pd.DataFrame(data_tunggakan, columns=['NIS', 'Nama Siswa', 'Kelas', 'Item Pembayaran', 'Bulan', 'Tunggakan', 'Angkatan'])
        df['Tunggakan'] = pd.to_numeric(df['Tunggakan'])
        st.session_state.df_tunggakan = df

    st.button("Tampilkan Tunggakan", type="primary", use_container_width=True, on_click=fetch_data_tunggakan)
    st.markdown("---")

    # --- Bagian 2: Tampilan Hasil (jika data ada) ---
    if 'df_tunggakan' in st.session_state and st.session_state.df_tunggakan is not None:
        df = st.session_state.df_tunggakan

        # Tampilkan Ringkasan & Tombol Download seperti sebelumnya
        st.subheader("📊 Ringkasan Tunggakan")
        total_tunggakan_keseluruhan = df['Tunggakan'].sum()
        jumlah_siswa_menunggak = len(df.groupby(['NIS', 'Nama Siswa']))
        rata_rata_tunggakan = total_tunggakan_keseluruhan / jumlah_siswa_menunggak if jumlah_siswa_menunggak > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Grand Total Tunggakan", f"Rp {total_tunggakan_keseluruhan:,.0f}")
        col2.metric("👥 Jumlah Siswa Menunggak", f"{jumlah_siswa_menunggak} Siswa")
        col3.metric("📈 Rata-rata Tunggakan", f"Rp {rata_rata_tunggakan:,.0f}")
        
        # ... (Kode tombol download tetap sama) ...
        @st.cache_data
        def convert_df_to_csv(df_to_convert):
            return df_to_convert.to_csv(index=False).encode('utf-8')
        csv = convert_df_to_csv(df)
        st.download_button(label="📥 Unduh Laporan sebagai CSV", data=csv, file_name=f"laporan_tunggakan_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
        
        st.markdown("---")
        st.subheader("📂 Rincian Tunggakan per Siswa")

        # Logika Pengurutan
        sort_option = st.selectbox("Urutkan berdasarkan", ["Tunggakan Terbesar", "Tunggakan Terkecil", "Nama Siswa (A-Z)"], key="sort_tunggakan")
        student_groups = df.groupby(['NIS', 'Nama Siswa', 'Kelas'])
        agg_data = [{'nis': nis, 'nama': nama, 'kelas': kelas, 'total_tunggakan': group['Tunggakan'].sum(), 'group_data': group} for (nis, nama, kelas), group in student_groups]
        
        if sort_option == "Tunggakan Terbesar":
            sorted_students = sorted(agg_data, key=lambda x: x['total_tunggakan'], reverse=True)
        elif sort_option == "Tunggakan Terkecil":
            sorted_students = sorted(agg_data, key=lambda x: x['total_tunggakan'])
        else:
            sorted_students = sorted(agg_data, key=lambda x: x['nama'])

        # --- LOGIKA PAGINASI BARU DIMULAI DI SINI ---
        items_per_page = 5
        total_items = len(sorted_students)
        total_pages = math.ceil(total_items / items_per_page)
        
        # Pastikan halaman saat ini valid
        if st.session_state.current_page > total_pages:
            st.session_state.current_page = total_pages
        if total_pages == 0: # Kasus jika tidak ada data sama sekali
            st.session_state.current_page = 1
            
        start_index = (st.session_state.current_page - 1) * items_per_page
        end_index = start_index + items_per_page
        
        # Ambil data hanya untuk halaman saat ini
        students_on_page = sorted_students[start_index:end_index]

        # Tampilkan data per halaman
        for student in students_on_page:
            expander_title = f"**{student['nama']}** (NIS: {student['nis']}) | Kelas: {student['kelas']} | **Total Tunggakan: Rp {student['total_tunggakan']:,.0f}**"
            with st.expander(expander_title):
                # ... (Isi expander seperti kode sebelumnya, tidak ada perubahan di sini) ...
                display_group = student['group_data'][['Item Pembayaran', 'Bulan', 'Tunggakan']].reset_index(drop=True)
                display_group['Tunggakan'] = display_group['Tunggakan'].apply(lambda x: f"Rp {x:,.0f}")
                st.dataframe(display_group, use_container_width=True)

                if st.button("🖨️ Siapkan Rincian untuk Cetak", key=f"cetak_{student['nis']}"):
                    with st.container(border=True):
                        st.info("Teks di bawah ini siap untuk disalin (Ctrl+C) dan ditempel (Ctrl+V).")
                        rincian_items = ""
                        for _, row in student['group_data'].iterrows():
                            rincian_items += f"- {row['Item Pembayaran']} ({row['Bulan']}): **Rp {row['Tunggakan']:,.0f}**\n"
                        cetak_teks = f"""
                        #### RINCIAN TUNGGAKAN SISWA
                        ---
                        - **Nama**: &nbsp;&nbsp;&nbsp;&nbsp;{student['nama']}
                        - **NIS**: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{student['nis']}
                        - **Kelas**: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{student['kelas']}
                        - **Total**: &nbsp;&nbsp;&nbsp;**Rp {student['total_tunggakan']:,.0f}**
                        
                        **Rincian Tunggakan:**
                        {rincian_items}
                        """
                        st.markdown(cetak_teks)
        
        st.markdown("---")

        # --- KONTROL PAGINASI (TOMBOL NEXT/PREV) ---
        if total_pages > 1:
            col_prev, col_page, col_next = st.columns([2, 3, 2])

            # Tombol "Sebelumnya"
            with col_prev:
                if st.button("⬅️ Sebelumnya", use_container_width=True, disabled=(st.session_state.current_page <= 1)):
                    st.session_state.current_page -= 1
                    st.rerun()
            
            # Indikator Halaman
            with col_page:
                st.markdown(f"<div style='text-align: center;'>Halaman <b>{st.session_state.current_page}</b> dari <b>{total_pages}</b></div>", unsafe_allow_html=True)
            
            # Tombol "Berikutnya"
            with col_next:
                if st.button("Berikutnya ➡️", use_container_width=True, disabled=(st.session_state.current_page >= total_pages)):
                    st.session_state.current_page += 1
                    st.rerun()

# --- Fungsi Render Utama (Inisialisasi state halaman) ---
def render():
    inject_custom_css()

    # Inisialisasi session_state jika belum ada
    if 'laporan_view' not in st.session_state:
        st.session_state.laporan_view = 'menu'
    if 'df_tunggakan' not in st.session_state:
        st.session_state.df_tunggakan = None
    # TAMBAHKAN INISIALISASI HALAMAN
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1

    # --- Header dengan Tombol Kembali ---
    col_title, col_button = st.columns([3, 1])
    with col_title:
        st.title("📄 Modul Laporan")

    with col_button:
        if st.session_state.laporan_view != 'menu':
            if st.button("⬅️ Kembali ke Menu"):
                st.session_state.laporan_view = 'menu'
                st.session_state.df_tunggakan = None
                st.session_state.current_page = 1 # Reset halaman juga
                st.rerun()
        else:
            if st.button("⬅️ Menu Utama"):
                st.session_state.page = 'home'
                if 'page' in st.query_params:
                    st.query_params.clear()
                st.rerun()

    st.markdown("---")
    
    # ... Sisa kode render tetap sama ...
    menu_actions = {
        'laporan_pembayaran': show_laporan_tunggakan,
        'rekap_pembayaran': show_rekap_pembayaran
    }

    if st.session_state.laporan_view == 'menu':
        menu_options = {
            'laporan_pembayaran': {"label": "Laporan Tunggakan", "icon": SVG_ICONS["laporan"]},
            'rekap_pembayaran': {"label": "Rekap Pemasukan", "icon": SVG_ICONS["rekap"]}
        }
        
        cols = st.columns(len(menu_options))
        
        for i, (view, content) in enumerate(menu_options.items()):
            with cols[i]:
                with st.container(border=True):
                    st.markdown(f"""
                        <div class="menu-item-content">
                            <div class="menu-icon-container">{content['icon']}</div>
                            <h5>{content['label']}</h5>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Pilih Menu", key=f"btn_laporan_{view}", use_container_width=True):
                        st.session_state.laporan_view = view
                        st.rerun()
    else:
        if st.session_state.laporan_view in menu_actions:
            menu_actions[st.session_state.laporan_view]()