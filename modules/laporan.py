import streamlit as st
import pandas as pd
from utils import db_functions as db
from datetime import datetime, timedelta
import calendar
# --- Fungsi Terpusat (Diperbaiki) ---
def render_filter_widgets(show_date_range=False, key_prefix="default"):
    """
    Fungsi terpusat untuk menampilkan widget filter.
    Kunci widget kini dinamis menggunakan 'key_prefix' untuk menghindari error.
    """
    st.write("**Filter Laporan**")
    
    conn = db.create_connection()
    # Fungsi ini akan jauh lebih cepat jika menggunakan @st.cache_data
    list_kelas = db.get_semua_kelas(conn)
    conn.close()
    
    kelas_dict = {f"{angkatan} - {nama} ({tahun})": id_kelas for id_kelas, angkatan, nama, tahun in list_kelas}
    pilihan_kelas = ["Semua Kelas"] + list(kelas_dict.keys())
    
    tgl_mulai, tgl_sampai = None, None
    if show_date_range:
        col1, col2 = st.columns(2)
        tgl_mulai = col1.date_input("Tanggal Mulai", key=f"{key_prefix}_tgl_mulai")
        tgl_sampai = col2.date_input("Tanggal Sampai", key=f"{key_prefix}_tgl_sampai")

    col_filter1, col_filter2 = st.columns(2)
    # Kunci dibuat dinamis dengan prefix
    selected_kelas_nama = col_filter1.selectbox("Filter per Kelas", options=pilihan_kelas, key=f"{key_prefix}_filter_kelas")
    search_term = col_filter2.text_input("Cari Nama/NIS", key=f"{key_prefix}_search")
    
    id_kelas_filter = None
    if selected_kelas_nama != "Semua Kelas":
        id_kelas_filter = kelas_dict[selected_kelas_nama]
        
    return tgl_mulai, tgl_sampai, id_kelas_filter, search_term

def display_rekap_data(title, tgl_mulai, tgl_sampai, id_kelas=None, search_term=None):
    """Fungsi terpusat untuk menampilkan data rekap."""
    conn = db.create_connection()
    data_rekap = db.get_rekap_pembayaran(conn, tgl_mulai, tgl_sampai, id_kelas, search_term)
    conn.close()

    if not data_rekap:
        st.warning("Tidak ada data rekap yang cocok dengan filter Anda.")
        return
    
    df = pd.DataFrame(data_rekap, columns=['Jenis POS', 'Total Pemasukan (Rp)'])
    df['Total Pemasukan (Rp)'] = pd.to_numeric(df['Total Pemasukan (Rp)']) # Pastikan tipe data numerik
    
    st.write(f"**{title}**")
    st.dataframe(df, use_container_width=True)
    
    total_pemasukan = df['Total Pemasukan (Rp)'].sum()
    st.metric("Grand Total Pemasukan Sesuai Filter", f"Rp {total_pemasukan:,.0f}")

# --- Halaman untuk Setiap Jenis Rekap (Diperbaiki) ---
def show_rekap_per_hari():
    st.subheader("Rekap Pembayaran Harian")
    tanggal_laporan = st.date_input("Pilih Tanggal")
    # Menggunakan key_prefix unik
    _, _, id_kelas_filter, search_term = render_filter_widgets(key_prefix="harian")
    if st.button("Tampilkan Rekap", type="primary"):
        display_rekap_data(f"Rekap Pemasukan Tanggal: {tanggal_laporan.strftime('%d-%m-%Y')}", tanggal_laporan, tanggal_laporan, id_kelas_filter, search_term)

def show_rekap_per_periode(jenis_rekap):
    st.subheader(f"Rekap Pembayaran {jenis_rekap}")

    # --- LOGIKA PENENTUAN TANGGAL OTOMATIS ---
    today = datetime.now().date()
    tgl_mulai_default, tgl_sampai_default = today, today

    if jenis_rekap == "Perminggu":
        # Default ke minggu lalu (Senin - Minggu)
        start_of_this_week = today - timedelta(days=today.weekday())
        tgl_mulai_default = start_of_this_week - timedelta(days=7)
        tgl_sampai_default = tgl_mulai_default + timedelta(days=6)
    elif jenis_rekap == "Perbulan":
        # Default ke bulan lalu
        first_day_current_month = today.replace(day=1)
        last_day_last_month = first_day_current_month - timedelta(days=1)
        tgl_mulai_default = last_day_last_month.replace(day=1)
        tgl_sampai_default = last_day_last_month
    # Anda bisa tambahkan logika untuk Pertriwulan, Persemester, Pertahun di sini

    st.write("**Pilih Periode Laporan**")
    col1, col2 = st.columns(2)
    tgl_mulai = col1.date_input("Tanggal Mulai", value=tgl_mulai_default, key=f"{jenis_rekap}_mulai")
    tgl_sampai = col2.date_input("Tanggal Sampai", value=tgl_sampai_default, key=f"{jenis_rekap}_sampai")
    
    # Panggil filter lainnya setelah widget tanggal
    _, _, id_kelas_filter, search_term = render_filter_widgets(key_prefix=jenis_rekap.lower())

    if st.button("Tampilkan Rekap", type="primary", key=f"btn_{jenis_rekap}"):
        if not tgl_mulai or not tgl_sampai:
            st.error("Tanggal mulai dan tanggal sampai harus diisi.")
            return
        if tgl_mulai > tgl_sampai:
            st.error("Tanggal mulai tidak boleh lebih akhir dari tanggal sampai.")
            return

        display_rekap_data(
            f"Rekap Pemasukan {jenis_rekap}: {tgl_mulai.strftime('%d-%m-%Y')} s/d {tgl_sampai.strftime('%d-%m-%Y')}",
            tgl_mulai, tgl_sampai, id_kelas_filter, search_term
        )

# --- Halaman Utama untuk Rekap Pembayaran (Logika pemanggilan diperbaiki) ---
def show_rekap_pembayaran():
    pilihan_rekap = {
        "Perhari": show_rekap_per_hari,
        "Perminggu": lambda: show_rekap_per_periode("Perminggu"),
        "Perbulan": lambda: show_rekap_per_periode("Perbulan"),
        "Pertriwulan": lambda: show_rekap_per_periode("Pertriwulan"),
        "Persemester": lambda: show_rekap_per_periode("Persemester"),
        "Pertahun": lambda: show_rekap_per_periode("Pertahun"),
    }
    
    jenis_rekap = st.selectbox("Pilih Jenis Rekapitulasi", options=pilihan_rekap.keys())
    
    # Jalankan fungsi yang dipilih dari dictionary
    pilihan_rekap[jenis_rekap]()

# --- Semua fungsi laporan pembayaran lainnya (Diperbaiki) ---
def show_laporan_tunggakan():
    st.subheader("Laporan Tunggakan Siswa")
    
    # MENGGUNAKAN KEMBALI FUNGSI FILTER (LEBIH EFISIEN)
    _, _, id_kelas_filter, search_term = render_filter_widgets(key_prefix="tunggakan")
    
    if st.button("Tampilkan Tunggakan", type="primary"):
        conn = db.create_connection()
        data_tunggakan = db.get_semua_tunggakan(conn, kelas_id=id_kelas_filter, search_term=search_term)
        conn.close()
        
        if not data_tunggakan:
            st.info("Tidak ada data tunggakan yang ditemukan untuk filter ini.")
            return
            
        df = pd.DataFrame(data_tunggakan, columns=['NIS', 'Nama Siswa', 'Kelas', 'Item Pembayaran', 'Bulan', 'Tunggakan', 'Angkatan'])
        df['Tunggakan'] = pd.to_numeric(df['Tunggakan']) # Pastikan tipe data numerik
        
        total_tunggakan_keseluruhan = 0
        
        # Grouping dan menampilkan data per siswa
        for (nis, nama, kelas), group in df.groupby(['NIS', 'Nama Siswa', 'Kelas']):
            st.markdown("---")
            st.write(f"**Nama:** {nama}")
            st.write(f"**NIS:** {nis} | **Kelas:** {kelas}")
            
            display_group = group[['Item Pembayaran', 'Bulan', 'Tunggakan']].reset_index(drop=True)
            st.dataframe(display_group, use_container_width=True)
            
            total_per_siswa = group['Tunggakan'].sum()
            st.error(f"**Total Tunggakan Siswa: Rp {total_per_siswa:,.0f}**")
            total_tunggakan_keseluruhan += total_per_siswa
            
        st.markdown("---")
        st.header(f"Grand Total Semua Tunggakan: Rp {total_tunggakan_keseluruhan:,.0f}")

def show_laporan_pembayaran():
    # Karena hanya ada satu jenis laporan, tidak perlu selectbox.
    # Langsung panggil fungsi laporannya untuk UX yang lebih baik.
    # Jika nanti ada laporan lain, Anda bisa kembali menggunakan st.selectbox.
    show_laporan_tunggakan()

# --- Fungsi Render Utama (Tidak ada perubahan signifikan) ---
def render():
    # --- PENAMBAHAN CSS ---
    st.markdown("""
        <style>
            /* Latar belakang utama */
            .main, [data-testid="stAppViewContainer"] {
                background-color: #FFF7E8;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }

            /* Gaya Kotak Konten (SEMI-TRANSPARAN) */
            .st-emotion-cache-1d8vwwt,
            [data-testid="stForm"],
            div[data-testid="stExpander"],
            .st-container[border="true"] {
                background-color: rgba(0, 0, 0, 0.7) !important;
                border: 1px solid #495057 !important;
                border-radius: 12px !important;
                padding: 1.5rem !important;
                box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            }
            
            .st-emotion-cache-1d8vwwt:hover {
                border-color: #007BFF !important;
                transform: translateY(-5px);
            }

            /* Penyesuaian Warna Teks di Dalam Kotak Gelap */
            .st-emotion-cache-1d8vwwt h5, [data-testid="stForm"] h6, div[data-testid="stExpander"] summary,
            [data-testid="stForm"] label, .st-container[border="true"] div[data-testid="stText"],
            [data-testid="stMetric"], [data-testid="stMetricLabel"] > div, [data-testid="stMetricValue"] {
                color: #FFFFFF !important;
                font-weight: 600;
            }
            .st-emotion-cache-1d8vwwt h5::before {
                content: ''; position: absolute; left: 0; top: 50%;
                transform: translateY(-50%); width: 8px; height: 100%;
                background-color: #007BFF; border-radius: 4px;
            }
            .st-emotion-cache-1d8vwwt h5 { position: relative; padding-left: 20px; }
            .st-emotion-cache-1d8vwwt p, div[data-testid="stExpander"] p, div[data-testid="stExpander"] li {
                color: #E0E0E0 !important;
            }
            .st-emotion-cache-1d8vwwt p { flex-grow: 1; }

            /* Gaya Tombol (REVISI AKHIR) */
            .stButton > button, 
            [data-testid="stDownloadButton"] > button, 
            [data-testid="stForm"] button {
                background-color: #007BFF !important;
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
            }
            .stButton > button:hover, 
            [data-testid="stDownloadButton"] > button:hover, 
            [data-testid="stForm"] button:hover {
                background-color: #0056b3 !important;
            }
        </style>
        """, unsafe_allow_html=True)

    st.title("📄 Modul Laporan")
    
    if 'laporan_view' not in st.session_state:
        st.session_state.laporan_view = 'menu'

    if st.session_state.laporan_view != 'menu':
        if st.button("⬅️ Kembali ke Menu Laporan"):
            st.session_state.laporan_view = 'menu'
            st.rerun()
        st.markdown("---")
    
    menu_actions = {
        'laporan_pembayaran': show_laporan_pembayaran,
        'rekap_pembayaran': show_rekap_pembayaran
    }

    if st.session_state.laporan_view == 'menu':
        st.markdown("---")
        menu_options = {
            'laporan_pembayaran': {"label": "Laporan Pembayaran", "desc": "Tampilkan laporan pemasukan dan tunggakan."},
            'rekap_pembayaran': {"label": "Rekap Pemasukan", "desc": "Lihat rekapitulasi total pemasukan per jenis POS."}
        }
        items = list(menu_options.items())
        cols = st.columns(len(items))
        
        for i, (view, content) in enumerate(items):
            with cols[i]:
                container = st.container(border=True)
                container.markdown(f"<h5>{content['label']}</h5>", unsafe_allow_html=True)
                container.markdown(f"<p>{content['desc']}</p>", unsafe_allow_html=True)
                if container.button("Pilih Menu", key=f"btn_laporan_{view}", use_container_width=True):
                    st.session_state.laporan_view = view
                    st.rerun()
                    
        st.markdown("---")
        if st.button("⬅️ Kembali ke Menu Utama"):
            st.session_state.page = 'home'
            if 'page' in st.query_params:
                st.query_params.clear()
            st.rerun()
    else:
        # Panggil fungsi yang sesuai dari dictionary
        if st.session_state.laporan_view in menu_actions:
            menu_actions[st.session_state.laporan_view]()

# Untuk menjalankan file ini, Anda bisa panggil fungsi render() dari script utama Anda
if __name__ == '__main__':
    render()