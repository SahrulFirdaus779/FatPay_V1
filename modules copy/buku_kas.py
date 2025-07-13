import streamlit as st
import pandas as pd
from utils import db_functions as db
from datetime import datetime

def show_buku_kas_umum():
    st.subheader("Laporan Buku Kas Umum")
    if st.button("⬅️ Kembali ke Menu Buku Kas"):
        st.session_state.buku_kas_view = 'menu'
        st.rerun()
    st.markdown("---")
    
    st.write("**Filter Laporan**")

    conn = db.create_connection()
    list_pos = db.get_semua_pos_pembayaran(conn)
    conn.close()
    
    pos_dict = {nama: id_pos for id_pos, nama, _ in list_pos}
    pilihan_pos = ["Semua"] + list(pos_dict.keys())
    
    col1, col2, col3 = st.columns(3)
    tgl_mulai = col1.date_input("Tanggal Mulai", value=datetime.now().date())
    tgl_sampai = col2.date_input("Tanggal Sampai", value=datetime.now().date())
    selected_pos_nama = col3.selectbox("Filter Jenis POS", options=pilihan_pos)

    if st.button("Tampilkan Laporan", type="primary"):
        id_pos_filter = None
        if selected_pos_nama != "Semua":
            id_pos_filter = pos_dict[selected_pos_nama]
            
        conn = db.create_connection()
        laporan_data = db.get_laporan_kas_umum(conn, tgl_mulai, tgl_sampai, id_pos=id_pos_filter)
        conn.close()
        
        if not laporan_data:
            st.warning("Tidak ada data transaksi pada periode atau filter yang dipilih.")
            return
            
        df = pd.DataFrame(laporan_data, columns=['No. Bukti', 'Tanggal', 'Jenis POS', 'Uraian', 'Penerimaan (Rp)'])
        
        df['Pengeluaran (Rp)'] = 0 
        df['Saldo'] = df['Penerimaan (Rp)'].cumsum()
        
        st.write(f"**Laporan Kas Umum Periode {tgl_mulai.strftime('%d-%m-%Y')} s/d {tgl_sampai.strftime('%d-%m-%Y')}**")
        st.dataframe(df[['Tanggal', 'Uraian', 'Penerimaan (Rp)', 'Pengeluaran (Rp)', 'Saldo']], use_container_width=True)
        
        total_pemasukan = df['Penerimaan (Rp)'].sum()
        saldo_akhir = total_pemasukan
        
        st.markdown("---")
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        summary_col1.metric("Total Pemasukan", f"Rp {total_pemasukan:,.0f}")
        summary_col2.metric("Total Pengeluaran", "Rp 0")
        summary_col3.metric("SALDO AKHIR", f"Rp {saldo_akhir:,.0f}")

def show_rekap_saldo():
    st.subheader("Rekap Saldo per Jenis POS")
    if st.button("⬅️ Kembali ke Menu Buku Kas"):
        st.session_state.buku_kas_view = 'menu'
        st.rerun()
    st.markdown("---")

    conn = db.create_connection()
    rekap_data = db.get_rekap_saldo_per_pos(conn)
    conn.close()

    if not rekap_data:
        st.info("Belum ada data pembayaran yang tercatat untuk direkap.")
        return
        
    df = pd.DataFrame(rekap_data, columns=['Jenis POS', 'Saldo'])
    st.dataframe(df, use_container_width=True)

    total_saldo = df['Saldo'].sum()
    st.metric("Total Saldo dari Semua POS", f"Rp {total_saldo:,.0f}")


def render():
    st.title("📚 Modul Buku Kas")

    if 'buku_kas_view' not in st.session_state:
        st.session_state.buku_kas_view = 'menu'

    if st.session_state.buku_kas_view == 'menu':
        if st.button("⬅️ Kembali ke Menu Utama"):
            st.session_state.page = 'home'
            st.rerun()
        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Buku Kas Umum"):
                st.session_state.buku_kas_view = 'buku_kas_umum'
                st.rerun()
        with col2:
            if st.button("Rekap Saldo per POS"):
                st.session_state.buku_kas_view = 'rekap_saldo'
                st.rerun()
    
    elif st.session_state.buku_kas_view == 'buku_kas_umum':
        show_buku_kas_umum()
    elif st.session_state.buku_kas_view == 'rekap_saldo':
        show_rekap_saldo()