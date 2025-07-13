import streamlit as st
import pandas as pd
from utils import db_functions as db
from datetime import datetime, timedelta
import calendar

# --- Fungsi Terpusat ---
def render_filter_widgets(show_date_range=False):
    """Fungsi terpusat untuk menampilkan widget filter."""
    st.write("**Filter Laporan**")
    
    conn = db.create_connection()
    list_kelas = db.get_semua_kelas(conn)
    conn.close()
    
    kelas_dict = {f"{nama} ({tahun})": id_kelas for id_kelas, nama, tahun in list_kelas}
    pilihan_kelas = ["Semua Kelas"] + list(kelas_dict.keys())
    
    tgl_mulai, tgl_sampai = None, None
    if show_date_range:
        col1, col2 = st.columns(2)
        tgl_mulai = col1.date_input("Tanggal Mulai")
        tgl_sampai = col2.date_input("Tanggal Sampai")

    col_filter1, col_filter2 = st.columns(2)
    selected_kelas_nama = col_filter1.selectbox("Filter per Kelas", options=pilihan_kelas, key="filter_kelas_rekap")
    search_term = col_filter2.text_input("Cari Nama/NIS", key="search_rekap")
    
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
    st.write(f"**{title}**")
    st.dataframe(df, use_container_width=True)
    
    total_pemasukan = df['Total Pemasukan (Rp)'].sum()
    st.metric("Grand Total Pemasukan Sesuai Filter", f"Rp {total_pemasukan:,.0f}")

# --- Halaman untuk Setiap Jenis Rekap ---
def show_rekap_per_hari():
    st.subheader("Rekap Pembayaran Harian")
    tanggal_laporan = st.date_input("Pilih Tanggal")
    _, _, id_kelas_filter, search_term = render_filter_widgets()
    if st.button("Tampilkan Rekap", type="primary"):
        display_rekap_data(f"Rekap Pemasukan Tanggal: {tanggal_laporan.strftime('%d-%m-%Y')}", tanggal_laporan, tanggal_laporan, id_kelas_filter, search_term)

def show_rekap_per_periode(jenis_rekap):
    st.subheader(f"Rekap Pembayaran {jenis_rekap}")
    tgl_mulai, tgl_sampai, id_kelas_filter, search_term = render_filter_widgets(show_date_range=True)
    if st.button("Tampilkan Rekap", type="primary"):
        if not tgl_mulai or not tgl_sampai:
            st.error("Tanggal mulai dan tanggal sampai harus diisi.")
            return
        display_rekap_data(f"Rekap Pemasukan Periode: {tgl_mulai.strftime('%d-%m-%Y')} s/d {tgl_sampai.strftime('%d-%m-%Y')}", tgl_mulai, tgl_sampai, id_kelas_filter, search_term)

# --- Halaman Utama untuk Rekap Pembayaran ---
def show_rekap_pembayaran():
    st.subheader("Rekapitulasi Pembayaran")
    if st.button("⬅️ Kembali ke Menu Laporan"):
        st.session_state.laporan_view = 'menu'
        st.rerun()
    st.markdown("---")

    pilihan_rekap = {
        "Perhari": show_rekap_per_hari,
        "Perminggu": lambda: show_rekap_per_periode("Perminggu"),
        "Perbulan": lambda: show_rekap_per_periode("Perbulan"),
        "Pertriwulan": lambda: show_rekap_per_periode("Pertriwulan"),
        "Persemester": lambda: show_rekap_per_periode("Persemester"),
        "Pertahun": lambda: show_rekap_per_periode("Pertahun"),
    }
    
    jenis_rekap = st.selectbox("Pilih Jenis Rekapitulasi", options=pilihan_rekap.keys())
    
    # Panggil fungsi yang sesuai dari dictionary
    pilihan_rekap[jenis_rekap]()

# --- Semua fungsi laporan pembayaran lainnya (tidak berubah) ---
# ... (Salin semua fungsi show_lap_per_* dan show_laporan_tunggakan dari kode sebelumnya di sini) ...
def show_laporan_tunggakan():
    st.subheader("Laporan Tunggakan Siswa")
    conn = db.create_connection()
    list_kelas = db.get_semua_kelas(conn)
    conn.close()
    kelas_dict = {f"{nama} ({tahun})": id_kelas for id_kelas, nama, tahun in list_kelas}
    pilihan_kelas = ["Semua Kelas"] + list(kelas_dict.keys())
    col1, col2 = st.columns(2)
    selected_kelas_nama = col1.selectbox("Filter per Kelas", options=pilihan_kelas)
    search_term = col2.text_input("Cari Nama atau NIS Siswa", placeholder="Ketik di sini...")
    if st.button("Tampilkan Tunggakan", type="primary"):
        id_kelas_filter = None
        if selected_kelas_nama != "Semua Kelas":
            id_kelas_filter = kelas_dict[selected_kelas_nama]
        conn = db.create_connection()
        data_tunggakan = db.get_semua_tunggakan(conn, kelas_id=id_kelas_filter, search_term=search_term)
        conn.close()
        if not data_tunggakan:
            st.info("Tidak ada data tunggakan yang ditemukan untuk filter ini.")
            return
        df = pd.DataFrame(data_tunggakan, columns=['NIS', 'Nama Siswa', 'Kelas', 'Item Pembayaran', 'Bulan', 'Tunggakan'])
        total_tunggakan_keseluruhan = 0
        for (nis, nama, kelas), group in df.groupby(['NIS', 'Nama Siswa', 'Kelas']):
            st.markdown(f"---")
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
    st.subheader("Laporan Pembayaran")
    if st.button("⬅️ Kembali ke Menu Laporan"):
        st.session_state.laporan_view = 'menu'
        st.rerun()
    st.markdown("---")
    
    jenis_laporan = st.selectbox("Pilih Jenis Laporan Pembayaran", ["Laporan Pembayaran Per Hari", "Laporan Pembayaran Per Minggu", "Laporan Pembayaran Per Bulan", "Laporan Pembayaran Per Triwulan", "Laporan Pembayaran Per Semester", "Laporan Pembayaran Per Tahun", "Laporan Tunggakan"])
    
    if jenis_laporan == "Laporan Tunggakan": show_laporan_tunggakan()
    elif jenis_laporan == "Laporan Pembayaran Per Hari": show_lap_per_hari()
    elif jenis_laporan == "Laporan Pembayaran Per Minggu": show_lap_per_minggu()
    elif jenis_laporan == "Laporan Pembayaran Per Bulan": show_lap_per_bulan()
    elif jenis_laporan == "Laporan Pembayaran Per Triwulan": show_lap_per_triwulan()
    elif jenis_laporan == "Laporan Pembayaran Per Semester": show_lap_per_semester()
    elif jenis_laporan == "Laporan Pembayaran Per Tahun": show_lap_per_tahun()

# --- Fungsi Render Utama ---
def render():
    st.title("📄 Modul Laporan")
    if 'laporan_view' not in st.session_state:
        st.session_state.laporan_view = 'menu'
    if st.session_state.laporan_view == 'menu':
        if st.button("⬅️ Kembali ke Menu Utama"):
            st.session_state.page = 'home'
            st.rerun()
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(" Laporan Pembayaran"):
                st.session_state.laporan_view = 'laporan_pembayaran'
                st.rerun()
        with col2:
            if st.button(" Rekap Pembayaran"):
                st.session_state.laporan_view = 'rekap_pembayaran'
                st.rerun()
    elif st.session_state.laporan_view == 'laporan_pembayaran':
        show_laporan_pembayaran()
    elif st.session_state.laporan_view == 'rekap_pembayaran':
        show_rekap_pembayaran()