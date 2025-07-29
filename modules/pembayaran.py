import streamlit as st
import pandas as pd
from utils import db_functions as db
from urllib.parse import quote

# --- FUNGSI BANTUAN ---
def format_status_pembayaran(status):
    """Mengubah teks status pembayaran menjadi badge HTML berwarna."""
    if status == "Lunas":
        bg_color, text_color = "#DFF2BF", "#4F8A10"
    elif status == "Belum Lunas":
        bg_color, text_color = "#FFC0CB", "#A30E2B"
    else: # Sebagian
        bg_color, text_color = "#F7F5A8", "#877B0F"
    
    badge_style = f"background-color: {bg_color}; color: {text_color}; padding: 5px 12px; border-radius: 15px; text-align: center; font-weight: 600; font-size: 12px; display: inline-block;"
    return f'<div style="{badge_style}">{status}</div>'

# --- FUNGSI SUB-HALAMAN (LENGKAP DENGAN PERBAIKAN) ---

def show_jenis_pembayaran():
    st.subheader("Master Data Pembayaran")

    st.markdown("""
    <style>
        /* Memberi warna latar pada baris genap */
        div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"]:nth-of-type(even) {
            background-color: #FFF7E8; /* Warna abu-abu sangat muda */
            border-radius: 8px;
        }

        /* Memberi sedikit padding pada baris ganjil agar sejajar */
        div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"]:nth-of-type(odd) {
        }

        /* Mengatur header agar sedikit berbeda */
        div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"]:first-of-type {
            background-color: transparent;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- Tombol untuk memunculkan dialog Tambah Data ---
    if st.button("➕ Tambah Jenis Pembayaran Baru"):
        st.session_state.show_add_dialog = True

    # --- Dialog untuk Tambah Data ---
    if st.session_state.get("show_add_dialog", False):
        # PERBAIKAN: Menghapus 'with' dari st.dialog
        st.dialog("Tambah Jenis Pembayaran")
        with st.form("form_tambah_pos"):
            nama_pos = st.text_input("Nama Pembayaran (Contoh: SPP Juli 2025)")
            tipe = st.selectbox("Tipe Pembayaran", ["Bulanan", "Bebas", "Sukarela"])
            
            submitted = st.form_submit_button("Simpan")
            if submitted:
                if nama_pos and tipe:
                    with st.spinner("Menyimpan..."):
                        conn = db.create_connection()
                        db.tambah_pos_pembayaran(conn, nama_pos, tipe)
                        conn.close()
                    st.toast(f"✅ Jenis pembayaran '{nama_pos}' berhasil ditambahkan.")
                    st.session_state.show_add_dialog = False
                    st.rerun()
                else:
                    st.error("Nama dan Tipe Pembayaran tidak boleh kosong.")
    
    st.markdown("---")

    # --- Menampilkan Daftar Data ---
    with st.spinner("Memuat data..."):
        conn = db.create_connection()
        list_pos = db.get_semua_pos_pembayaran(conn)
        conn.close()

    if not list_pos:
        st.info("Belum ada data jenis pembayaran. Silakan tambahkan data baru.")
        return

    # --- Tampilan Tabel dengan Tombol Aksi ---
    col1, col2, col3 = st.columns([4, 2, 2])
    col1.markdown("**Nama Pembayaran**")
    col2.markdown("**Tipe**")
    col3.markdown("**Aksi**")

    for id_pos, nama, tipe in list_pos:
        col1_data, col2_data, col3_data = st.columns([4, 2, 2])
        with col1_data:
            st.write(nama)
        with col2_data:
            st.write(tipe)
        with col3_data:
            # Membuat dua kolom khusus untuk tombol Edit dan Hapus
            aksi_col1, aksi_col2 = st.columns(2)
            with aksi_col1:
                if st.button("✏️", key=f"edit_{id_pos}", help="Edit item ini", use_container_width=True):
                    st.session_state.edit_id = id_pos
                    st.session_state.edit_nama = nama
                    st.session_state.edit_tipe = tipe
            with aksi_col2:
                if st.button("🗑️", key=f"delete_{id_pos}", help="Hapus item ini", use_container_width=True):
                    st.session_state.delete_id = id_pos
                    st.session_state.delete_nama = nama

    # --- Logika untuk Dialog Edit ---
    if 'edit_id' in st.session_state:
        # PERBAIKAN: Menghapus 'with' dari st.dialog
        st.dialog("Edit Jenis Pembayaran")
        with st.form("form_edit_pos"):
            st.write(f"Anda sedang mengedit: **{st.session_state.edit_nama}**")
            nama_baru = st.text_input("Nama Pembayaran Baru", value=st.session_state.edit_nama)
            
            tipe_options = ["Bulanan", "Bebas", "Sukarela"]
            try:
                default_index = tipe_options.index(st.session_state.edit_tipe)
            except ValueError:
                default_index = 0
            tipe_baru = st.selectbox("Tipe Pembayaran Baru", options=tipe_options, index=default_index)

            col_save, col_cancel = st.columns(2)
            if col_save.form_submit_button("Simpan Perubahan", use_container_width=True):
                with st.spinner("Memperbarui..."):
                    conn = db.create_connection()
                    db.update_pos_pembayaran(conn, st.session_state.edit_id, nama_baru, tipe_baru)
                    conn.close()
                st.toast("✅ Data berhasil diperbarui!")
                del st.session_state.edit_id
                st.rerun()
            
            if col_cancel.form_submit_button("Batal", type="secondary", use_container_width=True):
                del st.session_state.edit_id
                st.rerun()

# --- Logika untuk Dialog Konfirmasi Hapus ---
    if 'delete_id' in st.session_state:
        st.dialog("Konfirmasi Hapus")
        st.warning(f"Anda yakin ingin menghapus item '{st.session_state.delete_nama}'?")
        
        conn = db.create_connection()
        is_in_use = db.is_pos_pembayaran_in_use(conn, st.session_state.delete_id)
        conn.close()

        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Ya, Hapus", type="primary", use_container_width=True, disabled=is_in_use):
                with st.spinner("Menghapus..."):
                    conn = db.create_connection()
                    db.hapus_pos_pembayaran(conn, st.session_state.delete_id)
                    conn.close()
                st.toast(f"🗑️ Item '{st.session_state.delete_nama}' telah dihapus.")
                del st.session_state.delete_id
                st.rerun()
        
        with col_no:
            if st.button("Batal", use_container_width=True):
                del st.session_state.delete_id
                st.rerun()
        
        if is_in_use:
            st.error("Gagal! Jenis pembayaran ini sudah digunakan dalam tagihan.")

# Ganti fungsi Anda dengan versi alternatif ini jika tidak ingin upgrade

# Ganti fungsi lama di pembayaran.py dengan versi final yang sudah benar ini

def show_transaksi_pembayaran():
    st.subheader("💳 Transaksi Pembayaran")

    # --- Kode CSS (tidak perlu diubah) ---
    st.markdown("""
    <style>
        .payment-header { background-color: #0d6efd; color: white; padding: 10px; border-radius: 7px 7px 0 0; font-weight: 600; }
        .payment-row { border: 1px solid #dee2e6; border-top: none; padding: 10px; display: flex; align-items: center; min-height: 55px; }
        .payment-row:last-of-type { border-radius: 0 0 7px 7px; }
        .receipt-box { border: 1px solid #198754; border-radius: 8px; padding: 20px; background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

    search_col, form_col = st.columns([1, 2], gap="large")

    # --- Kolom Kiri: PENCARIAN SISWA ---
    with search_col:
        st.markdown("##### 1. Pilih Siswa")
        
        conn = db.create_connection()
        list_kelas = db.get_semua_kelas(conn)
        conn.close()
        
        kelas_dict = {"-- Pilih Kelas --": None}
        kelas_dict.update({f"{angkatan} - {nama}": id_kelas for id_kelas, angkatan, nama, _ in list_kelas})
        
        selected_kelas_nama = st.selectbox("Filter Kelas", options=kelas_dict.keys())
        id_kelas_filter = kelas_dict.get(selected_kelas_nama)

        search_term = st.text_input("Cari Nama Siswa atau NIS...", key="search_trx")
        
        with st.spinner("Memuat daftar siswa..."):
            conn = db.create_connection()
            list_siswa_db = db.get_filtered_siswa_detailed(conn, kelas_id=id_kelas_filter, search_term=search_term if search_term else None)
            conn.close()

        if not list_siswa_db:
            st.warning("Tidak ada siswa yang cocok dengan kriteria.")
        else:
            df_siswa = pd.DataFrame(list_siswa_db, columns=["NIS", "_", "_", "Nama Siswa", "_", "_", "_", "_", "_"])
            
            st.write("Klik pada baris untuk memilih siswa:")
            
            st.dataframe(
                df_siswa[["NIS", "Nama Siswa"]],
                key="student_selector",
                on_select="rerun",
                selection_mode="single-row",
                hide_index=True,
                use_container_width=True,
                height=400
            )
            
            selection = st.session_state.get("student_selector")
            if selection and selection["selection"]["rows"]:
                selected_index = selection["selection"]["rows"][0]
                selected_nis = df_siswa.iloc[selected_index]["NIS"]
                selected_nama = df_siswa.iloc[selected_index]["Nama Siswa"]

                if st.session_state.get("trx_nis") != selected_nis:
                    st.session_state.trx_nis = selected_nis
                    st.session_state.trx_nama = f"{selected_nama} ({selected_nis})"
                    if 'last_trx_id' in st.session_state: del st.session_state.last_trx_id
                    
    # --- Kolom Kanan: FORM PEMBAYARAN / KUITANSI ---
    with form_col:
        if 'last_trx_id' in st.session_state:
            with st.container(border=True):
                st.success("🎉 Pembayaran Berhasil!")
                st.markdown(f"##### Bukti Transaksi No: {st.session_state.last_trx_id}")
                st.markdown("---")
                # ... (kode untuk menampilkan detail kuitansi) ...
                st.markdown("---")
                st.metric("Total Dibayar", f"Rp {st.session_state.last_trx_total:,.0f}")

                # --- PERBAIKAN DI SINI ---
                if st.button("Lakukan Transaksi Lain"):
                    # Hapus semua state yang relevan untuk reset total
                    keys_to_delete = ['last_trx_id', 'last_trx_details', 'last_trx_total', 'trx_nis', 'trx_nama', 'student_selector']
                    for key in keys_to_delete:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

        elif 'trx_nis' in st.session_state:
            st.markdown(f"##### 2. Pembayaran untuk: **{st.session_state.trx_nama}**")
            conn = db.create_connection()
            tagihan_belum_lunas = [t for t in db.get_tagihan_by_siswa(conn, st.session_state.trx_nis) if t[5] != "Lunas"]
            conn.close()

            if not tagihan_belum_lunas:
                st.success(f"✅ Siswa ini tidak memiliki tagihan yang perlu dibayar.")
                # --- PERBAIKAN DI SINI ---
                if st.button("Pilih siswa lain"):
                    # Hapus state yang relevan untuk reset
                    keys_to_delete = ['trx_nis', 'trx_nama', 'student_selector']
                    for key in keys_to_delete:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
            else:
                with st.form("form_pembayaran"):
                    # ... (sisa kode form pembayaran tidak berubah) ...
                    pembayaran_dipilih = []
                    total_akan_dibayar = 0
                    header_cols = st.columns([4, 3])
                    header_cols[0].markdown('<div class="payment-header">Tagihan</div>', unsafe_allow_html=True)
                    header_cols[1].markdown('<div class="payment-header">Jumlah Bayar</div>', unsafe_allow_html=True)
                    for tagihan in tagihan_belum_lunas:
                        id_tagihan, nama_pos, bulan, _, sisa_tagihan, _ = tagihan
                        label = f"{nama_pos} {bulan if bulan else ''} (Sisa: Rp {sisa_tagihan:,.0f})"
                        row_cols = st.columns([4, 3])
                        with row_cols[0]:
                            st.markdown('<div class="payment-row">', unsafe_allow_html=True)
                            pilihan = st.checkbox(label, key=f"pilih_{id_tagihan}", value=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        with row_cols[1]:
                            st.markdown('<div class="payment-row">', unsafe_allow_html=True)
                            jumlah_bayar = st.number_input("Jml Bayar", min_value=0.0, max_value=float(sisa_tagihan), value=float(sisa_tagihan), key=f"bayar_{id_tagihan}", label_visibility="collapsed")
                            st.markdown('</div>', unsafe_allow_html=True)
                        if pilihan:
                            pembayaran_dipilih.append({'id_tagihan': id_tagihan, 'jumlah_bayar': jumlah_bayar, 'label': label})
                            total_akan_dibayar += jumlah_bayar
                    st.markdown("---")
                    st.metric("Total Akan Dibayar", f"Rp {total_akan_dibayar:,.0f}")
                    if st.form_submit_button("Proses Pembayaran", type="primary", use_container_width=True):
                        if pembayaran_dipilih:
                            # ... (sisa kode proses pembayaran tidak berubah) ...
                            list_db = [(item['id_tagihan'], item['jumlah_bayar']) for item in pembayaran_dipilih]
                            petugas = st.session_state.get('username', 'admin')
                            conn = db.create_connection()
                            id_transaksi = db.proses_pembayaran(conn, st.session_state.trx_nis, petugas, list_db)
                            conn.close()
                            if id_transaksi:
                                st.session_state.last_trx_id = id_transaksi
                                st.session_state.last_trx_details = pembayaran_dipilih
                                st.session_state.last_trx_total = total_akan_dibayar
                                del st.session_state.trx_nis
                                del st.session_state.trx_nama
                                st.rerun()
        else:
            st.info("Gunakan filter di sebelah kiri lalu klik sebuah baris pada tabel untuk memulai transaksi.")
# Ganti fungsi lama di pembayaran.py dengan yang ini

def show_tagihan_siswa():
    st.subheader("🧾 Manajemen Tagihan Siswa")

    # Menggunakan st.tabs untuk memisahkan fungsionalitas
    tab1, tab2 = st.tabs(["Buat Tagihan Massal", "Cari & Lihat Tagihan Siswa"])

    # --- TAB 1: BUAT TAGIHAN MASSAL ---
    with tab1:
        # Jika ada data tagihan yang baru dibuat, tampilkan dulu
        if 'last_created_bills' in st.session_state:
            st.success(f"✅ Berhasil membuat {len(st.session_state.last_created_bills)} tagihan baru.")
            df_new_bills = pd.DataFrame(st.session_state.last_created_bills, columns=['Nama Siswa', 'Jenis Tagihan', 'Bulan', 'Nominal'])
            st.dataframe(df_new_bills, use_container_width=True, hide_index=True)
            if st.button("➕ Buat Tagihan Lainnya"):
                del st.session_state.last_created_bills
                st.rerun()
        else:
            # Tampilkan form jika tidak ada data baru
            st.info("Gunakan menu ini untuk membuat tagihan yang sama untuk semua siswa dalam satu kelas/angkatan.")
            with st.form("form_buat_tagihan_kelas"):
                conn = db.create_connection()
                list_kelas = db.get_semua_kelas(conn)
                list_pos = db.get_semua_pos_pembayaran(conn)
                conn.close()

                if not list_kelas or not list_pos:
                    st.warning("Data Kelas atau Jenis Pembayaran belum ada.")
                    st.form_submit_button("Buat Tagihan", disabled=True)
                else:
                    kelas_dict = {f"{angkatan} - {nama} ({tahun})": id_kelas for id_kelas, angkatan, nama, tahun in list_kelas}
                    pos_dict = {f"{nama} ({tipe})": id_pos for id_pos, nama, tipe in list_pos}

                    col1, col2 = st.columns(2)
                    selected_kelas_nama = col1.selectbox("Pilih Kelas Tujuan", options=kelas_dict.keys())
                    nominal = col1.number_input("Nominal Tagihan", min_value=0, step=50000, format="%d")
                    selected_pos_nama = col2.selectbox("Pilih Jenis Pembayaran", options=pos_dict.keys())
                    bulan = col2.text_input("Bulan (opsional, misal: Juli 2025)")

                    if st.form_submit_button("🚀 Buat Tagihan Sekarang", type="primary"):
                        id_kelas, id_pos = kelas_dict[selected_kelas_nama], pos_dict[selected_pos_nama]
                        with st.spinner(f"Membuat tagihan untuk kelas {selected_kelas_nama}..."):
                            conn = db.create_connection()
                            db.buat_tagihan_satu_kelas(conn, id_kelas, id_pos, nominal, bulan if bulan else None)
                            # Ambil data yang baru dibuat untuk ditampilkan
                            just_created = db.get_tagihan_by_kelas_and_pos(conn, id_kelas, id_pos)
                            st.session_state.last_created_bills = just_created
                            conn.close()
                        st.rerun()

    # --- TAB 2: CARI & LIHAT TAGIHAN SISWA ---
    with tab2:
        conn = db.create_connection()
        list_kelas_filter = db.get_semua_kelas(conn)
        conn.close()
        kelas_dict_filter = {"Semua Kelas": None}
        kelas_dict_filter.update({f"{angkatan} - {nama} ({tahun})": id_kls for id_kls, angkatan, nama, tahun in list_kelas_filter})

        # --- Filter Section ---
        col1, col2 = st.columns([2, 3])
        selected_kelas_nama = col1.selectbox("Filter Berdasarkan Kelas", options=kelas_dict_filter.keys())
        id_kelas_terpilih = kelas_dict_filter[selected_kelas_nama]
        search_term = col2.text_input("Cari Siswa Spesifik (Nama atau NIS)", help="Kosongkan untuk melihat semua siswa di kelas terpilih")
        
        st.markdown("---")

        # --- Display Section ---
        # Logika untuk menampilkan data berdasarkan filter
        if id_kelas_terpilih and not search_term:
            # Jika hanya kelas yang dipilih, tampilkan semua tagihan kelas itu
            st.markdown(f"#### Menampilkan Semua Tagihan untuk Kelas: **{selected_kelas_nama}**")
            conn = db.create_connection()
            all_bills_in_class = db.get_all_tagihan_by_kelas(conn, id_kelas_terpilih)
            conn.close()
            if all_bills_in_class:
                df_class_bills = pd.DataFrame(all_bills_in_class, columns=['Nama Siswa', 'NIS', 'Jenis Tagihan', 'Bulan', 'Total Tagihan', 'Sisa Tagihan', 'Status'])
                df_class_bills['Status'] = df_class_bills['Status'].apply(format_status_pembayaran)
                # Tampilkan sebagai HTML untuk styling
                html_table = df_class_bills.to_html(escape=False, index=False, classes='styled-table')
                st.markdown(html_table, unsafe_allow_html=True)
            else:
                st.info("Belum ada tagihan untuk siswa di kelas ini.")

        elif search_term:
            # Jika ada pencarian, tampilkan hasil pencarian
            st.markdown("#### Hasil Pencarian Siswa")
            conn = db.create_connection()
            # Batasi pencarian di kelas terpilih jika ada
            list_siswa_db = db.get_filtered_siswa_detailed(conn, kelas_id=id_kelas_terpilih, search_term=search_term)
            conn.close()

            if list_siswa_db:
                # Layout 2 kolom untuk daftar siswa dan detail tagihannya
                list_col, detail_col = st.columns([1, 2])
                with list_col:
                    for nis, _, _, nama, _, _, kelas, _, angkatan in list_siswa_db:
                        if st.button(f"{nama} ({nis})", key=f"select_{nis}", use_container_width=True):
                            st.session_state.selected_nis_tagihan = nis
                            st.session_state.selected_nama_tagihan = nama
                with detail_col:
                    if 'selected_nis_tagihan' in st.session_state:
                        st.markdown(f"##### Tagihan untuk: **{st.session_state.selected_nama_tagihan}**")
                        conn = db.create_connection()
                        tagihan_siswa = db.get_tagihan_by_siswa(conn, st.session_state.selected_nis_tagihan)
                        conn.close()
                        if tagihan_siswa:
                            df_tagihan = pd.DataFrame(tagihan_siswa, columns=['ID', 'Nama Pembayaran', 'Bulan', 'Total', 'Sisa', 'Status'])
                            df_tagihan['Status'] = df_tagihan['Status'].apply(format_status_pembayaran)
                            st.dataframe(df_tagihan[['Nama Pembayaran', 'Bulan', 'Total', 'Sisa', 'Status']], hide_index=True, use_container_width=True)
                        else:
                            st.success("Siswa ini tidak memiliki tagihan.")
            else:
                st.warning("Siswa tidak ditemukan dengan kriteria tersebut.")
        else:
            st.info("Silakan pilih kelas atau cari siswa untuk melihat tagihan.")
            
    # CSS untuk tabel (diletakkan sekali saja di akhir)
    st.markdown("""
    <style>
        .styled-table { width: 100%; border-collapse: collapse; font-size: 14px; }
        .styled-table th { background-color: #0d6efd; color: white; text-align: left; padding: 12px; }
        .styled-table td { padding: 10px; border-bottom: 1px solid #ddd; }
        .styled-table tr:hover { background-color: #f5f5f5; }
    </style>
    """, unsafe_allow_html=True)

# Ganti fungsi lama di pembayaran.py dengan yang ini

def show_history_transaksi():
    st.subheader("⏳ History Transaksi Pembayaran")

    # --- Filter Lanjutan ---
    with st.expander("🔍 Filter Pencarian Lanjutan"):
        conn = db.create_connection()
        list_kelas = db.get_semua_kelas(conn)
        list_angkatan = db.get_semua_angkatan(conn)
        conn.close()

        kelas_dict = {f"{a} - {n}": i for i, a, n, _ in list_kelas}

        c1, c2, c3 = st.columns(3)
        selected_angkatan = c1.selectbox("Filter Angkatan", ["Semua"] + list_angkatan)
        selected_kelas_nama = c2.selectbox("Filter Kelas", ["Semua"] + list(kelas_dict.keys()))
        search_term = c3.text_input("Cari Nama/NIS/No. Transaksi")
        
        id_kelas_filter = None if selected_kelas_nama == "Semua" else kelas_dict.get(selected_kelas_nama)
        angkatan_filter = None if selected_angkatan == "Semua" else selected_angkatan

    st.markdown("---")
    
    table_col, detail_col = st.columns([0.6, 0.4], gap="large")

    with table_col:
        st.markdown("#### Daftar Transaksi")
        with st.spinner("Mencari riwayat transaksi..."):
            conn = db.create_connection()
            semua_transaksi = db.get_filtered_transaksi(conn, search_term=search_term, kelas_id=id_kelas_filter, angkatan=angkatan_filter)
            conn.close()

        if not semua_transaksi:
            st.warning("Tidak ada data transaksi yang cocok dengan pencarian Anda.")
            return
        
        df_transaksi = pd.DataFrame(semua_transaksi, columns=['ID', 'Tanggal', 'NIS', 'Nama Siswa', 'Total Bayar', 'Kelas', 'Angkatan'])
        
        st.dataframe(
            df_transaksi.rename(columns={'ID': 'No. Trx'}), # Mengganti nama kolom untuk tampilan
            key="history_selector",
            on_select="rerun",
            selection_mode="single-row",
            hide_index=True,
            use_container_width=True,
            height=500
        )

    with detail_col:
        st.markdown("#### Detail Transaksi")
        selection = st.session_state.get("history_selector")
        
        if selection and selection["selection"]["rows"]:
            selected_index = selection["selection"]["rows"][0]
            selected_row = df_transaksi.iloc[selected_index]
            selected_id = selected_row["ID"]
            
            # --- TAMPILAN KARTU DETAIL BARU ---
            with st.container(border=True):
                # 1. Informasi Kontekstual
                st.write(f"**Nama Siswa:** {selected_row['Nama Siswa']}")
                st.write(f"**NIS:** {selected_row['NIS']}")
                st.write(f"**Tanggal:** {selected_row['Tanggal']}")
                st.metric("Total Pembayaran", f"Rp {selected_row['Total Bayar']:,.0f}")

                # 2. Rincian Item Pembayaran
                with st.spinner("Memuat rincian item..."):
                    conn = db.create_connection()
                    detail_transaksi = db.get_detail_by_transaksi(conn, selected_id)
                    conn.close()
                
                if detail_transaksi:
                    st.write("**Rincian Pembayaran:**")
                    df_detail = pd.DataFrame(detail_transaksi, columns=['Item Pembayaran', 'Bulan', 'Jumlah Dibayar'])
                    if df_detail['Bulan'].isna().all():
                        df_detail = df_detail.drop(columns=['Bulan'])
                    df_detail['Jumlah Dibayar'] = df_detail['Jumlah Dibayar'].apply(lambda x: f"Rp {x:,.0f}")
                    st.table(df_detail)
        else:
            st.info("Klik sebuah baris pada tabel di sebelah kiri untuk melihat rinciannya.")


def show_broadcast_tagihan():
    st.subheader("📡 Broadcast Tagihan ke Orang Tua")

    # --- Kode CSS untuk Styling Tabel ---
    st.markdown("""
    <style>
        [data-testid="stDataFrame"] { border: 1px solid #dee2e6; border-radius: 8px; }
        [data-testid="stDataFrame"] thead th { background-color: #0d6efd; color: white; font-size: 14px; }
        [data-testid="stDataFrame"] tbody tr:hover { background-color: #f5f5f5; }
    </style>
    """, unsafe_allow_html=True)

    # --- Memuat data master sekali di awal ---
    conn = db.create_connection()
    list_pos = db.get_semua_pos_pembayaran(conn)
    list_kelas_master = db.get_semua_kelas(conn) # Daftar master semua kelas
    list_angkatan = db.get_semua_angkatan(conn)
    conn.close()

    if not list_pos:
        st.warning("Jenis Pembayaran belum ada. Silakan lengkapi terlebih dahulu.")
        return

    # --- UI Filter dengan Logika Cascading ---
    with st.container(border=True):
        st.write("**Filter Daftar Broadcast**")
        pos_dict = {f"{nama} ({tipe})": id_pos for id_pos, nama, tipe in list_pos}

        selected_pos_nama_list = st.multiselect(
            "Pilih Satu atau Beberapa Item Pembayaran",
            options=pos_dict.keys(),
            placeholder="Pilih item..."
        )

        c1, c2, c3 = st.columns(3)
        
        # Filter 1: Angkatan
        selected_angkatan = c1.selectbox("Filter Angkatan", ["Semua"] + list_angkatan)
        
        # --- Logika Filter Dependen ---
        # Filter 2: Kelas (opsinya bergantung pada Angkatan)
        if selected_angkatan != "Semua":
            # Saring daftar kelas master berdasarkan angkatan yang dipilih
            filtered_kelas_list = [k for k in list_kelas_master if k[1] == selected_angkatan]
        else:
            # Jika "Semua Angkatan", tampilkan semua kelas
            filtered_kelas_list = list_kelas_master
        
        kelas_dict_filtered = {f"{a} - {n}": i for i, a, n, _ in filtered_kelas_list}
        selected_kelas_nama = c2.selectbox("Filter Kelas", ["Semua"] + list(kelas_dict_filtered.keys()))

        # Filter 3: Pencarian Nama/NIS
        search_term = c3.text_input("Cari Nama Siswa / NIS")

        # Mengambil ID dari filter yang dipilih
        id_pos_filter_list = [pos_dict[nama] for nama in selected_pos_nama_list]
        id_kelas_filter = None if selected_kelas_nama == "Semua" else kelas_dict_filtered.get(selected_kelas_nama)
        angkatan_filter = None if selected_angkatan == "Semua" else selected_angkatan
    
    st.markdown("---")

    # --- Menampilkan Tabel Secara Dinamis ---
    if not id_pos_filter_list:
        st.info("Silakan pilih minimal satu item pembayaran untuk melihat daftar tagihan.")
    else:
        with st.spinner("Mencari data tagihan..."):
            conn = db.create_connection()
            data_broadcast = db.get_broadcast_data(
                conn, 
                list_of_id_pos=id_pos_filter_list, 
                angkatan=angkatan_filter, 
                kelas_id=id_kelas_filter,
                search_term=search_term
            )
            conn.close()

        if not data_broadcast:
            st.info("Tidak ada data tagihan yang cocok dengan filter yang dipilih.")
        else:
            st.success(f"**Ditemukan {len(data_broadcast)} tagihan yang siap di-broadcast:**")
            display_data = []
            for nama, no_wa, kelas, item, sisa in data_broadcast:
                pesan = f"Yth. Wali Murid dari {nama} ({kelas}), kami informasikan tagihan {item} sebesar Rp {sisa:,.0f} belum lunas. Terima kasih."
                pesan_url = quote(pesan)
                link = f"https://wa.me/{no_wa}?text={pesan_url}"
                display_data.append([nama, kelas if kelas else "-", item, f"Rp {sisa:,.0f}", link])
            
            df_broadcast = pd.DataFrame(display_data, columns=["Nama Siswa", "Kelas", "Tagihan", "Sisa", "Link WhatsApp"])
            st.dataframe(
                df_broadcast,
                column_config={"Link WhatsApp": st.column_config.LinkColumn("Kirim Pesan", display_text="➡️ Buka WhatsApp")},
                hide_index=True,
                use_container_width=True
            )
            
import streamlit as st
import base64 # Impor ini bisa dihapus jika tidak digunakan di tempat lain

# --- FUNGSI RENDER UTAMA MODUL (DENGAN SVG DARI ASSETS) ---
def render():
    """
    Merender seluruh antarmuka untuk Modul Pembayaran dengan memuat ikon SVG
    dari folder assets.
    """

    # --- FUNGSI BANTUAN BARU: Memuat SVG dari File ---
    @st.cache_data
    def load_svg(filepath):
        """Membuka file SVG dan mengembalikannya sebagai string XML yang bersih."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                svg = f.read()
            # Membersihkan SVG agar warnanya bisa diatur oleh CSS
            # Ganti 'currentColor' dengan warna spesifik jika perlu
            svg_cleaned = svg.replace('stroke="#007BFF"', 'stroke="currentColor"')
            svg_cleaned = svg_cleaned.replace('fill="none"', '')
            return svg_cleaned
        except FileNotFoundError:
            # Mengembalikan ikon error jika file tidak ditemukan
            return '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="red" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'

    # --- Path ke Ikon SVG di Folder Assets ---
    # Pastikan nama file ini sesuai dengan yang ada di folder assets/pembayaran/ Anda
    path_jenis_pembayaran = "assets/pembayaran/jenispembayaran.svg"
    path_tagihan_siswa = "assets/pembayaran/tagihan.svg"
    path_transaksi = "assets/pembayaran/input.svg"
    path_history = "assets/pembayaran/history.svg"
    path_broadcast = "assets/pembayaran/broadcast.svg"
    
    # --- CSS (Tidak ada perubahan) ---
    st.markdown("""
        <style>
            /* Latar belakang utama */
            .main, [data-testid="stAppViewContainer"] {
                background-color: #FFF7E8;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] > div[data-testid="stBorderedSticker"] {
                background-color: #FFFFFF;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                transition: all 0.3s ease-in-out;
                height: 100%; display: flex; flex-direction: column; padding: 1.5rem;
            }
            div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] > div[data-testid="stBorderedSticker"]:hover {
                transform: translateY(-5px); box-shadow: 0 8px 16px rgba(0,0,0,0.12); border-color: #007BFF;
            }
            .menu-item-content { text-align: center; flex-grow: 1; }
            .menu-icon-container { color: #343A40; margin-bottom: 1rem; transition: color 0.3s ease-in-out; }
            .menu-icon-container svg { width: 50px; height: 50px; }
            div[data-testid="stBorderedSticker"]:hover .menu-icon-container { color: #007BFF; }
            .menu-item-content h5 { font-size: 1.1rem; font-weight: 600; color: #343A40; margin: 0; }
            .stButton > button {
                background-color: #007BFF !important; color: white !important; font-weight: bold;
                border-radius: 8px !important; border: none !important; width: 100% !important;
                padding: 0.75rem 0 !important; font-size: 1rem !important; margin-top: 1rem;
            }
            .stButton > button:hover { background-color: #0056b3 !important; }
            [data-testid="stForm"], div[data-testid="stExpander"], .st-container[border="true"] {
                background-color: #FFFFFF !important; border: 1px solid #DEE2E6 !important;
                border-radius: 12px !important; padding: 1.5rem !important;
            }
            [data-testid="stForm"] label, div[data-testid="stExpander"] summary, .st-container[border="true"] div[data-testid="stText"] {
                color: #343A40 !important; font-weight: 600;
            }
        </style>
        """, unsafe_allow_html=True)
    
    # --- Penanganan State Halaman ---
    if 'pembayaran_view' not in st.session_state:
        st.session_state.pembayaran_view = 'menu'
    
    # --- HEADER: Judul dan Tombol Kembali ---
    col_title, col_button = st.columns([3, 1])
    with col_title:
        st.title("💵 Modul Pembayaran")
    with col_button:
        st.markdown('<div style="height: 2.5rem;"></div>', unsafe_allow_html=True)
        if st.session_state.pembayaran_view != 'menu':
            if st.button("⬅️ Kembali ke Menu", key="pembayaran_back_to_menu", use_container_width=True):
                st.session_state.pembayaran_view = 'menu'
                st.rerun()
        else:
            if st.button("⬅️ Menu Utama", key="pembayaran_back_to_main", use_container_width=True):
                st.session_state.page = 'home'
                if 'page' in st.query_params: st.query_params.clear()
                st.rerun()

    st.markdown("---")

    # --- RENDER KONTEN: Menu atau Sub-halaman ---
    if st.session_state.pembayaran_view == 'menu':
        menu_options = {
            'jenis_pembayaran': {"label": "Jenis Pembayaran", "path": path_jenis_pembayaran},
            'tagihan_siswa': {"label": "Tagihan Siswa", "path": path_tagihan_siswa},
            'transaksi_pembayaran': {"label": "Input Transaksi", "path": path_transaksi},
            'history_transaksi': {"label": "History Transaksi", "path": path_history},
            'broadcast_tagihan': {"label": "Broadcast Tagihan", "path": path_broadcast}
        }
        
        items = list(menu_options.items())
        num_cols = 3
        for i in range(0, len(items), num_cols):
            cols = st.columns(num_cols)
            row_items = items[i:i+num_cols]
            for j, (view, content) in enumerate(row_items):
                with cols[j]:
                    with st.container(border=True):
                        st.markdown(f"""
                        <div class="menu-item-content">
                            <div class="menu-icon-container">
                                {load_svg(content['path'])}
                            </div>
                            <h5>{content['label']}</h5>
                        </div>
                        """, unsafe_allow_html=True)

                        if st.button("Buka Menu", key=f"btn_pembayaran_{view}"):
                            st.session_state.pembayaran_view = view
                            st.rerun()
    else:
        view_function_map = {
            'jenis_pembayaran': show_jenis_pembayaran, 
            'tagihan_siswa': show_tagihan_siswa,
            'transaksi_pembayaran': show_transaksi_pembayaran, 
            'history_transaksi': show_history_transaksi,
            'broadcast_tagihan': show_broadcast_tagihan
        }
        render_function = view_function_map.get(st.session_state.pembayaran_view)
        if render_function:
            render_function()