# modules/pembayaran.py
from urllib.parse import quote
import streamlit as st
import pandas as pd
from utils import db_functions as db

def show_jenis_pembayaran():
    st.subheader("Master Data Pembayaran")
    if st.button("⬅️ Kembali ke Menu Pembayaran"):
        st.session_state.pembayaran_view = 'menu'
        st.rerun()
    st.markdown("---")
    with st.form("form_tambah_pos", clear_on_submit=True):
        nama_pos = st.text_input("Nama Pembayaran (Contoh: SPP Juli 2025, Uang Gedung 2025)")
        tipe = st.selectbox("Tipe Pembayaran", ["Bulanan", "Bebas", "Sukarela"])
        if st.form_submit_button("Tambah Jenis Pembayaran"):
            if nama_pos and tipe:
                conn = db.create_connection()
                db.tambah_pos_pembayaran(conn, nama_pos, tipe)
                conn.close()
                st.success(f"Jenis pembayaran '{nama_pos}' berhasil ditambahkan.")
                st.rerun()
            else:
                st.warning("Nama dan Tipe Pembayaran tidak boleh kosong.")
    st.markdown("---")
    conn = db.create_connection()
    list_pos = db.get_semua_pos_pembayaran(conn)
    conn.close()
    if list_pos:
        df_pos = pd.DataFrame(list_pos, columns=['ID', 'Nama Pembayaran', 'Tipe'])
        st.dataframe(df_pos, use_container_width=True)
        st.markdown("---")
        st.subheader("Edit atau Hapus Jenis Pembayaran")
        pos_dict = {f"{nama} ({tipe})": id_pos for id_pos, nama, tipe in list_pos}
        selected_pos_nama = st.selectbox("Pilih item untuk diubah/dihapus", options=pos_dict.keys())
        id_pos_terpilih = pos_dict.get(selected_pos_nama)
        if id_pos_terpilih:
            selected_details = next(item for item in list_pos if item[0] == id_pos_terpilih)
            with st.form(f"form_edit_pos_{id_pos_terpilih}"):
                st.write(f"**Edit: {selected_pos_nama}**")
                edit_nama = st.text_input("Nama Pembayaran Baru", value=selected_details[1])
                tipe_options = ["Bulanan", "Bebas", "Sukarela"]
                tipe_index = tipe_options.index(selected_details[2]) if selected_details[2] in tipe_options else 0
                edit_tipe = st.selectbox("Tipe Pembayaran Baru", options=tipe_options, index=tipe_index)
                if st.form_submit_button("Simpan Perubahan"):
                    conn = db.create_connection()
                    db.update_pos_pembayaran(conn, id_pos_terpilih, edit_nama, edit_tipe)
                    conn.close()
                    st.success("Data berhasil diperbarui!")
                    st.rerun()
            if st.button(f"❌ Hapus: {selected_pos_nama}", type="primary"):
                conn = db.create_connection()
                db.hapus_pos_pembayaran(conn, id_pos_terpilih)
                conn.close()
                st.warning(f"Item '{selected_pos_nama}' telah dihapus.")
                st.rerun()

def show_tagihan_siswa():
    st.subheader("🧾 Buat dan Lihat Tagihan Siswa")
    
    if st.button("⬅️ Kembali ke Menu Pembayaran"):
        st.session_state.pembayaran_view = 'menu'
        st.rerun()
    st.markdown("---")
    
    # --- Form untuk Buat Tagihan Satu Kelas ---
    with st.expander("Buat Tagihan untuk Satu Kelas", expanded=False):
        conn = db.create_connection()
        list_kelas = db.get_semua_kelas(conn)
        list_pos = db.get_semua_pos_pembayaran(conn)
        conn.close()

        if not list_kelas or not list_pos:
            st.warning("Data Kelas atau Jenis Pembayaran belum ada. Silakan lengkapi terlebih dahulu.")
            return

        kelas_dict = {f"{nama} ({tahun})": id_kelas for id_kelas, nama, tahun in list_kelas}
        pos_dict = {f"{nama} ({tipe})": id_pos for id_pos, nama, tipe in list_pos}

        with st.form("form_buat_tagihan_kelas"):
            col1, col2 = st.columns(2)
            with col1:
                selected_kelas_nama = st.selectbox("Pilih Kelas", options=kelas_dict.keys())
                nominal = st.number_input("Nominal Tagihan", min_value=0)
            with col2:
                selected_pos_nama = st.selectbox("Pilih Jenis Pembayaran", options=pos_dict.keys())
                bulan = st.text_input("Bulan (opsional, misal: Juli)")
            
            if st.form_submit_button("Buat Tagihan Sekarang"):
                id_kelas = kelas_dict[selected_kelas_nama]
                id_pos = pos_dict[selected_pos_nama]
                
                conn = db.create_connection()
                jumlah_siswa = db.buat_tagihan_satu_kelas(conn, id_kelas, id_pos, nominal, bulan if bulan else None)
                conn.close()
                
                st.success(f"Berhasil membuat tagihan '{selected_pos_nama}' untuk {jumlah_siswa} siswa di kelas {selected_kelas_nama}.")

    # --- Tampilan untuk Melihat Tagihan per Siswa ---
    st.markdown("---")
    st.header("Lihat Tagihan per Siswa")
    
    # --- (BARU) Widget Filter Siswa ---
    conn = db.create_connection()
    list_kelas = db.get_semua_kelas(conn)
    conn.close()

    kelas_dict_filter = {f"{nama} ({tahun})": id_kelas for id_kelas, nama, tahun in list_kelas}
    pilihan_kelas_filter = ["Semua Kelas"] + list(kelas_dict_filter.keys())

    col1, col2 = st.columns([2, 3])
    with col1:
        selected_kelas_filter_nama = st.selectbox("Filter per Kelas", options=pilihan_kelas_filter, key="filter_kelas_tagihan")
    with col2:
        search_term = st.text_input("Cari Nama atau NIS Siswa", placeholder="Ketik di sini...", key="search_tagihan")

    id_kelas_filter = None
    if selected_kelas_filter_nama != "Semua Kelas":
        id_kelas_filter = kelas_dict_filter[selected_kelas_filter_nama]

    conn = db.create_connection()
    list_siswa_db = db.get_filtered_siswa_detailed(conn, kelas_id=id_kelas_filter, search_term=search_term)
    conn.close()
    
    if not list_siswa_db:
        st.warning("Tidak ada data siswa yang cocok dengan filter Anda.")
        return
        
    pilihan_siswa_dict = {f"{nama} ({nis})": nis for nis, _, _, nama, _, _, _, _ in list_siswa_db}
    siswa_terpilih_nama = st.selectbox("Pilih Siswa untuk melihat tagihan:", options=pilihan_siswa_dict.keys())

    if siswa_terpilih_nama:
        nis_terpilih = pilihan_siswa_dict[siswa_terpilih_nama]
        st.write(f"**Menampilkan tagihan untuk: {siswa_terpilih_nama}**")
        
        conn = db.create_connection()
        tagihan_siswa = db.get_tagihan_by_siswa(conn, nis_terpilih)
        conn.close()
        
        if tagihan_siswa:
            df_tagihan = pd.DataFrame(tagihan_siswa, columns=['ID Tagihan', 'Nama Pembayaran', 'Bulan', 'Total Tagihan', 'Sisa Tagihan', 'Status'])
            st.dataframe(df_tagihan, use_container_width=True)
        else:
            st.info("Siswa ini belum memiliki tagihan.")

def show_transaksi_pembayaran():
    st.subheader("💳 Transaksi Pembayaran")
    
    if st.button("⬅️ Kembali ke Menu Pembayaran"):
        st.session_state.pembayaran_view = 'menu'
        st.rerun()
    st.markdown("---")

    # --- (BARU) Filter untuk memilih siswa ---
    st.write("**Pilih Siswa**")
    conn = db.create_connection()
    list_kelas = db.get_semua_kelas(conn)
    conn.close()

    kelas_dict_filter = {f"{nama} ({tahun})": id_kelas for id_kelas, nama, tahun in list_kelas}
    pilihan_kelas_filter = ["Semua Kelas"] + list(kelas_dict_filter.keys())

    col1, col2 = st.columns([2, 3])
    with col1:
        selected_kelas_filter_nama = st.selectbox("Filter per Kelas", options=pilihan_kelas_filter, key="filter_kelas_transaksi")
    with col2:
        search_term = st.text_input("Cari Nama atau NIS Siswa", placeholder="Ketik di sini...", key="search_transaksi")

    id_kelas_filter = None
    if selected_kelas_filter_nama != "Semua Kelas":
        id_kelas_filter = kelas_dict_filter[selected_kelas_filter_nama]

    conn = db.create_connection()
    list_siswa_db = db.get_filtered_siswa_detailed(conn, kelas_id=id_kelas_filter, search_term=search_term)
    conn.close()
    
    if not list_siswa_db:
        st.warning("Tidak ada data siswa yang cocok dengan filter Anda.")
        return
        
    pilihan_siswa_dict = {f"{nama} ({nis})": nis for nis, _, _, nama, _, _, _, _ in list_siswa_db}
    siswa_terpilih_nama = st.selectbox("Pilih Siswa untuk melakukan pembayaran:", options=pilihan_siswa_dict.keys())

    # --- Lanjutan setelah siswa dipilih ---
    if siswa_terpilih_nama:
        nis_terpilih = pilihan_siswa_dict[siswa_terpilih_nama]
        
        conn = db.create_connection()
        tagihan_belum_lunas = db.get_tagihan_by_siswa(conn, nis_terpilih)
        conn.close()
        
        if not tagihan_belum_lunas:
            st.info(f"Siswa {siswa_terpilih_nama} tidak memiliki tagihan yang belum lunas.")
            return

        st.markdown("---")
        st.write(f"**Daftar Tagihan Belum Lunas untuk {siswa_terpilih_nama}:**")
        
        with st.form("form_pembayaran"):
            pembayaran_dipilih = []
            total_akan_dibayar = 0
            
            for tagihan in tagihan_belum_lunas:
                id_tagihan, nama_pos, bulan, _, sisa_tagihan, _ = tagihan
                label = f"{nama_pos} {bulan if bulan else ''} - Sisa: Rp {sisa_tagihan:,.0f}"
                
                col1, col2 = st.columns([3, 2])
                with col1:
                    pilih = st.checkbox(label, key=f"pilih_{id_tagihan}")
                with col2:
                    if pilih:
                        jumlah_bayar = st.number_input("Jumlah Bayar", min_value=0.0, max_value=float(sisa_tagihan), value=float(sisa_tagihan), step=1000.0, key=f"bayar_{id_tagihan}", label_visibility="collapsed")
                        pembayaran_dipilih.append({'id_tagihan': id_tagihan, 'jumlah_bayar': jumlah_bayar, 'label': label})
                        total_akan_dibayar += jumlah_bayar

            st.markdown("---")
            st.metric("Total Akan Dibayar", f"Rp {total_akan_dibayar:,.0f}")

            if st.form_submit_button("Proses Pembayaran"):
                if not pembayaran_dipilih:
                    st.error("Tidak ada tagihan yang dipilih untuk dibayar.")
                else:
                    list_untuk_db = [(item['id_tagihan'], item['jumlah_bayar']) for item in pembayaran_dipilih]
                    petugas = st.session_state.get('username', 'admin')
                    
                    conn = db.create_connection()
                    id_transaksi = db.proses_pembayaran(conn, nis_terpilih, petugas, list_untuk_db)
                    conn.close()
                    
                    st.success(f"Pembayaran berhasil diproses! No. Transaksi: {id_transaksi}")
                    st.balloons()
                    
                    with st.expander("Lihat Detail Pembayaran yang Baru Saja Dilakukan"):
                        for item in pembayaran_dipilih:
                            st.write(f"- {item['label'].split(' - ')[0]}: Rp {item['jumlah_bayar']:,.0f}")
                        st.metric("Total Dibayar", f"Rp {total_akan_dibayar:,.0f}")


def show_history_transaksi():
    st.subheader("⏳ History Transaksi Pembayaran")
    
    if st.button("⬅️ Kembali ke Menu Pembayaran"):
        st.session_state.pembayaran_view = 'menu'
        st.rerun()
    st.markdown("---")

    # --- (BARU) Kotak Pencarian ---
    search_term = st.text_input("Cari Nama Siswa, NIS, atau No. Transaksi", placeholder="Ketik di sini...")

    conn = db.create_connection()
    semua_transaksi = db.get_semua_transaksi(conn, search_term=search_term)
    conn.close()

    if not semua_transaksi:
        st.info("Tidak ada data transaksi yang cocok dengan pencarian Anda.")
        return

    st.write(f"**Menampilkan {len(semua_transaksi)} Transaksi**")
    df_transaksi = pd.DataFrame(semua_transaksi, columns=['No. Transaksi', 'Tanggal', 'NIS', 'Nama Siswa', 'Total Bayar', 'Petugas'])
    st.dataframe(df_transaksi, use_container_width=True)
    
    st.markdown("---")
    
    # Hanya tampilkan detail jika ada hasil pencarian
    if semua_transaksi:
        st.write("**Lihat Detail Transaksi**")
        pilihan_transaksi_dict = {f"No. {tr[0]} - {tr[3]} - Rp {tr[4]:,.0f}": tr[0] for tr in semua_transaksi}
        transaksi_terpilih_nama = st.selectbox("Pilih transaksi untuk melihat detail:", options=pilihan_transaksi_dict.keys())
        
        if transaksi_terpilih_nama:
            id_transaksi_terpilih = pilihan_transaksi_dict[transaksi_terpilih_nama]
            
            conn = db.create_connection()
            detail_transaksi = db.get_detail_by_transaksi(conn, id_transaksi_terpilih)
            conn.close()
            
            if detail_transaksi:
                df_detail = pd.DataFrame(detail_transaksi, columns=['Item Pembayaran', 'Bulan', 'Jumlah Dibayar'])
                st.table(df_detail)
            else:
                st.warning("Detail untuk transaksi ini tidak ditemukan.")

def show_broadcast_tagihan():
    st.subheader("📡 Broadcast Tagihan ke Orang Tua")
    
    if st.button("⬅️ Kembali ke Menu Pembayaran"):
        st.session_state.pembayaran_view = 'menu'
        st.rerun()
    st.markdown("---")
    
    st.info("Pilih jenis pembayaran, lalu klik 'Lihat Daftar Tagihan'. Klik link di kolom 'Link Kirim' untuk membuka WhatsApp.")

    conn = db.create_connection()
    list_pos = db.get_semua_pos_pembayaran(conn)
    conn.close()

    if not list_pos:
        st.warning("Jenis Pembayaran belum ada. Silakan lengkapi terlebih dahulu.")
        return

    pos_dict = {f"{nama} ({tipe})": id_pos for id_pos, nama, tipe in list_pos}
    selected_pos_nama = st.selectbox("Pilih Item Pembayaran yang akan di-broadcast", options=pos_dict.keys())
    
    if st.button("Lihat Daftar Tagihan"):
        id_pos = pos_dict[selected_pos_nama]
        conn = db.create_connection()
        data_broadcast = db.get_tagihan_by_pos(conn, id_pos)
        conn.close()

        if not data_broadcast:
            st.info(f"Tidak ada tagihan belum lunas untuk '{selected_pos_nama}' yang memiliki No. WA.")
            return

        st.write(f"Ditemukan {len(data_broadcast)} tagihan yang siap di-broadcast:")
        
        # Siapkan data untuk ditampilkan
        display_data = []
        for nama, no_wa, item, sisa in data_broadcast:
            # Format pesan
            pesan = f"Yth. Orang Tua dari {nama}, kami informasikan tagihan {item} sebesar Rp {sisa:,.0f} belum lunas. Terima kasih."
            # Ubah pesan ke format URL
            pesan_url = quote(pesan)
            # Buat link Click to Chat
            link = f"https://wa.me/{no_wa}?text={pesan_url}"
            display_data.append([nama, no_wa, f"Kirim Pesan", link])
            
        df_broadcast = pd.DataFrame(display_data, columns=["Nama Siswa", "No. WA Ortu", "Aksi", "Link"])

        # Menampilkan tabel dengan link yang bisa diklik
        st.dataframe(
            df_broadcast,
            column_config={
                "Link": st.column_config.LinkColumn(
                    "Link Kirim",
                    help="Klik untuk membuka WhatsApp",
                    display_text="Buka WhatsApp"
                )
            },
            hide_index=True,
            use_container_width=True
        )
def render():
    st.title("💵 Modul Pembayaran")
    if 'pembayaran_view' not in st.session_state:
        st.session_state.pembayaran_view = 'menu'
    if st.session_state.pembayaran_view == 'menu':
        if st.button("⬅️ Kembali ke Menu Utama"):
            st.session_state.page = 'home'
            st.rerun()
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💰 Jenis Pembayaran"):
                st.session_state.pembayaran_view = 'jenis_pembayaran'
                st.rerun()
            if st.button("🧾 Tagihan Siswa"):
                st.session_state.pembayaran_view = 'tagihan_siswa'
                st.rerun()
        with col2:
            if st.button("💳 Transaksi Pembayaran"):
                st.session_state.pembayaran_view = 'transaksi_pembayaran'
                st.rerun()
            if st.button("⏳ History Transaksi"):
                st.session_state.pembayaran_view = 'history_transaksi'
                st.rerun()
        with col3:
            if st.button("📡 Broadcast Tagihan"):
                st.session_state.pembayaran_view = 'broadcast_tagihan'
                st.rerun()
    elif st.session_state.pembayaran_view == 'jenis_pembayaran':
        show_jenis_pembayaran()
    elif st.session_state.pembayaran_view == 'tagihan_siswa':
        show_tagihan_siswa()
    elif st.session_state.pembayaran_view == 'transaksi_pembayaran':
        show_transaksi_pembayaran()
    elif st.session_state.pembayaran_view == 'history_transaksi':
        show_history_transaksi()
    elif st.session_state.pembayaran_view == 'broadcast_tagihan':
        show_broadcast_tagihan()