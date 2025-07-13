import streamlit as st
import pandas as pd
from utils import db_functions as db
from utils import config_manager as cfg
import shutil
from datetime import datetime
import os

# --- FUNGSI SUB-HALAMAN DENGAN PENINGKATAN UI ---

def show_data_user():
    st.subheader("Kelola Data Pengguna Aplikasi")
    
    with st.expander("➕ Tambah User Baru"):
        with st.form("form_tambah_user", clear_on_submit=True):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["admin", "operator"])
            if st.form_submit_button("Tambah User"):
                if new_username and new_password:
                    with st.spinner("Menambahkan user..."):
                        conn = db.create_connection()
                        if db.tambah_user(conn, new_username, new_password, new_role):
                            st.toast(f"✅ User '{new_username}' berhasil ditambahkan.")
                        else:
                            st.error(f"Gagal! Username '{new_username}' sudah ada.")
                        conn.close()
                    st.rerun()
                else:
                    st.warning("Username dan Password tidak boleh kosong.")
                    
    with st.spinner("Memuat daftar pengguna..."):
        conn = db.create_connection()
        users_data = db.get_all_users(conn)
        conn.close()
        
    st.write("**Daftar Pengguna:**")
    df_users = pd.DataFrame(users_data, columns=['ID', 'Username', 'Role'])
    st.dataframe(df_users, use_container_width=True, hide_index=True)
    
    with st.expander("✏️ Reset Password atau Hapus Pengguna"):
        # Menyaring agar user tidak bisa mengedit/menghapus dirinya sendiri
        user_list = {user[1]: user[1] for user in users_data if user[1] != st.session_state.get('username')}
        if not user_list:
            st.info("Tidak ada pengguna lain yang bisa diubah atau dihapus.")
            return
            
        selected_user = st.selectbox("Pilih username", options=user_list.keys())
        if selected_user:
            with st.form(f"form_edit_{selected_user}"):
                st.write(f"Reset Password untuk **{selected_user}**")
                reset_password = st.text_input("Masukkan Password Baru", type="password")
                if st.form_submit_button("Reset Password"):
                    with st.spinner(f"Mereset password untuk {selected_user}..."):
                        conn = db.create_connection()
                        db.update_user_password(conn, selected_user, reset_password)
                        conn.close()
                    st.toast(f"✅ Password untuk user '{selected_user}' berhasil direset.")
            
            if st.button(f"❌ Hapus User: {selected_user}", type="primary"):
                with st.spinner(f"Menghapus user {selected_user}..."):
                    conn = db.create_connection()
                    db.hapus_user(conn, selected_user)
                    conn.close()
                st.toast(f"🗑️ User '{selected_user}' telah dihapus.")
                st.rerun()

def show_ganti_password():
    st.subheader("🔑 Ubah Password Anda")
    
    with st.form("form_ganti_password"):
        username = st.session_state.get('username', '')
        st.text_input("Nama User", value=username, disabled=True)
        password_lama = st.text_input("Password Lama", type="password")
        password_baru = st.text_input("Password Baru", type="password")
        konfirmasi_password = st.text_input("Konfirmasi Password Baru", type="password")
        
        if st.form_submit_button("Simpan Password Baru"):
            if not all([password_lama, password_baru, konfirmasi_password]):
                st.error("Semua kolom harus diisi.")
            elif password_baru != konfirmasi_password:
                st.error("Password Baru dan Konfirmasi tidak cocok.")
            else:
                with st.spinner("Memverifikasi dan menyimpan..."):
                    conn = db.create_connection()
                    user_role = db.check_login(conn, username, password_lama)
                    if user_role:
                        db.update_user_password(conn, username, password_baru)
                        st.success("✅ Password Anda berhasil diubah!")
                    else:
                        st.error("Password Lama yang Anda masukkan salah.")
                    conn.close()

def show_backup_db():
    st.subheader("💾 Backup Database")
    st.info("Fitur ini akan membuat salinan file database Anda saat ini (`fatpay.db`). Simpan file ini di tempat yang aman.")
    
    if st.button("Buat File Backup Sekarang", type="primary", use_container_width=True):
        source_db = "fatpay.db"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_fatpay_{timestamp}.db"
        with st.spinner("Membuat file backup..."):
            try:
                shutil.copyfile(source_db, backup_filename)
                st.success(f"File backup '{backup_filename}' berhasil dibuat!")
                with open(backup_filename, "rb") as fp:
                    st.download_button(label="📥 Unduh File Backup", data=fp, file_name=backup_filename, mime="application/octet-stream")
            except Exception as e:
                st.error(f"Terjadi kesalahan saat membuat backup: {e}")

def show_restore_db():
    st.subheader("🔄 Restore Database")
    st.error("**PERINGATAN:** Merestore database akan **MENGGANTI SEMUA DATA** yang ada saat ini dengan data dari file backup. Tindakan ini tidak bisa dibatalkan.")
    
    with st.container(border=True):
        uploaded_file = st.file_uploader("Pilih file backup database (.db) yang valid", type=['db'])
        if uploaded_file is not None:
            if st.button("Lakukan Restore Sekarang", type="primary"):
                with st.spinner("Merestore database... Aplikasi akan dimulai ulang setelah selesai."):
                    destination_db = "fatpay.db"
                    try:
                        with open(destination_db, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        st.success("Database berhasil direstore!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Terjadi kesalahan saat merestore database: {e}")

def show_profil_lembaga():
    st.subheader("🏢 Pengaturan Profil Lembaga")
    
    with st.form("form_profil_lembaga"):
        config = cfg.load_config()
        st.write("**Detail Lembaga**")
        nama_lembaga = st.text_input("Nama Lembaga", value=config.get("nama_lembaga", ""))
        alamat = st.text_area("Alamat", value=config.get("alamat", ""))
        telp = st.text_input("No. Telp/Fax", value=config.get("telp", ""))
        website = st.text_input("Website / Email", value=config.get("website", ""))
        st.markdown("---")
        st.write("**Logo**")
        logo_saat_ini = config.get("logo_path", "logo.png")
        if os.path.exists(logo_saat_ini):
            st.image(logo_saat_ini, width=100)
        uploaded_logo = st.file_uploader("Unggah Logo Baru (Kosongkan jika tidak ingin ganti)", type=['png', 'jpg'])
        
        if st.form_submit_button("Simpan Pengaturan"):
            with st.spinner("Menyimpan pengaturan..."):
                if uploaded_logo is not None:
                    with open(logo_saat_ini, "wb") as f:
                        f.write(uploaded_logo.getbuffer())
                new_config = {"nama_lembaga": nama_lembaga, "alamat": alamat, "telp": telp, "website": website, "logo_path": logo_saat_ini}
                cfg.save_config(new_config)
            st.toast("✅ Pengaturan profil lembaga berhasil disimpan!")

def show_reset_db():
    st.subheader("🔥 Reset Database")
    st.error("**PERINGATAN SUPER PENTING!** Tindakan ini akan **MENGHAPUS SEMUA DATA** di aplikasi secara permanen dan tidak bisa dikembalikan.")
    with st.container(border=True):
        confirmation_text = "SAYA YAKIN INGIN MENGHAPUS SEMUA DATA"
        st.write("Untuk melanjutkan, ketik kalimat persis seperti di bawah ini ke dalam kotak teks:")
        st.code(confirmation_text)
        user_input = st.text_input("Ketik kalimat konfirmasi di sini:", key="reset_confirm_input")
        
        is_disabled = (user_input != confirmation_text)
        if st.button("RESET DATABASE SEKARANG", type="primary", disabled=is_disabled):
            with st.spinner("Menghapus database... Aplikasi akan dimulai ulang."):
                try:
                    db_file = "fatpay.db"
                    if os.path.exists(db_file):
                        os.remove(db_file)
                    st.success("Database berhasil direset!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal mereset database: {e}")

# --- Fungsi Render Utama untuk Modul Admin ---
def render():
    # Menambahkan CSS untuk UI yang konsisten
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
            div[data-testid="stExpander"] {
                background-color: rgba(0, 0, 0, 0.7) !important;
                border: 1px solid #495057 !important;
                border-radius: 12px !important;
                padding: 1.5rem !important;
                box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            }

            .st-emotion-cache-1d8vwwt:hover {
                transform: translateY(-5px);
                box-shadow: 0 12px 28px rgba(0,0,0,0.2);
            }

            /* Judul kartu dan aksen biru */
            .st-emotion-cache-1d8vwwt h5 {
                color: #FFFFFF !important;
                font-weight: 600;
                position: relative;
                padding-left: 20px;
            }
            .st-emotion-cache-1d8vwwt h5::before {
                content: '';
                position: absolute;
                left: 0;
                top: 50%;
                transform: translateY(-50%);
                width: 8px;
                height: 100%;
                background-color: #007BFF;
                border-radius: 4px;
            }
            
            /* Deskripsi kartu */
            .st-emotion-cache-1d8vwwt p {
                color: #E0E0E0 !important;
                flex-grow: 1; /* Mendorong tombol ke bawah */
            }
            
            /* Tombol di dalam kartu */
            .st-emotion-cache-1d8vwwt .stButton > button {
                background-color: #007BFF !important;
                color: white !important;
            }
            
            /* Tombol umum di luar kartu */
            .stButton:not(.st-emotion-cache-1d8vwwt .stButton) > button {
                /* Gaya untuk tombol lain jika diperlukan */
            }

        </style>
        """, unsafe_allow_html=True)

    st.title("⚙️ Modul Admin")
    
    if 'admin_view' not in st.session_state:
        st.session_state.admin_view = 'menu'

    if st.session_state.admin_view != 'menu':
        if st.button("⬅️ Kembali ke Menu Admin"):
            st.session_state.admin_view = 'menu'
            st.rerun()
        st.markdown("---")

    if st.session_state.admin_view == 'menu':
        st.markdown("---")
        menu_options = {
            'data_user': {"label": "👥 Data User", "desc": "Tambah, edit, dan hapus akun pengguna."},
            'ganti_password': {"label": "🔑 Ganti Password", "desc": "Ubah password login Anda saat ini."},
            'profil_lembaga': {"label": "🏢 Profil Lembaga", "desc": "Atur nama, alamat, dan logo sekolah."},
            'backup_db': {"label": "💾 Backup Database", "desc": "Buat cadangan semua data aplikasi."},
            'restore_db': {"label": "🔄 Restore Database", "desc": "Kembalikan data dari file backup."},
            'reset_db': {"label": "🔥 Reset Database", "desc": "Hapus semua data dan mulai dari awal."}
        }
        items = list(menu_options.items())
        num_cols = 3
        for i in range(0, len(items), num_cols):
            cols = st.columns(num_cols)
            row_items = items[i:i+num_cols]
            for j, (view, content) in enumerate(row_items):
                with cols[j]:
                    container = st.container(border=True)
                    container.markdown(f"<h5>{content['label']}</h5>", unsafe_allow_html=True)
                    container.markdown(f"<p>{content['desc']}</p>", unsafe_allow_html=True)
                    if container.button("Pilih Menu", key=f"btn_admin_{view}", use_container_width=True):
                        st.session_state.admin_view = view
                        st.rerun()
        st.markdown("---")
        if st.button("⬅️ Kembali ke Menu Utama"):
            st.session_state.page = 'home'
            if 'page' in st.query_params:
                st.query_params.clear()
            st.rerun()
    
    # Router untuk sub-halaman
    else:
        view_function_map = {
            'data_user': show_data_user, 'ganti_password': show_ganti_password,
            'backup_db': show_backup_db, 'restore_db': show_restore_db,
            'profil_lembaga': show_profil_lembaga, 'reset_db': show_reset_db
        }
        render_function = view_function_map.get(st.session_state.admin_view)
        if render_function:
            render_function()