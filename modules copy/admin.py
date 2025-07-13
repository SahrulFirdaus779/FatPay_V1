import streamlit as st
import pandas as pd
from utils import db_functions as db
from utils import config_manager as cfg
import shutil
from datetime import datetime
import os

# --- Semua fungsi show_* yang sudah ada (tidak berubah) ---
def show_data_user():
    st.subheader("Kelola Data Pengguna Aplikasi")
    if st.button("⬅️ Kembali ke Menu Admin"):
        st.session_state.admin_view = 'menu'
        st.rerun()
    st.markdown("---")
    with st.expander("Tambah User Baru"):
        with st.form("form_tambah_user", clear_on_submit=True):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["admin", "operator"])
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
    user_list = {user[1]: user[1] for user in users_data if user[1] != st.session_state.get('username', 'admin')}
    if not user_list:
        st.info("Tidak ada pengguna lain yang bisa diubah atau dihapus.")
        return
    selected_user = st.selectbox("Pilih username untuk diubah/dihapus", options=user_list.keys())
    if selected_user:
        with st.form(f"form_edit_{selected_user}"):
            st.write(f"Reset Password untuk **{selected_user}**")
            reset_password = st.text_input("Masukkan Password Baru", type="password")
            if st.form_submit_button("Reset Password"):
                conn = db.create_connection()
                db.update_user_password(conn, selected_user, reset_password)
                conn.close()
                st.success(f"Password untuk user '{selected_user}' berhasil direset.")
        if st.button(f"❌ Hapus User: {selected_user}", type="primary"):
            conn = db.create_connection()
            db.hapus_user(conn, selected_user)
            conn.close()
            st.warning(f"User '{selected_user}' telah dihapus.")
            st.rerun()

def show_ganti_password():
    st.subheader("Ubah Password Anda")
    if st.button("⬅️ Kembali ke Menu Admin"):
        st.session_state.admin_view = 'menu'
        st.rerun()
    st.markdown("---")
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

def show_backup_db():
    st.subheader("💾 Backup Database")
    if st.button("⬅️ Kembali ke Menu Admin"):
        st.session_state.admin_view = 'menu'
        st.rerun()
    st.markdown("---")
    st.info("Fitur ini akan membuat salinan file database Anda saat ini (`fatpay.db`).")
    if st.button("Buat File Backup Sekarang"):
        source_db = "fatpay.db"
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
    st.subheader("🔄 Restore Database")
    if st.button("⬅️ Kembali ke Menu Admin"):
        st.session_state.admin_view = 'menu'
        st.rerun()
    st.markdown("---")
    st.error("PERINGATAN: Merestore database akan MENGGANTI SEMUA data yang ada saat ini dengan data dari file backup.")
    uploaded_file = st.file_uploader("Pilih file backup database (.db)", type=['db'])
    if uploaded_file is not None:
        if st.button("Lakukan Restore Sekarang", type="primary"):
            destination_db = "fatpay.db"
            try:
                with open(destination_db, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("Database berhasil direstore! Aplikasi akan dimuat ulang.")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Terjadi kesalahan saat merestore database: {e}")

def show_profil_lembaga():
    st.subheader("🏢 Pengaturan Profil Lembaga")
    if st.button("⬅️ Kembali ke Menu Admin"):
        st.session_state.admin_view = 'menu'
        st.rerun()
    st.markdown("---")
    config = cfg.load_config()
    with st.form("form_profil_lembaga"):
        st.write("**Detail Lembaga**")
        nama_lembaga = st.text_input("Nama Lembaga", value=config.get("nama_lembaga", ""))
        alamat = st.text_area("Alamat", value=config.get("alamat", ""))
        telp = st.text_input("No. Telp/Fax", value=config.get("telp", ""))
        website = st.text_input("Website / Email", value=config.get("website", ""))
        st.write("**Logo**")
        logo_saat_ini = config.get("logo_path", "logo.png")
        st.write(f"Logo saat ini: `{logo_saat_ini}`")
        if os.path.exists(logo_saat_ini):
            st.image(logo_saat_ini, width=100)
        uploaded_logo = st.file_uploader("Unggah Logo Baru (Kosongkan jika tidak ingin ganti)", type=['png', 'jpg'])
        if st.form_submit_button("Simpan Pengaturan"):
            if uploaded_logo is not None:
                with open(logo_saat_ini, "wb") as f:
                    f.write(uploaded_logo.getbuffer())
            new_config = {"nama_lembaga": nama_lembaga, "alamat": alamat, "telp": telp, "website": website, "logo_path": logo_saat_ini}
            cfg.save_config(new_config)
            st.success("Pengaturan profil lembaga berhasil disimpan!")

# --- (BARU) Halaman untuk Reset Database ---
def show_reset_db():
    st.subheader("🔥 Reset Database")
    if st.button("⬅️ Kembali ke Menu Admin"):
        st.session_state.admin_view = 'menu'
        st.rerun()
    st.markdown("---")
    
    st.error("**PERINGATAN SUPER PENTING!** Tindakan ini akan **MENGHAPUS SEMUA DATA** di aplikasi (siswa, transaksi, tagihan, dll.) secara permanen dan tidak bisa dikembalikan. Lakukan hanya jika Anda benar-benar yakin.")
    
    st.markdown("---")
    
    confirmation_text = "SAYA YAKIN INGIN MENGHAPUS SEMUA DATA"
    
    st.write("Untuk melanjutkan, ketik kalimat persis seperti di bawah ini ke dalam kotak teks:")
    st.code(confirmation_text)
    
    user_input = st.text_input("Ketik kalimat konfirmasi di sini:")
    
    # Tombol Reset akan aktif jika input pengguna cocok dengan teks konfirmasi
    is_disabled = (user_input != confirmation_text)
    
    if st.button("RESET DATABASE SEKARANG", type="primary", disabled=is_disabled):
        try:
            db_file = "fatpay.db"
            if os.path.exists(db_file):
                os.remove(db_file)
                st.success("Database berhasil direset! Aplikasi akan dimulai ulang dengan data kosong.")
                st.balloons()
                st.rerun()
            else:
                st.warning("File database tidak ditemukan, tidak ada yang perlu direset.")
        except Exception as e:
            st.error(f"Gagal mereset database: {e}")


# --- Fungsi Render Utama untuk Modul Admin ---
def render():
    st.title("⚙️ Modul Admin")
    if 'admin_view' not in st.session_state:
        st.session_state.admin_view = 'menu'

    if st.session_state.admin_view == 'menu':
        if st.button("⬅️ Kembali ke Menu Utama"):
            st.session_state.page = 'home'
            st.rerun()
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("👥 Data User"): st.session_state.admin_view = 'data_user'; st.rerun()
            if st.button("🔑 Ganti Password"): st.session_state.admin_view = 'ganti_password'; st.rerun()
        with col2:
            if st.button("🏢 Profil Lembaga"): st.session_state.admin_view = 'profil_lembaga'; st.rerun()
            if st.button("💾 Backup Database"): st.session_state.admin_view = 'backup_db'; st.rerun()
        with col3:
            if st.button("🔄 Restore Database"): st.session_state.admin_view = 'restore_db'; st.rerun()
            # (PERUBAHAN) Mengaktifkan Tombol Reset
            if st.button("🔥 Reset Database"): st.session_state.admin_view = 'reset_db'; st.rerun()
            
    elif st.session_state.admin_view == 'data_user': show_data_user()
    elif st.session_state.admin_view == 'ganti_password': show_ganti_password()
    elif st.session_state.admin_view == 'backup_db': show_backup_db()
    elif st.session_state.admin_view == 'restore_db': show_restore_db()
    elif st.session_state.admin_view == 'profil_lembaga': show_profil_lembaga()
    # (BARU) Menambahkan rute untuk halaman baru
    elif st.session_state.admin_view == 'reset_db':
        show_reset_db()