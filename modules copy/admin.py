# admin.py

import streamlit as st
import pandas as pd
from utils import db_functions as db
from utils import config_manager as cfg
import shutil
from datetime import datetime
import os

# --- (BARU) Fungsi Gabungan untuk Manajemen User & Ganti Password ---
def show_manajemen_user():
    """
    Menggabungkan fungsionalitas Data User dan Ganti Password dalam satu halaman dengan tabs.
    """
    # Tombol kembali ini berlaku untuk seluruh halaman Manajemen User
    if st.button("⬅️ Kembali ke Menu Admin"):
        st.session_state.admin_view = 'menu'
        st.rerun()
    st.markdown("---")

    tab1, tab2 = st.tabs(["👥 Kelola Data Pengguna", "🔑 Ubah Password Saya"])

    # --- TAB 1: KELOLA DATA PENGGUNA (Logika dari show_data_user lama) ---
    with tab1:
        st.subheader("Kelola Semua Pengguna Aplikasi")
        with st.expander("Tambah User Baru"):
            with st.form("form_tambah_user", clear_on_submit=True):
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox("Role", ["admin", "operator"], help="Admin bisa akses semua menu, Operator terbatas.")
                if st.form_submit_button("Tambah User"):
                    if new_username and new_password:
                        conn = db.create_connection()
                        if db.tambah_user(conn, new_username, new_password, new_role):
                            st.success(f"User '{new_username}' berhasil ditambahkan.")
                        else:
                            st.error(f"Username '{new_username}' sudah ada.")
                        conn.close()
                        st.rerun()
                    else:
                        st.warning("Username dan Password tidak boleh kosong.")

        conn = db.create_connection()
        users_data = db.get_all_users(conn)
        conn.close()

        st.write("**Daftar Pengguna:**")
        df_users = pd.DataFrame(users_data, columns=['ID', 'Username', 'Role'])
        st.dataframe(df_users, use_container_width=True)

        st.write("**Opsi Edit / Hapus Pengguna**")
        # Filter agar tidak bisa mengubah/menghapus diri sendiri
        user_list = {user[1]: user[1] for user in users_data if user[1] != st.session_state.get('username')}
        if not user_list:
            st.info("Tidak ada pengguna lain yang bisa diubah atau dihapus.")
        else:
            selected_user = st.selectbox("Pilih username untuk diubah/dihapus", options=list(user_list.keys()))
            if selected_user:
                # Opsi Reset Password
                with st.form(f"form_edit_{selected_user}"):
                    st.write(f"Reset Password untuk **{selected_user}**")
                    reset_password = st.text_input("Masukkan Password Baru", type="password", key=f"pwd_{selected_user}")
                    if st.form_submit_button("Reset Password"):
                        conn = db.create_connection()
                        db.update_user_password(conn, selected_user, reset_password)
                        conn.close()
                        st.success(f"Password untuk user '{selected_user}' berhasil direset.")

                # Opsi Hapus User
                if st.button(f"❌ Hapus User: {selected_user}", type="primary"):
                    conn = db.create_connection()
                    db.hapus_user(conn, selected_user)
                    conn.close()
                    st.warning(f"User '{selected_user}' telah dihapus.")
                    st.rerun()

    # --- TAB 2: UBAH PASSWORD SAYA (Logika dari show_ganti_password lama) ---
    with tab2:
        st.subheader("Ubah Password Anda")
        username = st.session_state.get('username', '')
        with st.form("form_ganti_password"):
            st.text_input("Nama User", value=username, disabled=True)
            password_lama = st.text_input("Password Lama", type="password")
            password_baru = st.text_input("Password Baru", type="password")
            konfirmasi_password = st.text_input("Konfirmasi Password Baru", type="password")
            if st.form_submit_button("Simpan Perubahan"):
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

# --- (BARU) Fungsi untuk Import & Merge Database ---
def show_import_merge_db():
    if st.button("⬅️ Kembali ke Menu Admin"):
        st.session_state.admin_view = 'menu'
        st.rerun()
    st.markdown("---")
    st.subheader("📥 Import & Gabungkan Transaksi")
    st.warning(
        """
        **PERHATIAN:** Fitur ini digunakan untuk **menggabungkan (merge)** data transaksi dari komputer lain.
        - Fitur ini **TIDAK AKAN MENGHAPUS** data yang sudah ada.
        - Ia hanya akan **MENAMBAHKAN** data transaksi yang belum ada di database ini.
        - Pastikan file yang Anda unggah adalah file database `fatpay.db` yang valid dari komputer lain.
        """
    )

    uploaded_file = st.file_uploader("Pilih file database (.db) dari komputer sumber", type=['db'])
    
    if uploaded_file is not None:
        if st.button("Lakukan Import & Merge Sekarang", type="primary"):
            # Simpan file yang diupload sementara
            temp_db_path = f"temp_{uploaded_file.name}"
            with open(temp_db_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with st.spinner("Memproses dan menggabungkan data... Mohon tunggu."):
                conn_main = db.create_connection()
                try:
                    # Panggil fungsi backend untuk melakukan merge
                    result = db.merge_transactions_from_db(conn_main, temp_db_path)
                    
                    st.success("Proses penggabungan selesai!")
                    st.info(f"- **{result['added']}** transaksi baru berhasil ditambahkan.")
                    st.info(f"- **{result['skipped']}** transaksi dilewati (karena sudah ada).")
                    st.info(f"- **{result['errors']}** transaksi gagal di-merge (kemungkinan data siswa tidak ditemukan).")

                except Exception as e:
                    st.error(f"Terjadi kesalahan teknis saat proses merge: {e}")
                finally:
                    conn_main.close()
                    # Hapus file sementara
                    if os.path.exists(temp_db_path):
                        os.remove(temp_db_path)

# --- Fungsi-fungsi show_* lainnya yang tidak banyak berubah ---
def show_backup_db():
    if st.button("⬅️ Kembali ke Menu Admin"):
        st.session_state.admin_view = 'menu'
        st.rerun()
    st.markdown("---")
    st.subheader("💾 Backup Database")
    st.info("Fitur ini akan membuat salinan file database Anda saat ini (`fatpay.db`).")
    if st.button("Buat File Backup Sekarang"):
        # (PERBAIKAN) Menggunakan config manager untuk nama DB jika ada
        config = cfg.load_config()
        source_db = config.get("db_name", "fatpay.db")
        if not os.path.exists(source_db):
            st.error(f"File database '{source_db}' tidak ditemukan.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_fatpay_{timestamp}.db"
        try:
            shutil.copyfile(source_db, backup_filename)
            st.success(f"File backup '{backup_filename}' berhasil dibuat!")
            with open(backup_filename, "rb") as fp:
                st.download_button(label="📥 Unduh File Backup", data=fp, file_name=backup_filename, mime="application/octet-stream")
        except Exception as e:
            st.error(f"Terjadi kesalahan saat membuat backup: {e}")

def show_restore_db():
    if st.button("⬅️ Kembali ke Menu Admin"):
        st.session_state.admin_view = 'menu'
        st.rerun()
    st.markdown("---")
    st.subheader("🔄 Restore Database")
    st.error("PERINGATAN: Merestore database akan MENGGANTI SEMUA data yang ada saat ini dengan data dari file backup.")
    uploaded_file = st.file_uploader("Pilih file backup database (.db)", type=['db'])
    if uploaded_file is not None:
        if st.button("Lakukan Restore Sekarang", type="primary"):
            config = cfg.load_config()
            destination_db = config.get("db_name", "fatpay.db")
            try:
                with open(destination_db, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("Database berhasil direstore! Aplikasi akan dimuat ulang.")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Terjadi kesalahan saat merestore database: {e}")

def show_profil_lembaga():
    if st.button("⬅️ Kembali ke Menu Admin"):
        st.session_state.admin_view = 'menu'
        st.rerun()
    st.markdown("---")
    st.subheader("🏢 Pengaturan Profil Lembaga")
    st.info("Informasi ini akan digunakan pada kop surat di kuitansi dan laporan.")
    config = cfg.load_config()
    with st.form("form_profil_lembaga"):
        nama_lembaga = st.text_input("Nama Lembaga", value=config.get("nama_lembaga", ""))
        alamat = st.text_area("Alamat", value=config.get("alamat", ""))
        telp = st.text_input("No. Telp/Fax", value=config.get("telp", ""))
        website = st.text_input("Website / Email", value=config.get("website", ""))
        
        logo_path = config.get("logo_path", "assets/logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=100)
        uploaded_logo = st.file_uploader("Unggah Logo Baru (Kosongkan jika tidak ingin ganti)", type=['png', 'jpg'])
        
        if st.form_submit_button("Simpan Pengaturan"):
            if uploaded_logo is not None:
                with open(logo_path, "wb") as f:
                    f.write(uploaded_logo.getbuffer())
            
            new_config = {
                "nama_lembaga": nama_lembaga, "alamat": alamat, 
                "telp": telp, "website": website, "logo_path": logo_path
            }
            cfg.save_config(new_config)
            st.success("Pengaturan profil lembaga berhasil disimpan!")
            st.rerun()

def show_reset_db():
    if st.button("⬅️ Kembali ke Menu Admin"):
        st.session_state.admin_view = 'menu'
        st.rerun()
    st.markdown("---")
    st.subheader("🔥 Reset Database")
    st.error("**PERINGATAN SUPER PENTING!** Tindakan ini akan **MENGHAPUS SEMUA DATA** di aplikasi (siswa, transaksi, tagihan, dll.) secara permanen. Lakukan hanya jika Anda benar-benar yakin.")
    
    confirmation_text = "SAYA YAKIN INGIN MENGHAPUS SEMUA DATA"
    st.write("Untuk melanjutkan, ketik kalimat persis seperti di bawah ini ke dalam kotak teks:")
    st.code(confirmation_text)
    user_input = st.text_input("Ketik kalimat konfirmasi di sini:")
    
    is_disabled = (user_input != confirmation_text)
    if st.button("RESET DATABASE SEKARANG", type="primary", disabled=is_disabled):
        try:
            config = cfg.load_config()
            db_file = config.get("db_name", "fatpay.db")
            if os.path.exists(db_file):
                os.remove(db_file)
                # Inisialisasi ulang database kosong
                conn = db.create_connection()
                db.create_tables(conn)
                db.add_default_user(conn) # Pastikan Anda punya fungsi ini
                conn.close()
                st.success("Database berhasil direset! Aplikasi akan dimulai ulang dengan data kosong.")
                st.balloons()
                st.rerun()
        except Exception as e:
            st.error(f"Gagal mereset database: {e}")

# --- Fungsi Render Utama untuk Modul Admin ---
def render():
    # Pengecekan Hak Akses Admin
    if st.session_state.get('role') != 'admin':
        st.error("⛔ Anda tidak memiliki hak akses untuk membuka halaman ini.")
        st.info("Silakan hubungi administrator.")
        return

    # --- (PERUBAHAN) Tata Letak Header ---
    col_header_1, col_header_2 = st.columns([0.7, 0.3])
    with col_header_1:
        st.title("⚙️ Modul Admin")
    with col_header_2:
        if st.button("⬅️ Kembali ke Menu Utama", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()
    
    if 'admin_view' not in st.session_state:
        st.session_state.admin_view = 'menu'

    if st.session_state.admin_view == 'menu':
        st.markdown("---")
        st.markdown(
            """
            <style>
            .stButton>button {
                height: 100px;
                font-size: 16px;
                font-weight: bold;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            # --- (PERUBAHAN) Menu digabung ---
            if st.button("👥 Manajemen Pengguna"): 
                st.session_state.admin_view = 'manajemen_user'
                st.rerun()
            if st.button("💾 Backup Database"): 
                st.session_state.admin_view = 'backup_db'
                st.rerun()
        with col2:
            if st.button("🏢 Profil Lembaga"): 
                st.session_state.admin_view = 'profil_lembaga'
                st.rerun()
            if st.button("🔄 Restore Database"): 
                st.session_state.admin_view = 'restore_db'
                st.rerun()
        with col3:
            # --- (BARU) Tombol untuk Import & Merge ---
            if st.button("📥 Import & Merge Transaksi"): 
                st.session_state.admin_view = 'import_merge_db'
                st.rerun()
            if st.button("🔥 Reset Database"): 
                st.session_state.admin_view = 'reset_db'
                st.rerun()
            
    # --- (PERUBAHAN) Rute pemanggilan fungsi ---
    elif st.session_state.admin_view == 'manajemen_user': show_manajemen_user()
    elif st.session_state.admin_view == 'backup_db': show_backup_db()
    elif st.session_state.admin_view == 'restore_db': show_restore_db()
    elif st.session_state.admin_view == 'profil_lembaga': show_profil_lembaga()
    elif st.session_state.admin_view == 'reset_db': show_reset_db()
    # --- (BARU) Rute untuk halaman Import & Merge ---
    elif st.session_state.admin_view == 'import_merge_db': show_import_merge_db()