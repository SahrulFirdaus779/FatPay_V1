import streamlit as st
import pandas as pd
from utils import db_functions as db
from utils import config_manager as cfg
import shutil
from datetime import datetime
import os
import sqlite3
import datetime

# --- FUNGSI SUB-HALAMAN (HANYA MENGHAPUS TOMBOL KEMBALI) ---

def show_manajemen_user():
    """
    Versi perbaikan dari halaman manajemen user dengan UI/UX yang lebih modern.
    Menggunakan dialog untuk form dan konfirmasi, serta layout kolom untuk daftar interaktif.
    """
    # Inisialisasi state untuk dialog
    if "show_add_user_dialog" not in st.session_state:
        st.session_state.show_add_user_dialog = False
    if "editing_user" not in st.session_state:
        st.session_state.editing_user = None
    if "deleting_user" not in st.session_state:
        st.session_state.deleting_user = None

    st.markdown("---")
    tab1, tab2 = st.tabs(["👥 Kelola Data Pengguna", "🔑 Ubah Password Saya"])

    # --- TAB 1: KELOLA DATA PENGGUNA (VERSI BARU) ---
    with tab1:
        st.subheader("Kelola Semua Pengguna Aplikasi")

        # Tombol untuk memicu dialog tambah user
        if st.button("➕ Tambah User Baru", type="primary"):
            st.session_state.show_add_user_dialog = True
        
        st.markdown("---")

        # --- Daftar Pengguna Interaktif ---
        st.write("**Daftar Pengguna:**")
        
        # Header Tabel
        header_cols = st.columns([1, 4, 2, 2])
        header_cols[0].write("**ID**")
        header_cols[1].write("**Username**")
        header_cols[2].write("**Role**")
        header_cols[3].write("**Aksi**")

        conn = db.create_connection()
        users_data = db.get_all_users(conn)
        conn.close()

        for user in users_data:
            user_id, username, role = user
            # Jangan tampilkan aksi untuk user yang sedang login
            is_current_user = (username == st.session_state.get('username'))
            
            row_cols = st.columns([1, 4, 2, 2])
            row_cols[0].write(user_id)
            row_cols[1].write(username)
            row_cols[2].write(f"`{role}`")
            
            action_cols = row_cols[3].columns(2)
            if not is_current_user:
                # Tombol Edit
                if action_cols[0].button("✏️", key=f"edit_{user_id}", help="Edit User", use_container_width=True):
                    st.session_state.editing_user = user
                # Tombol Hapus
                if action_cols[1].button("🗑️", key=f"delete_{user_id}", help="Hapus User", use_container_width=True):
                    st.session_state.deleting_user = user
            else:
                row_cols[3].info("Anda")


    # --- TAB 2: UBAH PASSWORD SAYA (Dengan sedikit penyempurnaan visual) ---
    with tab2:
        st.subheader("Ubah Password Anda Sendiri")
        with st.container(border=True): # Menggunakan container agar terlihat lebih rapi
            username = st.session_state.get('username', '')
            with st.form("form_ganti_password_saya"):
                st.text_input("Nama User", value=username, disabled=True)
                password_lama = st.text_input("Password Lama", type="password")
                password_baru = st.text_input("Password Baru", type="password", help="Minimal 6 karakter.")
                konfirmasi_password = st.text_input("Konfirmasi Password Baru", type="password")
                
                if st.form_submit_button("Simpan Perubahan", type="primary"):
                    if not all([password_lama, password_baru, konfirmasi_password]):
                        st.error("Semua kolom harus diisi.")
                    elif password_baru != konfirmasi_password:
                        st.error("Password Baru dan Konfirmasi tidak cocok.")
                    else:
                        conn = db.create_connection()
                        user_role = db.check_login(conn, username, password_lama)
                        if user_role:
                            db.update_user_password(conn, username, password_baru)
                            st.success("Password Anda berhasil diubah!")
                        else:
                            st.error("Password Lama yang Anda masukkan salah.")
                        conn.close()


    # --- (BARU) Logika untuk Dialog Tambah User ---
    if st.session_state.show_add_user_dialog:
        st.dialog("Tambah User Baru")
        with st.form("form_dialog_tambah_user"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["admin", "operator"])
            
            btn_col1, btn_col2 = st.columns(2)
            if btn_col1.form_submit_button("Simpan", type="primary", use_container_width=True):
                if new_username and new_password:
                    conn = db.create_connection()
                    if db.tambah_user(conn, new_username, new_password, new_role):
                        st.toast(f"✅ User '{new_username}' berhasil ditambahkan.")
                        st.session_state.show_add_user_dialog = False
                        st.rerun()
                    else:
                        st.error(f"Username '{new_username}' sudah ada.")
                    conn.close()
                else:
                    st.warning("Username dan Password wajib diisi.")
            
            if btn_col2.form_submit_button("Batal", use_container_width=True):
                st.session_state.show_add_user_dialog = False
                st.rerun()

    # --- (BARU) Logika untuk Dialog Edit User ---
    if st.session_state.editing_user:
        user_id, username, role = st.session_state.editing_user
        st.dialog(f"Edit User: {username}")
        with st.form("form_dialog_edit_user"):
            st.write("Anda dapat mengubah role atau mereset password pengguna ini.")
            
            # Opsi Ganti Role
            new_role = st.selectbox("Ubah Role", ["admin", "operator"], index=0 if role == 'admin' else 1)
            
            # Opsi Reset Password
            st.markdown("---")
            st.write("**Reset Password (Opsional)**")
            new_password = st.text_input("Masukkan Password Baru", type="password", placeholder="Kosongkan jika tidak diubah")

            btn_col1, btn_col2 = st.columns(2)
            if btn_col1.form_submit_button("Simpan Perubahan", type="primary", use_container_width=True):
                conn = db.create_connection()
                # Update role
                db.update_user_role(conn, username, new_role) # Anda perlu membuat fungsi ini di db_functions.py
                # Update password jika diisi
                if new_password:
                    db.update_user_password(conn, username, new_password)
                conn.close()
                st.toast(f"✅ Data user '{username}' berhasil diperbarui.")
                st.session_state.editing_user = None
                st.rerun()

            if btn_col2.form_submit_button("Batal", use_container_width=True):
                st.session_state.editing_user = None
                st.rerun()


    # --- (BARU) Logika untuk Dialog Konfirmasi Hapus ---
    if st.session_state.deleting_user:
        user_id, username, role = st.session_state.deleting_user
        st.dialog("Konfirmasi Hapus")
        st.error(f"Anda yakin ingin menghapus user **'{username}'** secara permanen?")
        
        btn_col1, btn_col2 = st.columns(2)
        if btn_col1.button("Ya, Hapus Sekarang", type="primary", use_container_width=True):
            conn = db.create_connection()
            db.hapus_user(conn, username)
            conn.close()
            st.toast(f"🗑️ User '{username}' telah dihapus.")
            st.session_state.deleting_user = None
            st.rerun()
        
        if btn_col2.button("Batal", use_container_width=True):
            st.session_state.deleting_user = None
            st.rerun()

def show_import_merge_db():
    # ### PERUBAHAN: State management diperluas untuk tahap 'preview' ###
    if 'merge_step' not in st.session_state:
        st.session_state.merge_step = 'upload' # 'upload', 'preview', 'result'
    if 'temp_db_path' not in st.session_state:
        st.session_state.temp_db_path = None

    st.markdown("---")
    st.subheader("📥 Import & Gabungkan Transaksi")

    # --- TAHAP 1: UPLOAD FILE ---
    if st.session_state.merge_step == 'upload':
        with st.container(border=True):
            st.info(
                """
                **Langkah 1 dari 3:** Pilih file database (`.db`) dari komputer lain yang datanya ingin Anda gabungkan.
                """
            )
            uploaded_file = st.file_uploader(
                "Pilih file database...",
                type=['db'],
                key='file_uploader_merge'
            )
            
            if uploaded_file is not None:
                # Simpan file ke path sementara dan lanjutkan ke tahap pratinjau
                temp_db_path = f"temp_merge_{uploaded_file.name}"
                with open(temp_db_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.session_state.temp_db_path = temp_db_path
                st.session_state.merge_step = 'preview'
                st.rerun()

    # --- TAHAP 2: VALIDASI DATA (PRATINJAU) ---
    elif st.session_state.merge_step == 'preview':
        with st.container(border=True):
            st.info(
                f"""
                **Langkah 2 dari 3:** Validasi Data. Berikut adalah pratinjau data transaksi yang ditemukan di dalam file 
                **'{os.path.basename(st.session_state.temp_db_path)}'**.
                """
            )
            
            df_preview = pd.DataFrame()
            try:
                # Koneksi ke DB sementara untuk pratinjau
                conn_temp = sqlite3.connect(st.session_state.temp_db_path)
                df_preview = db.get_transactions_for_preview(conn_temp)
                conn_temp.close()
            except Exception as e:
                st.error(f"Gagal membaca file database. Pastikan file valid. Error: {e}")

            if not df_preview.empty:
                st.write(f"Ditemukan **{len(df_preview)}** data transaksi:")
                st.dataframe(df_preview, use_container_width=True, height=300)
                
                st.markdown("---")
                st.write("Jika data di atas sudah benar, silakan lanjutkan proses penggabungan.")
                
                # Tombol untuk melanjutkan ke proses merge
                if st.button("✅ Lanjutkan & Gabungkan Data Ini", type="primary"):
                    with st.spinner("Memproses dan menggabungkan data... Mohon tunggu."):
                        conn_main = db.create_connection()
                        try:
                            result = db.merge_transactions_from_db(conn_main, st.session_state.temp_db_path)
                            st.session_state.merge_result = result
                            st.session_state.merge_step = 'result'
                        except Exception as e:
                            st.error(f"Terjadi kesalahan teknis saat proses merge: {e}")
                            st.session_state.merge_step = 'upload'
                        finally:
                            conn_main.close()
                            # Hapus file sementara setelah proses selesai atau gagal
                            if os.path.exists(st.session_state.temp_db_path):
                                os.remove(st.session_state.temp_db_path)
                            st.rerun()
            else:
                st.error("Tidak ada data transaksi yang dapat ditampilkan dari file ini atau format database tidak sesuai.")

            # Tombol untuk batal dan memilih file lain
            if st.button("❌ Batal & Pilih File Lain"):
                if os.path.exists(st.session_state.temp_db_path):
                    os.remove(st.session_state.temp_db_path)
                st.session_state.merge_step = 'upload'
                st.session_state.temp_db_path = None
                st.rerun()

    # --- TAHAP 3: TAMPILKAN HASIL ---
    elif st.session_state.merge_step == 'result':
        with st.container(border=True):
            st.success("🎉 **Langkah 3 dari 3:** Proses penggabungan selesai!")
            st.markdown("---")
            
            result = st.session_state.merge_result
            col1, col2, col3 = st.columns(3)
            col1.metric(label="✔️ Transaksi Ditambahkan", value=result.get('added', 0))
            col2.metric(label="⏭️ Transaksi Dilewati", value=result.get('skipped', 0), help="Transaksi ini dilewati karena sudah ada di database utama.")
            col3.metric(label="⚠️ Transaksi Gagal", value=result.get('errors', 0), help="Gagal karena data siswa/referensi tidak ditemukan.")
            
            st.markdown("---")
            if st.button("➕ Import & Merge File Lain", type="primary", use_container_width=True):
                st.session_state.merge_step = 'upload'
                st.session_state.temp_db_path = None
                del st.session_state.merge_result
                st.rerun()

# Di admin.py
from datetime import datetime, timedelta

def show_backup_db():
    st.markdown("---")
    st.subheader("💾 Ekspor Transaksi (Backup)")
    
    with st.container(border=True):
        st.info(
            """
            Fitur ini akan membuat file database **baru** yang hanya berisi data transaksi
            dalam rentang waktu yang Anda pilih. File ini ideal untuk dipindahkan dan digabungkan
            (merge) di komputer lain.
            """
        )

        # Opsi Pilihan Rentang Waktu
        pilihan_rentang = st.radio(
            "Pilih rentang waktu untuk backup:",
            ("Hari Ini", "7 Hari Terakhir", "30 Hari Terakhir", "Pilih Rentang Manual"),
            horizontal=True,
            key="backup_range_option"
        )
        
        today = datetime.now().date()
        start_date, end_date = None, None

        if pilihan_rentang == "Hari Ini":
            start_date = today
            end_date = today
        elif pilihan_rentang == "7 Hari Terakhir":
            start_date = today - timedelta(days=6)
            end_date = today
        elif pilihan_rentang == "30 Hari Terakhir":
            start_date = today - timedelta(days=29)
            end_date = today
        elif pilihan_rentang == "Pilih Rentang Manual":
            col1, col2 = st.columns(2)
            start_date = col1.date_input("Tanggal Mulai", today - timedelta(days=7))
            end_date = col2.date_input("Tanggal Akhir", today)

        # Tampilkan rentang terpilih untuk konfirmasi
        if start_date and end_date:
            st.success(f"Rentang terpilih: **{start_date.strftime('%d %B %Y')}** hingga **{end_date.strftime('%d %B %Y')}**")

        st.markdown("---")

        if st.button("🚀 Buat File Backup Transaksi", type="primary"):
            if not all([start_date, end_date]):
                st.error("Rentang tanggal tidak valid. Mohon periksa kembali.")
                return
            
            if start_date > end_date:
                st.error("Tanggal mulai tidak boleh lebih akhir dari tanggal selesai.")
                return

            with st.spinner("Memeriksa dan mengekspor data transaksi..."):
                config = cfg.load_config()
                source_db = config.get("db_name", "fatpay.db")
                timestamp = datetime.now().strftime("%Y%m%d")
                backup_filename = f"export_transaksi_{start_date.strftime('%Y%m%d')}_sd_{end_date.strftime('%Y%m%d')}_{timestamp}.db"
                
                # Panggil fungsi ekspor dari db_functions
                result = db.export_transactions_to_new_db(
                    source_db,
                    backup_filename,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )

                # ### PERUBAHAN LOGIKA UNTUK MENAMPILKAN PESAN ###
                if result['success']:
                    if result['count'] > 0:
                        # KASUS 1: Berhasil dan ada data
                        st.success(f"Berhasil! Ditemukan dan diekspor {result['count']} data transaksi.")
                        with open(backup_filename, "rb") as fp:
                            st.download_button(
                                label="📥 Unduh File Backup",
                                data=fp,
                                file_name=backup_filename,
                                mime="application/octet-stream"
                            )
                    else:
                        # KASUS 2: Berhasil tapi tidak ada data
                        st.warning("Tidak ada data transaksi yang ditemukan pada rentang tanggal yang dipilih. File backup tidak dibuat.")
                else:
                    # KASUS 3: Gagal karena error teknis
                    st.error(f"Terjadi kesalahan teknis: {result['message']}")

def show_backup_restore_page():
    """
    Menampilkan halaman dengan antarmuka tab untuk backup dan restore database.
    Notifikasi untuk restore sekarang bersifat persisten setelah aplikasi dimuat ulang.
    """
    # Periksa apakah ada pesan sukses dari proses restore sebelumnya
    if 'db_restore_success' in st.session_state and st.session_state.db_restore_success:
        st.success("Database berhasil direstore! Aplikasi telah dimuat ulang untuk menerapkan perubahan.")
        # Hapus flag agar pesan tidak muncul lagi pada refresh berikutnya
        del st.session_state.db_restore_success

    st.markdown("---")
    st.subheader("🗄️ Manajemen Backup & Restore Database")
    st.info("Gunakan halaman ini untuk membuat cadangan (backup) data Anda atau mengembalikan (restore) data dari file cadangan.")

    tab1, tab2 = st.tabs(["📥 Backup Database", "🔄 Restore Database"])

    # --- Tab 1: Fungsionalitas Backup ---
    with tab1:
        st.markdown("#### Buat & Unduh Cadangan Database")
        st.write("Klik tombol di bawah untuk mengunduh salinan file database (`fatpay.db`) saat ini. Simpan file ini di tempat yang aman.")
        db_name = "fatpay.db"
        if os.path.exists(db_name):
            with open(db_name, "rb") as fp:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                backup_filename = f"backup_{db_name.split('.')[0]}_{timestamp}.db"
                st.download_button(
                    label="✅ Buat & Unduh Backup Sekarang",
                    data=fp,
                    file_name=backup_filename,
                    mime="application/octet-stream",
                    help=f"Unduh file database saat ini sebagai '{backup_filename}'"
                )
        else:
            st.error(f"File database '{db_name}' tidak ditemukan.")

    # --- Tab 2: Fungsionalitas Restore dengan Notifikasi Persisten ---
    with tab2:
        st.markdown("#### Kembalikan Database dari File Cadangan")
        with st.expander("⚠️ Buka untuk memulai proses restore"):
            st.error(
                "**PERINGATAN KERAS:** Merestore database akan **MENGGANTI SEMUA DATA** "
                "yang ada saat ini dengan data dari file backup yang Anda unggah. "
                "Aksi ini tidak dapat dibatalkan."
            )
            
            uploaded_file = st.file_uploader(
                "Pilih file backup database (.db) untuk di-restore",
                type=['db']
            )

            if uploaded_file is not None:
                confirm_restore = st.checkbox(
                    f"Saya mengerti dan setuju untuk menimpa seluruh data saat ini dengan file `{uploaded_file.name}`."
                )

                if st.button("Lakukan Restore Sekarang", type="primary", disabled=not confirm_restore):
                    with st.spinner("Sedang memproses restore... Harap tunggu."):
                        try:
                            destination_db = "fatpay.db"
                            with open(destination_db, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            # Set flag di session state untuk menampilkan pesan setelah rerun
                            st.session_state.db_restore_success = True
                            
                            st.balloons()
                            # Muat ulang aplikasi
                            st.rerun()
                        
                        except Exception as e:
                            st.error(f"Terjadi kesalahan saat merestore database: {e}")


def show_profil_lembaga_improved():
    st.markdown("---")
    st.subheader("🏢 Pengaturan Profil Lembaga")
    st.info("Informasi ini akan digunakan pada kop surat di kuitansi dan laporan.")
    
    config = cfg.load_config()

    # 1. Peningkatan UI: Gunakan kolom untuk tata letak yang lebih baik
    col1, col2 = st.columns([2, 1]) # Kolom kiri lebih lebar

    with col1:
        st.markdown("##### Data Lembaga")
        with st.form("form_profil_lembaga"):
            nama_lembaga = st.text_input(
                "Nama Lembaga", 
                value=config.get("nama_lembaga", ""), 
                placeholder="Contoh: Yayasan Cerdas Berkarya"
            )
            alamat = st.text_area(
                "Alamat", 
                value=config.get("alamat", ""),
                placeholder="Contoh: Jl. Pendidikan No. 123, Jakarta"
            )
            telp = st.text_input(
                "No. Telp/Fax", 
                value=config.get("telp", ""),
                placeholder="Contoh: 021-12345678"
            )
            website = st.text_input(
                "Website / Email", 
                value=config.get("website", ""),
                placeholder="Contoh: info@cerdasberkarya.org"
            )
            
            st.markdown("##### Logo Lembaga")
            uploaded_logo = st.file_uploader(
                "Unggah Logo Baru (Kosongkan jika tidak ingin ganti)", 
                type=['png', 'jpg', 'jpeg']
            )

            submitted = st.form_submit_button("Simpan Pengaturan", use_container_width=True)

    # 2. Peningkatan UX: Tampilkan logo saat ini dan preview logo baru di kolom terpisah
    with col2:
        st.markdown("###### Logo Saat Ini:")
        logo_path = config.get("logo_path", "assets/logo.png")
        if os.path.exists(logo_path):
            try:
                image = Image.open(logo_path)
                st.image(image, use_column_width=True)
            except Exception as e:
                st.error(f"Gagal memuat logo: {e}")
        else:
            st.warning("Logo belum diatur.")

        # Tampilkan preview logo yang baru diunggah
        if uploaded_logo is not None:
            st.markdown("###### Preview Logo Baru:")
            st.image(uploaded_logo, use_column_width=True)

    if submitted:
        with st.spinner("Menyimpan pengaturan..."):
            new_logo_path = logo_path

            # 3. Peningkatan Logika: Simpan logo dengan nama unik
            if uploaded_logo is not None:
                # Buat direktori jika belum ada
                upload_dir = "assets/uploads"
                os.makedirs(upload_dir, exist_ok=True)
                
                # Buat nama file unik untuk menghindari penimpaan
                file_extension = os.path.splitext(uploaded_logo.name)[1]
                new_filename = f"logo_{int(time.time())}{file_extension}"
                new_logo_path = os.path.join(upload_dir, new_filename)
                
                try:
                    with open(new_logo_path, "wb") as f:
                        f.write(uploaded_logo.getbuffer())
                except Exception as e:
                    st.error(f"Gagal menyimpan logo baru: {e}")
                    st.stop()

            # Simpan semua konfigurasi
            new_config = {
                "nama_lembaga": nama_lembaga, 
                "alamat": alamat, 
                "telp": telp, 
                "website": website, 
                "logo_path": new_logo_path  # Simpan path logo yang baru
            }
            cfg.save_config(new_config)
            
        st.success("✅ Pengaturan profil lembaga berhasil diperbarui!")
        time.sleep(1) # Beri jeda agar pengguna bisa membaca pesan sukses
        st.rerun()

def show_reset_db():
    # Bagian 1: Periksa apakah ada pesan sukses dari proses reset sebelumnya
    if 'db_reset_success' in st.session_state and st.session_state.db_reset_success:
        st.success("Database berhasil direset! Aplikasi telah dimulai ulang dengan data kosong dan user 'admin' default.")
        # Hapus flag agar pesan tidak muncul lagi pada refresh berikutnya
        del st.session_state.db_reset_success

    st.markdown("---")
    st.subheader("🔥 Reset Database")
    st.error(
        "**PERINGATAN SUPER PENTING!** Tindakan ini akan **MENGHAPUS SEMUA DATA** "
        "di aplikasi (siswa, transaksi, tagihan, dll.) secara permanen. "
        "Lakukan hanya jika Anda benar-benar yakin dan sudah memiliki backup."
    )
    
    with st.expander("Buka untuk melanjutkan proses reset"):
        confirmation_text = "SAYA YAKIN INGIN MENGHAPUS SEMUA DATA"
        st.write("Untuk melanjutkan, ketik kalimat di bawah ini (huruf besar semua) ke dalam kotak teks:")
        st.code(confirmation_text)
        
        user_input = st.text_input("Ketik kalimat konfirmasi di sini:")
        
        # Tombol reset dinonaktifkan sampai input pengguna cocok persis
        is_disabled = (user_input.strip() != confirmation_text)
        
        if st.button("RESET DATABASE SEKARANG", type="primary", disabled=is_disabled):
            with st.spinner("Mereset database..."):
                try:
                    # config = cfg.load_config()
                    # db_file = config.get("db_name", "fatpay.db")
                    db_file = "fatpay.db" # Atau gunakan nama file langsung

                    # Hapus file DB yang lama jika ada
                    if os.path.exists(db_file):
                        os.remove(db_file)
                    
                    # Buat ulang database dari awal
                    conn = db.create_connection()
                    if conn is not None:
                        db.create_tables(conn)
                        # Panggil fungsi yang baru ditambahkan
                        db.add_default_user(conn) 
                        conn.close()
                        
                        # Bagian 2: Set flag di session state, bukan menampilkan pesan
                        st.session_state.db_reset_success = True

                        st.rerun()
                    else:
                        st.error("Gagal membuat koneksi ke database baru.")

                except Exception as e:
                    st.error(f"Gagal mereset database: {e}")


# --- (BARU) FUNGSI RENDER UTAMA DENGAN UI MODERN ---
def render():
    # Pengecekan Hak Akses Admin
    if st.session_state.get('role') != 'admin':
        st.error("⛔ Anda tidak memiliki hak akses untuk membuka halaman ini.")
        st.info("Silakan hubungi administrator.")
        return

    # --- (BARU) Fungsi bantuan untuk memuat SVG dari file ---
    @st.cache_data
    def load_svg(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                svg = f.read()
            return svg
        except FileNotFoundError:
            return '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="red" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line></svg>'

    # --- (BARU) Path ke Ikon SVG di Folder Assets ---
    # Pastikan Anda membuat folder assets/admin dan menaruh file SVG di dalamnya
    path_manajemen_user = "assets/admin/users.svg"
    path_profil_lembaga = "assets/admin/institution.svg"
    path_import_merge = "assets/admin/import.svg"
    path_backup = "assets/admin/backup.svg"
    path_restore = "assets/admin/restore.svg"
    path_reset = "assets/admin/reset.svg"

    # --- (BARU) CSS untuk styling ---
    st.markdown("""
        <style>
            /* Latar belakang utama */
            .main, [data-testid="stAppViewContainer"] {
                background-color: #FFF7E8; /* Warna latar yang lebih netral */
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            /* Styling untuk kartu menu */
            div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] > div[data-testid="stBorderedSticker"] {
                background-color: #FFFFFF;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                transition: all 0.3s ease-in-out;
                height: 100%; display: flex; flex-direction: column; padding: 1.5rem;
            }
            div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] > div[data-testid="stBorderedSticker"]:hover {
                transform: translateY(-5px); 
                box-shadow: 0 8px 16px rgba(0,0,0,0.12);
                border: 1px solid #007BFF;
            }
            .menu-item-content { text-align: center; flex-grow: 1; }
            .menu-icon-container { color: #343A40; margin-bottom: 1rem; transition: color 0.3s ease-in-out; }
            .menu-icon-container svg { width: 50px; height: 50px; }
            div[data-testid="stBorderedSticker"]:hover .menu-icon-container { color: #007BFF; }
            .menu-item-content h5 { font-size: 1.1rem; font-weight: 600; color: #343A40; margin: 0; }
            
            /* Styling untuk tombol di dalam kartu */
            .stButton > button {
                background-color: #007BFF !important; color: white !important; font-weight: bold;
                border-radius: 8px !important; border: none !important; width: 100% !important;
                padding: 0.75rem 0 !important; font-size: 1rem !important; margin-top: 1rem;
            }
            .stButton > button:hover { background-color: #0056b3 !important; }

            /* Styling untuk form dan expander agar konsisten */
            [data-testid="stForm"], div[data-testid="stExpander"], .st-container[border="true"] {
                background-color: #FFFFFF !important; border: 1px solid #DEE2E6 !important;
                border-radius: 12px !important; padding: 1.5rem !important;
            }
        </style>
        """, unsafe_allow_html=True)

    # --- (BARU) Penanganan State & Header Terpusat ---
    if 'admin_view' not in st.session_state:
        st.session_state.admin_view = 'menu'

    col_title, col_button = st.columns([3, 1])
    with col_title:
        st.title("⚙️ Modul Admin")
    with col_button:
        st.markdown('<div style="height: 2.5rem;"></div>', unsafe_allow_html=True) # Spacer
        # Tombol kembali yang logikanya berubah tergantung di halaman mana
        if st.session_state.admin_view != 'menu':
            if st.button("⬅️ Kembali ke Menu Admin", use_container_width=True):
                st.session_state.admin_view = 'menu'
                st.rerun()
        else:
            if st.button("⬅️ Kembali ke Menu Utama", use_container_width=True):
                st.session_state.page = 'home'
                st.rerun()

    # --- (BARU) Logika untuk menampilkan menu atau sub-halaman ---
    if st.session_state.admin_view == 'menu':
        st.markdown("---")
        menu_options = {
            'manajemen_user': {"label": "Manajemen Pengguna", "path": path_manajemen_user},
            'profil_lembaga': {"label": "Profil Lembaga", "path": path_profil_lembaga},
            'import_merge_db': {"label": "Import & Merge", "path": path_import_merge},
            'backup_db': {"label": "Ekspor Transaksi", "path": path_backup},
            'restore_db': {"label": "Restore Database", "path": path_restore},
            'reset_db': {"label": "Reset Database", "path": path_reset}
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

                        if st.button("Buka Menu", key=f"btn_admin_{view}"):
                            st.session_state.admin_view = view
                            st.rerun()

    # --- Logika Pemanggilan Fungsi Sub-Halaman (Router) ---
    else:
        view_function_map = {
            'manajemen_user': show_manajemen_user,
            'backup_db': show_backup_db,
            'restore_db': show_backup_restore_page,
            'profil_lembaga': show_profil_lembaga_improved,
            'reset_db': show_reset_db,
            'import_merge_db': show_import_merge_db,
        }
        render_function = view_function_map.get(st.session_state.admin_view)
        if render_function:
            render_function()