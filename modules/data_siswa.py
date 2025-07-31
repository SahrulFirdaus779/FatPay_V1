import streamlit as st
import pandas as pd
from utils import db_functions as db
import io
import re
import barcode
import json
from barcode.writer import ImageWriter
import base64
from datetime import datetime # DITAMBAHKAN untuk tanggal & jam cetak

# --- FUNGSI CACHING UNTUK PERFORMA ---
def load_svg(filepath):
    """Membaca dan mengembalikan konten dari file SVG."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="currentColor" class="bi bi-question-circle" viewBox="0 0 16 16"><path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/><path d="M5.255 5.786a.237.237 0 0 0 .241.247h.825c.138 0 .248-.113.266-.25.09-.656.54-1.134 1.342-1.134.686 0 1.314.343 1.314 1.168 0 .635-.374.927-.965 1.371-.673.489-1.206 1.06-1.168 1.987l.003.217a.25.25 0 0 0 .25.246h.811a.25.25 0 0 0 .25-.25v-.105c0-.718.273-.927 1.01-1.486.609-.463 1.244-1.057 1.244-2.056 0-1.511-1.276-2.241-2.673-2.241-1.267 0-2.655.59-2.75 2.286zm1.557 5.763c0 .533.425.927 1.01.927.609 0 1.028-.394 1.028-.927 0-.552-.42-.94-1.029-.94-.584 0-1.009.388-1.009.94z"/></svg>"""

@st.cache_data(ttl=600)
def get_semua_kelas_cached():
    """Mengambil daftar kelas dari DB dan menyimpannya di cache."""
    conn = db.create_connection()
    data = db.get_semua_kelas(conn)
    conn.close()
    return data

@st.cache_data(ttl=600)
def get_semua_angkatan_cached():
    """Mengambil daftar angkatan dari DB dan menyimpannya di cache."""
    conn = db.create_connection()
    data = db.get_semua_angkatan(conn)
    conn.close()
    return data

# --- FUNGSI BANTUAN ---
def format_status_badge(status):
    """Mengubah teks status menjadi badge HTML berwarna."""
    colors = {
        "Aktif": "#DFF2BF", "Lulus": "#BDE5F8", "Pindah": "#F7F5A8",
        "Tinggal Kelas": "#FFC0CB", "Non Aktif": "#E0E0E0"
    }
    bg_color = colors.get(status, "#E0E0E0")
    badge_style = f"background-color: {bg_color}; color: #333; padding: 5px 12px; border-radius: 15px; text-align: center; font-weight: 600; font-size: 12px; display: inline-block;"
    return f'<div style="{badge_style}">{status}</div>'

# --- FUNGSI BANTUAN BARU ---
def terbilang(n):
    """Mengubah angka menjadi tulisan. Memerlukan implementasi yang lebih lengkap."""
    # Placeholder sederhana untuk demonstrasi
    if n == 1175000:
        return "Satu Juta Seratus Tujuh Puluh Lima Ribu Rupiah"
    return "Fungsi terbilang belum diimplementasikan sepenuhnya."

def load_config():
    """Membaca dan memuat data dari file config.json."""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Mengembalikan nilai default jika file tidak ada atau error
        st.error("File config.json tidak ditemukan atau formatnya salah.")
        return {
            "nama_lembaga": "NAMA LEMBAGA",
            "alamat": "Alamat Lembaga",
            "telp": "-",
            "website": "-",
            "logo_path": "logo.png"
        }
    
# (Ganti fungsi terbilang lama Anda dengan yang ini)
def terbilang(n):
    """Mengubah angka integer menjadi format kalimat terbilang dalam Bahasa Indonesia."""
    n = int(n) # Pastikan input adalah integer
    if n < 0:
        return "Minus " + terbilang(abs(n))
    
    satuan = ["", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan"]
    
    if n < 10:
        return satuan[n]
    if n == 10:
        return "sepuluh"
    if n == 11:
        return "sebelas"
    if n < 20:
        return terbilang(n % 10) + " belas"
    if n < 100:
        return satuan[n // 10] + " puluh " + terbilang(n % 10)
    if n < 200:
        return "seratus " + terbilang(n % 100)
    if n < 1000:
        return terbilang(n // 100) + " ratus " + terbilang(n % 100)
    if n < 2000:
        return "seribu " + terbilang(n % 1000)
    if n < 1000000:
        return terbilang(n // 1000) + " ribu " + terbilang(n % 1000)
    if n < 1000000000:
        return terbilang(n // 1000000) + " juta " + terbilang(n % 1000000)
    if n < 1000000000000:
        return terbilang(n // 1000000000) + " miliar " + terbilang(n % 1000000000)
    
    # Menghapus spasi ganda dan merapikan output
    hasil = ' '.join(terbilang(n).split()).title()
    return hasil + " Rupiah"

# --- FUNGSI SUB-HALAMAN ---

def show_master_kelas():
    st.subheader("Master Data Kelas")

    # Inisialisasi session state untuk konfirmasi hapus
    if 'confirm_delete_kelas_id' not in st.session_state:
        st.session_state.confirm_delete_kelas_id = None

    # --- CSS untuk Tabel Kustom ---
    st.markdown("""
    <style>
        .styled-table { width: 100%; border-collapse: collapse; }
        .styled-table thead th { background-color: #007bff; color: white; text-align: left; padding: 12px 15px; }
        .styled-table tbody tr { border-bottom: 1px solid #dddddd; }
        .styled-table tbody tr:nth-of-type(even) { background-color: #f3f3f3; }
        .styled-table tbody tr:hover { background-color: #e6f7ff; }
        .styled-table td { padding: 12px 15px; }
    </style>
    """, unsafe_allow_html=True)

    # --- Form Tambah Kelas dengan Layout Kolom ---
    with st.form("form_tambah_kelas", clear_on_submit=True):
        st.markdown("<h6>Tambah Kelas Baru</h6>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            angkatan = st.text_input("Angkatan*", help="Contoh: 2024, 2025")
        with c2:
            nama_kelas = st.text_input("Nama Kelas*", help="Contoh: X-A, XI-IPA-1")
        with c3:
            tahun_ajaran = st.text_input("Tahun Ajaran*", help="Contoh: 2024/2025")

        if st.form_submit_button("➕ Tambah Kelas"):
            if angkatan and nama_kelas and tahun_ajaran:
                with st.spinner("Menyimpan..."):
                    conn = db.create_connection()
                    db.tambah_kelas(conn, angkatan, nama_kelas, tahun_ajaran)
                    conn.close()
                st.cache_data.clear() # Membersihkan cache agar data baru muncul
                st.toast(f"✅ Kelas '{nama_kelas}' berhasil ditambahkan.")
                st.rerun()
            else:
                st.warning("Input dengan tanda (*) tidak boleh kosong.")

    st.markdown("---")

    # --- Menampilkan Daftar Kelas dengan Tabel Kustom ---
    st.markdown("<h6>Daftar Kelas Tersedia</h6>", unsafe_allow_html=True)
    with st.spinner("Memuat data kelas..."):
        conn = db.create_connection()
        # Menggunakan fungsi baru untuk mendapatkan jumlah siswa
        list_kelas = db.get_semua_kelas_dengan_jumlah_siswa(conn)
        conn.close()

    if list_kelas:
        df_kelas = pd.DataFrame(list_kelas, columns=['ID', 'Angkatan', 'Nama Kelas', 'Tahun Ajaran', 'Jumlah Siswa'])
        st.markdown(df_kelas.to_html(escape=False, index=False, classes="styled-table"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True) # Memberi jarak

        # --- Expander Edit dan Hapus dengan UX yang Ditingkatkan ---
        with st.expander("✏️ Edit atau Hapus Data Kelas"):
            # Membuat label dropdown lebih informatif
            kelas_dict = {f"{nama} ({angkatan}) - [{jum_siswa} siswa]": id_kelas for id_kelas, angkatan, nama, tahun, jum_siswa in list_kelas}
            selected_kelas_label = st.selectbox("Pilih kelas untuk diubah/dihapus", options=kelas_dict.keys())
            id_kelas_terpilih = kelas_dict.get(selected_kelas_label)

            if id_kelas_terpilih:
                # Mengambil detail lengkap dari kelas yang dipilih
                selected_details = next((item for item in list_kelas if item[0] == id_kelas_terpilih), None)
                
                if selected_details:
                    id_val, angkatan_val, nama_val, tahun_val, jumlah_siswa_val = selected_details

                    # Form Edit
                    with st.form(f"form_edit_kelas_{id_kelas_terpilih}"):
                        st.write(f"**Edit Kelas: {nama_val} ({angkatan_val})**")
                        edit_angkatan = st.text_input("Angkatan Baru", value=angkatan_val)
                        edit_nama = st.text_input("Nama Kelas Baru", value=nama_val)
                        edit_tahun = st.text_input("Tahun Ajaran Baru", value=tahun_val)
                        
                        if st.form_submit_button("Simpan Perubahan"):
                            with st.spinner("Memperbarui data..."):
                                conn = db.create_connection()
                                db.update_kelas(conn, id_kelas_terpilih, edit_angkatan, edit_nama, edit_tahun)
                                conn.close()
                            st.cache_data.clear()
                            st.toast("✅ Data kelas berhasil diperbarui!")
                            st.rerun()

                    st.markdown("---")
                    
                    # --- Logika Hapus dengan Pengecekan dan Konfirmasi ---
                    if jumlah_siswa_val > 0:
                        st.error(f"Tidak bisa menghapus kelas ini karena memiliki {jumlah_siswa_val} siswa. Pindahkan atau Luluskan siswa terlebih dahulu.")
                    else:
                        # Jika konfirmasi hapus untuk kelas ini sedang aktif
                        if st.session_state.confirm_delete_kelas_id == id_kelas_terpilih:
                            st.warning(f"**Anda yakin ingin menghapus kelas: {nama_val} ({angkatan_val})?**")
                            c1_del, c2_del = st.columns(2)
                            with c1_del:
                                if st.button("🔴 Ya, Hapus", use_container_width=True):
                                    with st.spinner("Menghapus..."):
                                        conn = db.create_connection()
                                        db.hapus_kelas(conn, id_kelas_terpilih)
                                        conn.close()
                                    st.cache_data.clear()
                                    st.session_state.confirm_delete_kelas_id = None # Reset state
                                    st.toast(f"🗑️ Kelas telah dihapus.")
                                    st.rerun()
                            with c2_del:
                                if st.button("Batalkan", use_container_width=True):
                                    st.session_state.confirm_delete_kelas_id = None # Reset state
                                    st.rerun()
                        else:
                            # Tombol hapus utama yang akan memicu konfirmasi
                            if st.button(f"❌ Hapus Kelas: {nama_val}", type="primary", use_container_width=True):
                                st.session_state.confirm_delete_kelas_id = id_kelas_terpilih
                                st.rerun()
    else:
        st.info("Belum ada data kelas yang ditambahkan.")

def show_daftar_siswa():
    st.subheader("Data Induk Siswa")

    # Inisialisasi session state
    if 'confirm_delete_nis' not in st.session_state:
        st.session_state.confirm_delete_nis = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1

    # --- CSS Kustom ---
    st.markdown("""
    <style>
        .table-container { 
            /* Tinggi tidak lagi diatur di sini agar menyesuaikan konten per halaman */
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin-top: 1em;
        }
        .styled-table { width: 100%; border-collapse: collapse; }
        .styled-table thead th { background-color: #007bff; color: white; text-align: left; padding: 12px 15px; position: sticky; top: 0; z-index: 1; }
        .styled-table tbody tr { border-bottom: 1px solid #dddddd; }
        .styled-table tbody tr:nth-of-type(even) { background-color: #f3f3f3; }
        .styled-table tbody tr:hover { background-color: #e6f7ff; }
        .styled-table td { padding: 12px 15px; }
    </style>
    """, unsafe_allow_html=True)

    # --- Filter Utama ---
    list_angkatan = ["Semua Angkatan"] + get_semua_angkatan_cached()
    list_kelas = get_semua_kelas_cached()
    kelas_dict = {f"{angkatan} - {nama} ({tahun})": id_kelas for id_kelas, angkatan, nama, tahun in list_kelas}

    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 2, 2])
        with c1:
            selected_angkatan = st.selectbox("Filter Angkatan", options=list_angkatan)
        with c2:
            pilihan_kelas_filter = ["Semua Kelas"] + list(kelas_dict.keys())
            selected_kelas_filter_nama = st.selectbox("Filter per Kelas", options=pilihan_kelas_filter)
        with c3:
            search_term = st.text_input("Cari Nama atau NIS Siswa", placeholder="Ketik untuk mencari...")

    id_kelas_filter = None if selected_kelas_filter_nama == "Semua Kelas" else kelas_dict.get(selected_kelas_filter_nama)
    angkatan_filter = None if selected_angkatan == "Semua Angkatan" else selected_angkatan

    with st.spinner("Memuat data siswa..."):
        conn = db.create_connection()
        list_siswa = db.get_filtered_siswa_detailed(conn, angkatan=angkatan_filter, kelas_id=id_kelas_filter, search_term=search_term)
        conn.close()

    st.markdown("---")
    
    if list_siswa:
        list_siswa.reverse()
        
        # --- LOGIKA PAGINASI ---
        items_per_page = 10  # Atur jumlah siswa per halaman
        total_items = len(list_siswa)
        total_pages = (total_items + items_per_page - 1) // items_per_page

        # Pastikan halaman saat ini valid
        if st.session_state.current_page > total_pages:
            st.session_state.current_page = 1
        
        start_idx = (st.session_state.current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        
        paginated_data = list_siswa[start_idx:end_idx]
        
        st.write(f"**Menampilkan {len(paginated_data)} dari {total_items} total data siswa:**")
        
        df_siswa = pd.DataFrame(paginated_data, columns=['NIS', 'NIK Siswa', 'NISN', 'Nama Lengkap', 'L/P', 'No. WA Ortu', 'Kelas', 'Status', 'Angkatan'])
        df_siswa['Status'] = df_siswa['Status'].apply(format_status_badge)
        table_html = df_siswa.to_html(escape=False, index=False, classes="styled-table")
        st.markdown(f'<div class="table-container">{table_html}</div>', unsafe_allow_html=True)

        # --- NAVIGASI PAGINASI ---
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([3, 2, 3])

        with col1:
            if st.session_state.current_page > 1:
                if st.button("⬅️ Halaman Sebelumnya"):
                    st.session_state.current_page -= 1
                    st.rerun()
        
        with col2:
            st.write(f"Halaman **{st.session_state.current_page}** dari **{total_pages}**")

        with col3:
            if st.session_state.current_page < total_pages:
                if st.button("Halaman Berikutnya ➡️"):
                    st.session_state.current_page += 1
                    st.rerun()

    else:
        st.info("Tidak ada data siswa yang cocok dengan filter Anda.")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Expander Tambah dan Edit/Hapus (Kode tetap sama) ---
    with st.expander("➕ Tambah Siswa Baru"):
        # ... (Kode form tambah siswa Anda tetap sama)
        with st.form("form_tambah_siswa", clear_on_submit=True):
            st.markdown("<h6>Informasi Pribadi Siswa</h6>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            nama_lengkap = c1.text_input("Nama Siswa*")
            jenis_kelamin = c2.selectbox("Jenis Kelamin (L/P)", ["L", "P"])
            nik_siswa = c1.text_input("NIK Siswa")
            nisn = c2.text_input("NISN")
            st.markdown("<h6>Informasi Akademik & Kontak</h6>", unsafe_allow_html=True)
            c3, c4 = st.columns(2)
            nis = c3.text_input("NO INDUK (NIS)*", help="NIS harus unik untuk setiap siswa.")
            selected_kelas_nama_tambah = c4.selectbox("Pilih Kelas*", options=list(kelas_dict.keys()), key="kelas_tambah")
            no_wa_ortu = st.text_input("No. WA Orang Tua")

            if st.form_submit_button("Tambah Siswa"):
                if nis and nama_lengkap and selected_kelas_nama_tambah:
                    id_kelas_terpilih_tambah = kelas_dict[selected_kelas_nama_tambah]
                    with st.spinner("Menyimpan data siswa..."):
                        conn = db.create_connection()
                        try:
                            db.tambah_siswa(conn, nis, nik_siswa, nisn, nama_lengkap, jenis_kelamin, no_wa_ortu, id_kelas_terpilih_tambah)
                            st.toast(f"✅ Siswa '{nama_lengkap}' berhasil ditambahkan.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal menambahkan siswa. Pastikan NIS unik. Error: {e}")
                        finally:
                            conn.close()
                else:
                    st.warning("Input dengan tanda (*) tidak boleh kosong.")

    if list_siswa:
        with st.expander("📝 Edit atau Hapus Data Siswa"):
            # ... (Kode expander edit/hapus Anda tetap sama)
            search_edit_term = st.text_input("Cari Siswa di bawah ini (Nama/NIS)", key="search_edit")
            
            if search_edit_term:
                list_siswa_for_edit = [s for s in list_siswa if search_edit_term.lower() in s[3].lower() or search_edit_term in s[0]]
            else:
                list_siswa_for_edit = list_siswa

            if not list_siswa_for_edit:
                st.warning("Siswa tidak ditemukan.")
            else:
                siswa_dict = {f"{nama} ({nis})": nis for nis, _, _, nama, *_, angkatan in list_siswa_for_edit}
                selected_siswa_nama = st.selectbox("Pilih siswa untuk diubah/dihapus", options=siswa_dict.keys(), key="edit_siswa_select")
                
                if selected_siswa_nama:
                    nis_terpilih = siswa_dict.get(selected_siswa_nama)
                    selected_details = next((item for item in list_siswa if item[0] == nis_terpilih), None)

                    if selected_details:
                        with st.form(f"form_edit_siswa_{nis_terpilih}"):
                            st.write(f"**Edit Siswa: {selected_siswa_nama}**")
                            _, nik_val, nisn_val, nama_val, jk_val, no_wa_val, kelas_val, _, _ = selected_details
                            
                            edit_nik = st.text_input("NIK Siswa Baru", value=nik_val, key=f"nik_{nis_terpilih}")
                            edit_nisn = st.text_input("NISN Baru", value=nisn_val, key=f"nisn_{nis_terpilih}")
                            edit_nama = st.text_input("Nama Lengkap Baru", value=nama_val, key=f"nama_{nis_terpilih}")
                            
                            jk_options = ["L", "P"]
                            jk_index = jk_options.index(jk_val) if jk_val in jk_options else 0
                            edit_jk = st.selectbox("Jenis Kelamin Baru", options=jk_options, index=jk_index, key=f"jk_{nis_terpilih}")
                            
                            edit_no_wa = st.text_input("No. WA Orang Tua Baru", value=no_wa_val, key=f"wa_{nis_terpilih}")
                            
                            kelas_options = list(kelas_dict.keys())
                            current_kelas_nama = next((nama for nama in kelas_options if nama.startswith(str(kelas_val))), None)
                            kelas_index = kelas_options.index(current_kelas_nama) if current_kelas_nama in kelas_options else 0
                            edit_kelas_nama = st.selectbox("Kelas Baru", options=kelas_options, index=kelas_index, key=f"kelas_{nis_terpilih}")

                            if st.form_submit_button("Simpan Perubahan Siswa"):
                                id_kelas_baru = kelas_dict[edit_kelas_nama]
                                with st.spinner("Memperbarui data..."):
                                    conn = db.create_connection()
                                    db.update_siswa(conn, nis_terpilih, edit_nik, edit_nisn, edit_nama, edit_jk, edit_no_wa, id_kelas_baru)
                                    conn.close()
                                st.toast("✅ Data siswa berhasil diperbarui!")
                                st.rerun()

                        st.markdown("---")

                        if st.session_state.confirm_delete_nis == nis_terpilih:
                            st.warning(f"**Anda yakin ingin menghapus data permanen untuk siswa: {selected_siswa_nama}?**")
                            c1_del, c2_del = st.columns(2)
                            with c1_del:
                                if st.button("🔴 Ya, Hapus Sekarang", use_container_width=True):
                                    with st.spinner("Menghapus data siswa..."):
                                        conn = db.create_connection()
                                        db.hapus_siswa(conn, nis_terpilih)
                                        conn.close()
                                    st.session_state.confirm_delete_nis = None
                                    st.toast(f"🗑️ Siswa {selected_siswa_nama} telah dihapus.")
                                    st.rerun()
                            with c2_del:
                                if st.button("Batalkan", use_container_width=True):
                                    st.session_state.confirm_delete_nis = None
                                    st.rerun()
                        else:
                            if st.button(f"❌ Hapus Siswa: {selected_siswa_nama}", type="primary", use_container_width=True):
                                st.session_state.confirm_delete_nis = nis_terpilih
                                st.rerun()

def show_import_excel():
    st.subheader("📥 Import Data Siswa dari Excel")

    # --- CSS untuk Tabel Kustom ---
    st.markdown("""
    <style>
        .styled-table { width: 100%; border-collapse: collapse; margin-top: 1em; }
        .styled-table thead th { background-color: #28a745; color: white; text-align: left; padding: 12px 15px; }
        .styled-table tbody tr { border-bottom: 1px solid #dddddd; }
        .styled-table tbody tr:nth-of-type(even) { background-color: #f3f3f3; }
        .styled-table tbody tr:hover { background-color: #d4edda; }
        .styled-table td { padding: 12px 15px; }
    </style>
    """, unsafe_allow_html=True)

    # --- Halaman Hasil Setelah Proses Impor Berhasil ---
    if 'import_sukses_info' in st.session_state:
        info = st.session_state.import_sukses_info
        st.success(f"**Impor Berhasil!** Sebanyak **{info['jumlah']} siswa** telah berhasil ditambahkan ke dalam sistem.")
        st.markdown("#### Rangkuman Siswa yang Diimpor")

        df_hasil = pd.DataFrame(info['list_siswa_impor'])
        table_html_hasil = df_hasil.to_html(escape=False, index=False, classes="styled-table")
        st.markdown(table_html_hasil, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅️ Impor File Lain"):
            del st.session_state.import_sukses_info
            st.rerun()
        return

    # --- Tampilan Halaman Utama ---
    st.info("Fitur ini akan secara otomatis mencocokkan Angkatan dan Tingkat Kelas yang Anda pilih dengan kolom 'KELAS' di file Excel.")

    with st.expander("Langkah 1: Siapkan File Excel", expanded=True):
        st.write("Pastikan file Excel Anda memiliki kolom **nis**, **nama_lengkap**, dan **KELAS** (berisi A, B, C, dst.)")
        template_df = pd.DataFrame({
            'nis': ['1001'], 'nama_lengkap': ['Budi Santoso'], 'KELAS': ['A'],
            'nik_siswa': ['3524...'], 'nisn': ['001...'], 'jenis_kelamin': ['L'], 'no_wa_ortu': ['0812...']
        })
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            template_df.to_excel(writer, index=False, sheet_name='Sheet1')
        
        st.download_button(
            label="📥 Unduh Template Excel",
            data=output.getvalue(),
            file_name="template_siswa_dengan_kelas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with st.expander("Langkah 2: Unggah dan Validasi File", expanded=True):
        conn = db.create_connection()
        list_angkatan = db.get_semua_angkatan(conn)
        
        if not list_angkatan:
            st.warning("Belum ada data Angkatan di Master Kelas.")
            conn.close()
            return

        c1, c2 = st.columns(2)
        with c1:
            selected_angkatan = st.selectbox("Pilih Angkatan*", options=list_angkatan)
        with c2:
            tingkat_kelas = st.text_input("Input Tingkat Kelas*", help="Contoh: 7, 8, X")

        uploaded_file = st.file_uploader("Pilih file Excel Anda", type=['xlsx'])

        if uploaded_file and selected_angkatan and tingkat_kelas:
            try:
                df_upload = pd.read_excel(uploaded_file, dtype=str).fillna('')
                
                column_mapping = {
                    'NO INDUK': 'nis', 'Nama Siswa': 'nama_lengkap', 'NIK Siswa': 'nik_siswa', 'NISN': 'nisn',
                    'L/P': 'jenis_kelamin', 'No Whatsapp': 'no_wa_ortu', 'KELAS': 'kelas_suffix'
                }
                df_upload.rename(columns=lambda c: column_mapping.get(c.strip(), c.strip()), inplace=True)

                required_cols = {'nis', 'nama_lengkap', 'kelas_suffix'}
                if not required_cols.issubset(df_upload.columns):
                    st.error(f"File Excel harus memiliki kolom: nis, nama_lengkap, dan KELAS.")
                    return

                semua_kelas_db = db.get_semua_kelas(conn)
                kelas_lookup = {(k[1], k[2]): k[0] for k in semua_kelas_db}
                id_ke_nama_kelas = {k[0]: k[2] for k in semua_kelas_db} # Untuk halaman hasil
                list_nis_db = {row[0] for row in db.get_filtered_siswa_detailed(conn)}
                conn.close()

                validation_results, list_data_valid = [], []
                for _, row in df_upload.iterrows():
                    nis, nama, kelas_suffix = row.get('nis'), row.get('nama_lengkap'), row.get('kelas_suffix')
                    nama_kelas_lengkap = f"{tingkat_kelas.strip()}{kelas_suffix.strip()}"
                    id_kelas_cocok = kelas_lookup.get((selected_angkatan, nama_kelas_lengkap))
                    
                    status = ""
                    if not nis or not nama or not kelas_suffix: status = "Data Tidak Lengkap"
                    elif not id_kelas_cocok: status = f"Kelas '{nama_kelas_lengkap}' tidak ditemukan"
                    elif nis in list_nis_db: status = "NIS Duplikat"
                    else:
                        status = "Siap Diimpor"
                        list_data_valid.append((row, id_kelas_cocok))
                    validation_results.append(status)
                
                df_upload['status_validasi'] = validation_results
                
                st.write("**Pratinjau & Hasil Validasi Data:**")
                def style_df(df):
                    def highlight_status(s):
                        if s == 'Siap Diimpor': return 'background-color: #d4edda; color: #155724;'
                        if 'Duplikat' in s: return 'background-color: #fff3cd; color: #856404;'
                        if 'Tidak' in s: return 'background-color: #f8d7da; color: #721c24;'
                        return ''
                    return df.style.applymap(highlight_status, subset=['status_validasi'])
                st.dataframe(style_df(df_upload), use_container_width=True)

                siap_impor = validation_results.count("Siap Diimpor")
                st.markdown("---")
                st.metric("✅ Siap Diimpor", f"{siap_impor} data")
                
                if siap_impor > 0:
                    st.markdown("---")
                    if st.button(f"🚀 Proses Import {siap_impor} Data Baru Sekarang", type="primary"):
                        progress_bar = st.progress(0, text="Memulai proses import...")
                        conn = db.create_connection()
                        
                        # Siapkan data untuk halaman hasil
                        list_siswa_berhasil_impor = []

                        for i, (row, id_kelas) in enumerate(list_data_valid):
                            db.tambah_siswa(
                                conn=conn, nis=row.get('nis'), nik_siswa=row.get('nik_siswa'), nisn=row.get('nisn'),
                                nama_lengkap=row.get('nama_lengkap'), jenis_kelamin=row.get('jenis_kelamin'),
                                no_wa_ortu=row.get('no_wa_ortu'), id_kelas=id_kelas
                            )
                            # Tambahkan data ke daftar hasil
                            list_siswa_berhasil_impor.append({
                                'NIS': row.get('nis'),
                                'Nama Siswa': row.get('nama_lengkap'),
                                'Kelas': id_ke_nama_kelas.get(id_kelas, 'N/A')
                            })
                            progress_bar.progress((i + 1) / siap_impor, text=f"Mengimpor {row.get('nama_lengkap')}...")
                        
                        conn.close()

                        # Simpan hasil ke session state dan rerun untuk menampilkan halaman hasil
                        st.session_state.import_sukses_info = {
                            'jumlah': siap_impor,
                            'list_siswa_impor': list_siswa_berhasil_impor
                        }
                        st.rerun()

            except Exception as e:
                st.error(f"Terjadi kesalahan saat membaca atau memproses file: {e}")

def show_naik_kelas():
    st.subheader("⬆️ Posting Kenaikan Kelas")
    st.info("Gunakan fitur ini untuk memindahkan SEMUA siswa dari kelas asal ke kelas tujuan secara massal.")

    # --- CSS untuk Tabel Pratinjau ---
    st.markdown("""
    <style>
        .preview-table-container {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            background-color: #f9f9f9;
        }
        .preview-table { width: 100%; border-collapse: collapse; }
        .preview-table th, .preview-table td { padding: 8px 12px; border: 1px solid #ddd; text-align: left; }
        .preview-table th { background-color: #f2f2f2; }
    </style>
    """, unsafe_allow_html=True)

    # --- Pengambilan Data Kelas dengan Jumlah Siswa ---
    conn = db.create_connection()
    try:
        list_kelas_db = db.get_semua_kelas_dengan_jumlah_siswa(conn)
    except AttributeError:
        list_kelas_db_simple = db.get_semua_kelas(conn)
        list_kelas_db = [(k[0], k[1], k[2], k[3], '?') for k in list_kelas_db_simple]
        st.warning("Fungsi 'get_semua_kelas_dengan_jumlah_siswa' tidak ditemukan. Tampilan jumlah siswa dinonaktifkan.")
    conn.close()

    if len(list_kelas_db) < 2:
        st.warning("Anda memerlukan setidaknya 2 kelas untuk proses ini.")
        return

    kelas_options = {
        f"{nama} ({angkatan}) - [{jum_siswa} siswa]": id_kelas
        for id_kelas, angkatan, nama, tahun, jum_siswa in list_kelas_db
    }

    # --- LANGKAH 1: Pemilihan Kelas ---
    st.markdown("#### Langkah 1: Pilih Kelas Asal dan Tujuan")
    col1, col2 = st.columns(2)
    with col1:
        kelas_asal_label = st.selectbox(
            "Pilih kelas asal", options=list(kelas_options.keys()), key="kelas_asal", index=None, placeholder="Pilih kelas..."
        )
    with col2:
        if kelas_asal_label:
            pilihan_tujuan = [label for label in kelas_options.keys() if label != kelas_asal_label]
            kelas_tujuan_label = st.selectbox(
                "Pilih kelas tujuan", options=pilihan_tujuan, key="kelas_tujuan", index=None, placeholder="Pilih kelas..."
            )
        else:
            st.selectbox("Pilih kelas tujuan", options=[], disabled=True)

    st.markdown("---")

    # --- LANGKAH 2: Pratinjau dan Konfirmasi ---
    if kelas_asal_label and 'kelas_tujuan_label' in locals() and kelas_tujuan_label:
        id_kelas_asal = kelas_options[kelas_asal_label]
        id_kelas_tujuan = kelas_options[kelas_tujuan_label]

        conn = db.create_connection()
        siswa_di_kelas_asal = db.get_siswa_by_kelas(conn, id_kelas_asal)
        conn.close()

        if not siswa_di_kelas_asal:
            st.warning(f"Tidak ada siswa yang ditemukan di kelas **{kelas_asal_label}**.")
        else:
            st.markdown("#### Langkah 2: Pratinjau dan Konfirmasi Perubahan")
            st.success(f"Akan memindahkan **{len(siswa_di_kelas_asal)} siswa** dari **{kelas_asal_label.split(' - ')[0]}** ke **{kelas_tujuan_label.split(' - ')[0]}**.")
            
            df_siswa = pd.DataFrame(siswa_di_kelas_asal, columns=['NIS', 'Nama Siswa'])

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("##### **SEBELUM**")
                with st.container(border=True):
                    df_before = df_siswa.copy()
                    df_before['Kelas Asal'] = kelas_asal_label.split(' - ')[0]
                    st.dataframe(df_before, use_container_width=True, hide_index=True)
            with c2:
                st.markdown("##### **SESUDAH**")
                with st.container(border=True):
                    df_after = df_siswa.copy()
                    df_after['Kelas Tujuan'] = kelas_tujuan_label.split(' - ')[0]
                    st.dataframe(df_after, use_container_width=True, hide_index=True)

            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- Tombol Konfirmasi Final ---
            if st.button("✅ Konfirmasi dan Pindahkan Semua Siswa", type="primary"):
                with st.spinner(f"Memindahkan {len(siswa_di_kelas_asal)} siswa..."):
                    conn = db.create_connection()
                    for nis, nama in siswa_di_kelas_asal:
                        db.update_kelas_siswa(conn, nis, id_kelas_tujuan)
                    conn.close()
                
                st.success(f"Selesai! {len(siswa_di_kelas_asal)} siswa telah berhasil dipindahkan.")

def show_pindah_kelas():
    st.subheader("➡️ Proses Pindah Kelas Individual")

    # --- CSS untuk Tabel Kustom ---
    st.markdown("""
    <style>
        .styled-table { width: 100%; border-collapse: collapse; margin-top: 1em; }
        .styled-table thead th { background-color: #007bff; color: white; text-align: left; padding: 12px 15px; }
        .styled-table tbody tr { border-bottom: 1px solid #dddddd; }
        .styled-table tbody tr:nth-of-type(even) { background-color: #f3f3f3; }
        .styled-table tbody tr:hover { background-color: #e6f7ff; }
        .styled-table td { padding: 12px 15px; }
    </style>
    """, unsafe_allow_html=True)

    # Cek apakah ada proses transfer yang baru saja berhasil
    if 'transfer_sukses_info' in st.session_state:
        info = st.session_state.transfer_sukses_info
        
        st.success(f"**Berhasil!** {info['jumlah']} siswa telah dipindahkan ke kelas **{info['nama_kelas_tujuan']}**.")
        st.markdown(f"#### Daftar Siswa Saat Ini di Kelas **{info['nama_kelas_tujuan']}**")

        with st.spinner("Memuat data kelas tujuan..."):
            conn = db.create_connection()
            siswa_di_kelas_tujuan = db.get_siswa_by_kelas(conn, info['id_kelas_tujuan'])
            conn.close()
        
        if siswa_di_kelas_tujuan:
            df_tujuan = pd.DataFrame(siswa_di_kelas_tujuan, columns=['NIS', 'Nama Siswa'])
            # Menggunakan tabel HTML kustom yang sudah diberi warna
            table_html = df_tujuan.to_html(escape=False, index=False, classes="styled-table")
            st.markdown(table_html, unsafe_allow_html=True)
        else:
            st.info("Saat ini tidak ada siswa di kelas ini.")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅️ Lakukan Pemindahan Lain"):
            del st.session_state.transfer_sukses_info
            st.rerun()
        return

    st.info("Gunakan fitur ini untuk memindahkan satu atau beberapa siswa yang Anda pilih ke kelas lain.")

    if 'pindah_kelas_id_asal_sebelumnya' not in st.session_state:
        st.session_state.pindah_kelas_id_asal_sebelumnya = None

    conn = db.create_connection()
    try:
        list_kelas_db = db.get_semua_kelas_dengan_jumlah_siswa(conn)
    except AttributeError:
        list_kelas_db_simple = db.get_semua_kelas(conn)
        list_kelas_db = [(k[0], k[1], k[2], k[3], '?') for k in list_kelas_db_simple]
    conn.close()

    if not list_kelas_db:
        st.warning("Belum ada data kelas.")
        return

    kelas_options = {f"{nama} ({angkatan}) - [{jum_siswa} siswa]": id_kelas for id_kelas, angkatan, nama, tahun, jum_siswa in list_kelas_db}

    st.markdown("#### Langkah 1: Pilih Kelas")
    col1, col2 = st.columns(2)
    with col1:
        kelas_asal_label = st.selectbox("Dari Kelas:", options=list(kelas_options.keys()), key="pindah_kelas_asal", index=None, placeholder="Pilih kelas asal...")
    with col2:
        if kelas_asal_label:
            pilihan_tujuan = [label for label in kelas_options.keys() if label != kelas_asal_label]
            kelas_tujuan_label = st.selectbox("Ke Kelas:", options=pilihan_tujuan, key="pindah_kelas_tujuan", index=None, placeholder="Pilih kelas tujuan...")
        else:
            st.selectbox("Ke Kelas:", options=[], disabled=True)

    id_kelas_asal_sekarang = kelas_options.get(kelas_asal_label)
    if id_kelas_asal_sekarang != st.session_state.pindah_kelas_id_asal_sebelumnya:
        if 'pindah_siswa_editor' in st.session_state:
            del st.session_state['pindah_siswa_editor']
        st.session_state.pindah_kelas_id_asal_sebelumnya = id_kelas_asal_sekarang

    st.markdown("---")

    if kelas_asal_label and 'kelas_tujuan_label' in locals() and kelas_tujuan_label:
        id_kelas_asal = kelas_options[kelas_asal_label]
        id_kelas_tujuan = kelas_options[kelas_tujuan_label]

        st.markdown("#### Langkah 2: Pilih Siswa")
        conn = db.create_connection()
        siswa_di_kelas = db.get_siswa_by_kelas(conn, id_kelas_asal)
        conn.close()

        if not siswa_di_kelas:
            st.warning(f"Tidak ada siswa yang ditemukan di kelas **{kelas_asal_label}**.")
            return

        with st.container(border=True):
            st.markdown("##### Daftar Siswa di Kelas Asal")
            search_term = st.text_input("Cari siswa di dalam tabel:", placeholder="Ketik Nama atau NIS...")
            siswa_di_kelas_filtered = [s for s in siswa_di_kelas if not search_term or search_term.lower() in s[1].lower() or search_term.lower() in s[0].lower()]

            if not siswa_di_kelas_filtered:
                st.info("Tidak ada siswa yang cocok dengan kriteria pencarian Anda.")
            else:
                df_siswa = pd.DataFrame(siswa_di_kelas_filtered, columns=['NIS', 'Nama Siswa'])
                df_siswa.insert(0, "Pilih", False)
                edited_df = st.data_editor(df_siswa, key="pindah_siswa_editor", height=300, hide_index=True, use_container_width=True, column_config={"Pilih": st.column_config.CheckboxColumn(required=True)}, disabled=['NIS', 'Nama Siswa'])
        
        siswa_terpilih_df = edited_df[edited_df['Pilih']]
        st.markdown("---")

        if not siswa_terpilih_df.empty:
            st.markdown("#### Langkah 3: Pratinjau dan Konfirmasi")
            df_preview = siswa_terpilih_df[['NIS', 'Nama Siswa']].copy()
            df_preview['Kelas Asal'] = kelas_asal_label.split(' - ')[0]
            df_preview['Kelas Tujuan'] = kelas_tujuan_label.split(' - ')[0]
            
            st.success(f"Anda akan memindahkan **{len(siswa_terpilih_df)} siswa** berikut:")
            # Menggunakan tabel HTML kustom yang sudah diberi warna untuk pratinjau
            preview_html = df_preview.to_html(escape=False, index=False, classes="styled-table")
            st.markdown(preview_html, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button(f"✅ Konfirmasi dan Pindahkan {len(siswa_terpilih_df)} Siswa", type="primary"):
                nis_siswa_terpilih = siswa_terpilih_df['NIS'].tolist()
                with st.spinner("Memproses perpindahan..."):
                    conn = db.create_connection()
                    for nis in nis_siswa_terpilih:
                        db.update_kelas_siswa(conn, nis, id_kelas_tujuan)
                    conn.close()
                
                st.session_state.transfer_sukses_info = {
                    'jumlah': len(nis_siswa_terpilih),
                    'id_kelas_tujuan': id_kelas_tujuan,
                    'nama_kelas_tujuan': kelas_tujuan_label.split(' - ')[0]
                }
                
                if 'pindah_siswa_editor' in st.session_state:
                    del st.session_state.pindah_siswa_editor
                
                st.rerun()
        else:
            st.info("Centang kotak di samping nama siswa pada tabel di atas untuk memulai proses pemindahan.")

def show_tinggal_kelas():
    st.subheader("❌ Proses Tinggal Kelas")

    # --- CSS untuk Tabel Kustom ---
    st.markdown("""
    <style>
        .styled-table { width: 100%; border-collapse: collapse; margin-top: 1em; }
        .styled-table thead th { background-color: #dc3545; color: white; text-align: left; padding: 12px 15px; }
        .styled-table tbody tr { border-bottom: 1px solid #dddddd; }
        .styled-table tbody tr:nth-of-type(even) { background-color: #f3f3f3; }
        .styled-table tbody tr:hover { background-color: #f8d7da; }
        .styled-table td { padding: 12px 15px; }
    </style>
    """, unsafe_allow_html=True)

    # Cek apakah ada proses yang baru saja berhasil
    if 'tinggal_kelas_sukses_info' in st.session_state:
        info = st.session_state.tinggal_kelas_sukses_info
        st.success(f"**Berhasil!** Status untuk **{info['jumlah']} siswa** telah diubah menjadi **'Tinggal Kelas'**.")
        st.write("Berikut adalah daftar siswa yang terpengaruh:")
        
        df_hasil = pd.DataFrame(info['list_siswa'], columns=['NIS', 'Nama Siswa'])
        # Menggunakan tabel HTML kustom yang sudah diberi warna
        table_html_hasil = df_hasil.to_html(escape=False, index=False, classes="styled-table")
        st.markdown(table_html_hasil, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅️ Kembali"):
            del st.session_state.tinggal_kelas_sukses_info
            st.rerun()
        return

    # Tampilan Halaman Utama
    st.info("Gunakan fitur ini untuk mengubah status siswa aktif menjadi 'Tinggal Kelas'.")
    if 'tinggal_kelas_id_sebelumnya' not in st.session_state:
        st.session_state.tinggal_kelas_id_sebelumnya = None

    conn = db.create_connection()
    try:
        list_kelas_db = db.get_semua_kelas_dengan_jumlah_siswa(conn)
    except AttributeError:
        list_kelas_db_simple = db.get_semua_kelas(conn)
        list_kelas_db = [(k[0], k[1], k[2], k[3], '?') for k in list_kelas_db_simple]
    conn.close()

    if not list_kelas_db:
        st.warning("Belum ada data kelas.")
        return

    kelas_options = {f"{nama} ({angkatan}) - [{jum_siswa} siswa]": id_kelas for id_kelas, angkatan, nama, tahun, jum_siswa in list_kelas_db}

    st.markdown("#### Langkah 1: Pilih Kelas")
    kelas_label = st.selectbox("Pilih kelas:", options=list(kelas_options.keys()), key="tinggal_kelas_asal", index=None, placeholder="Pilih kelas...")

    id_kelas_sekarang = kelas_options.get(kelas_label)
    if id_kelas_sekarang != st.session_state.tinggal_kelas_id_sebelumnya:
        if 'tinggal_kelas_editor' in st.session_state:
            del st.session_state['tinggal_kelas_editor']
        st.session_state.tinggal_kelas_id_sebelumnya = id_kelas_sekarang
        
    st.markdown("---")

    if kelas_label:
        id_kelas_asal = kelas_options[kelas_label]
        
        st.markdown("#### Langkah 2: Pilih Siswa")
        conn = db.create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nis, nama_lengkap FROM siswa WHERE id_kelas = ? AND status = 'Aktif'", (id_kelas_asal,))
        siswa_di_kelas = cursor.fetchall()
        conn.close()
        
        if not siswa_di_kelas:
            st.warning(f"Tidak ada siswa **aktif** yang ditemukan di kelas ini.")
            return

        with st.container(border=True):
            search_term = st.text_input("Cari siswa di dalam tabel:", placeholder="Ketik Nama atau NIS...")
            siswa_filtered = [s for s in siswa_di_kelas if not search_term or search_term.lower() in s[1].lower() or search_term.lower() in s[0].lower()]

            if not siswa_filtered:
                st.info("Tidak ada siswa yang cocok dengan kriteria pencarian Anda.")
            else:
                df_siswa = pd.DataFrame(siswa_filtered, columns=['NIS', 'Nama Siswa'])
                df_siswa.insert(0, "Pilih", False)
                edited_df = st.data_editor(df_siswa, key="tinggal_kelas_editor", height=300, hide_index=True, use_container_width=True, column_config={"Pilih": st.column_config.CheckboxColumn(required=True)}, disabled=['NIS', 'Nama Siswa'])
        
        siswa_terpilih_df = edited_df[edited_df['Pilih']]
        st.markdown("---")

        if not siswa_terpilih_df.empty:
            st.markdown("#### Langkah 3: Pratinjau dan Konfirmasi")
            
            df_preview = siswa_terpilih_df[['NIS', 'Nama Siswa']].copy()
            df_preview['Status Saat Ini'] = "Aktif"
            df_preview['Status Baru'] = "Tinggal Kelas"
            
            st.warning(f"Anda akan mengubah status untuk **{len(siswa_terpilih_df)} siswa** berikut:")
            # Menggunakan tabel HTML kustom yang sudah diberi warna untuk pratinjau
            table_html_preview = df_preview.to_html(escape=False, index=False, classes="styled-table")
            st.markdown(table_html_preview, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button(f"✔️ Konfirmasi dan Ubah Status {len(siswa_terpilih_df)} Siswa", type="primary"):
                list_siswa_terpilih = list(zip(siswa_terpilih_df['NIS'], siswa_terpilih_df['Nama Siswa']))
                
                with st.spinner("Memperbarui status siswa..."):
                    conn = db.create_connection()
                    for nis, nama in list_siswa_terpilih:
                        db.update_status_siswa(conn, nis, "Tinggal Kelas")
                    conn.close()

                st.session_state.tinggal_kelas_sukses_info = {
                    'jumlah': len(list_siswa_terpilih),
                    'list_siswa': list_siswa_terpilih
                }
                
                if 'tinggal_kelas_editor' in st.session_state:
                    del st.session_state.tinggal_kelas_editor
                
                st.rerun()
        else:
            st.info("Centang kotak di samping nama siswa pada tabel di atas untuk melanjutkan.")

def show_kelulusan():
    st.subheader("🎓 Posting Kelulusan")

    # --- CSS untuk Tabel Kustom ---
    st.markdown("""
    <style>
        .styled-table { width: 100%; border-collapse: collapse; margin-top: 1em; }
        .styled-table thead th { background-color: #28a745; color: white; text-align: left; padding: 12px 15px; }
        .styled-table tbody tr { border-bottom: 1px solid #dddddd; }
        .styled-table tbody tr:nth-of-type(even) { background-color: #f3f3f3; }
        .styled-table tbody tr:hover { background-color: #d4edda; }
        .styled-table td { padding: 12px 15px; }
    </style>
    """, unsafe_allow_html=True)

    # --- Tampilan Halaman Hasil Setelah Proses Berhasil ---
    if 'lulus_sukses_info' in st.session_state:
        info = st.session_state.lulus_sukses_info
        st.success(f"**Selamat!** Sebanyak **{info['jumlah']} siswa** telah berhasil ditandai 'Lulus'.")
        st.markdown("#### Rangkuman Hasil Kelulusan")
        
        # Membuat dan menampilkan tabel hasil yang lebih informatif
        df_hasil = pd.DataFrame(info['list_lulus'])
        df_hasil = df_hasil.rename(columns={'Kelas Asal': 'Lulus dari Kelas', 'Status Baru': 'Status Kelulusan'})
        table_html_hasil = df_hasil[['NIS', 'Nama Siswa', 'Lulus dari Kelas', 'Status Kelulusan']].to_html(escape=False, index=False, classes="styled-table")
        st.markdown(table_html_hasil, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅️ Kembali"):
            del st.session_state.lulus_sukses_info
            st.rerun()
        return

    # Tampilan Halaman Utama
    st.info("Gunakan fitur ini untuk mengubah status siswa aktif menjadi 'Lulus'.")
    if 'lulus_kelas_id_sebelumnya' not in st.session_state:
        st.session_state.lulus_kelas_id_sebelumnya = None

    conn = db.create_connection()
    try:
        list_kelas_db = db.get_semua_kelas_dengan_jumlah_siswa(conn)
    except AttributeError:
        list_kelas_db_simple = db.get_semua_kelas(conn)
        list_kelas_db = [(k[0], k[1], k[2], k[3], '?') for k in list_kelas_db_simple]
    conn.close()

    if not list_kelas_db:
        st.warning("Belum ada data kelas.")
        return

    kelas_options = {f"{nama} ({angkatan}) - [{jum_siswa} siswa]": id_kelas for id_kelas, angkatan, nama, tahun, jum_siswa in list_kelas_db}

    st.markdown("#### Langkah 1: Pilih Kelas")
    kelas_label = st.selectbox("Pilih kelas yang akan diluluskan:", options=list(kelas_options.keys()), key="lulus_kelas_asal", index=None, placeholder="Pilih kelas...")

    id_kelas_sekarang = kelas_options.get(kelas_label)
    if id_kelas_sekarang != st.session_state.lulus_kelas_id_sebelumnya:
        if 'lulus_editor' in st.session_state:
            del st.session_state['lulus_editor']
        st.session_state.lulus_kelas_id_sebelumnya = id_kelas_sekarang
        
    st.markdown("---")

    if kelas_label:
        id_kelas_asal = kelas_options[kelas_label]
        
        st.markdown("#### Langkah 2: Pilih Siswa")
        conn = db.create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nis, nama_lengkap FROM siswa WHERE id_kelas = ? AND status = 'Aktif'", (id_kelas_asal,))
        siswa_di_kelas = cursor.fetchall()
        conn.close()
        
        if not siswa_di_kelas:
            st.warning(f"Tidak ada siswa **aktif** yang dapat diluluskan di kelas ini.")
            return

        with st.container(border=True):
            search_term = st.text_input("Cari siswa di dalam tabel:", placeholder="Ketik Nama atau NIS...")
            siswa_filtered = [s for s in siswa_di_kelas if not search_term or search_term.lower() in s[1].lower() or search_term.lower() in s[0].lower()]

            if not siswa_filtered:
                st.info("Tidak ada siswa yang cocok dengan kriteria pencarian Anda.")
            else:
                df_siswa = pd.DataFrame(siswa_filtered, columns=['NIS', 'Nama Siswa'])
                df_siswa.insert(0, "Pilih", False)
                edited_df = st.data_editor(df_siswa, key="lulus_editor", height=300, hide_index=True, use_container_width=True, column_config={"Pilih": st.column_config.CheckboxColumn(required=True)}, disabled=['NIS', 'Nama Siswa'])
        
        siswa_terpilih_df = edited_df[edited_df['Pilih']]
        st.markdown("---")

        if not siswa_terpilih_df.empty:
            st.markdown("#### Langkah 3: Pratinjau dan Konfirmasi")
            
            df_preview = siswa_terpilih_df[['NIS', 'Nama Siswa']].copy()
            df_preview['Kelas Asal'] = kelas_label.split(' - ')[0]
            df_preview['Status Baru'] = "Lulus"
            
            st.info(f"Anda akan meluluskan **{len(siswa_terpilih_df)} siswa** berikut:")
            preview_html = df_preview.to_html(escape=False, index=False, classes="styled-table")
            st.markdown(preview_html, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button(f"🎓 Konfirmasi dan Luluskan {len(siswa_terpilih_df)} Siswa", type="primary"):
                with st.spinner("Memproses kelulusan..."):
                    conn = db.create_connection()
                    for nis in siswa_terpilih_df['NIS']:
                        db.update_status_siswa(conn, nis, "Lulus")
                    conn.close()

                # Menyimpan data dari DataFrame pratinjau untuk ditampilkan di halaman hasil
                st.session_state.lulus_sukses_info = {
                    'jumlah': len(df_preview),
                    'list_lulus': df_preview.to_dict('records')
                }
                
                if 'lulus_editor' in st.session_state:
                    del st.session_state.lulus_editor
                
                st.rerun()
        else:
            st.info("Centang kotak di samping nama siswa pada tabel di atas untuk melanjutkan.")

def show_cetak_bukti_pembayaran():
    st.subheader("📄 Cetak Ulang Bukti Pembayaran")
    st.info("Gunakan filter untuk mencari transaksi, lalu centang satu atau beberapa data dari tabel untuk dicetak.")

    config = load_config()

    # --- UI FILTER ---
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            list_angkatan = ["Semua Angkatan"] + get_semua_angkatan_cached()
            selected_angkatan_filter = st.selectbox("Filter Angkatan", options=list_angkatan)
        with c2:
            list_kelas = get_semua_kelas_cached()
            kelas_dict = {f"{angkatan} - {nama}": id_kls for id_kls, angkatan, nama, thn in list_kelas}
            selected_kelas_nama = st.selectbox("Filter per Kelas", options=["Semua Kelas"] + list(kelas_dict.keys()))
        with c3:
            search_term = st.text_input("Cari Nama Siswa atau NIS")

    id_kelas_filter = None if selected_kelas_nama == "Semua Kelas" else kelas_dict.get(selected_kelas_nama)
    angkatan_filter = None if selected_angkatan_filter == "Semua Angkatan" else selected_angkatan_filter
    
    st.markdown("---")

    # --- Layout Utama 2 Kolom ---
    table_col, preview_col = st.columns([0.6, 0.4], gap="large")

    with table_col:
        st.markdown("#### Daftar Transaksi")
        conn = db.create_connection()
        filtered_trans = db.get_filtered_transaksi(conn, search_term=search_term, kelas_id=id_kelas_filter, angkatan=angkatan_filter)
        conn.close()

        if not filtered_trans:
            st.warning("Tidak ada data transaksi yang cocok dengan filter Anda.")
            return
        
        df_trans = pd.DataFrame(filtered_trans, columns=['ID', 'Tanggal', 'NIS', 'Nama Siswa', 'Total Bayar', 'Kelas', 'Angkatan'])
        df_trans['Tanggal'] = pd.to_datetime(df_trans['Tanggal']).dt.strftime('%d-%m-%Y %H:%M')
        df_trans.insert(0, "Pilih", False)
        
        edited_df = st.data_editor(
            df_trans[['Pilih', 'ID', 'Tanggal', 'Nama Siswa', 'Total Bayar']],
            key="cetak_editor", hide_index=True, use_container_width=True, height=500,
            column_config={"Pilih": st.column_config.CheckboxColumn(required=True)},
            disabled=['ID', 'Tanggal', 'Nama Siswa', 'Total Bayar']
        )
        
        transaksi_terpilih_df = edited_df[edited_df['Pilih']]

    with preview_col:
        st.markdown("#### Pratinjau & Aksi")

        # Logika untuk membuat HTML satu nota
        def generate_receipt_html_content(trans_id):
            conn = db.create_connection()
            trans_info_tuple = db.get_transaksi_by_id(conn, trans_id)
            item_pembayaran_tuple = db.get_detail_by_transaksi(conn, trans_id)
            conn.close()

            if not trans_info_tuple: return "<div>Data transaksi tidak ditemukan.</div>"

            trans_info = {'no_trans': trans_info_tuple[0], 'tanggal_trans': datetime.strptime(trans_info_tuple[1], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y'), 'nis': trans_info_tuple[2], 'nama_siswa': trans_info_tuple[3], 'kelas': trans_info_tuple[4] or "-", 'grand_total': trans_info_tuple[5], 'nama_petugas': trans_info_tuple[6]}
            item_rows_html = "".join([f'<tr><td class="col-no">{i+1}.</td><td class="col-ket">{item[0] + (f" - {item[1]}" if item[1] else "")}</td><td class="col-jml">{item[2]:,.0f}</td></tr>' for i, item in enumerate(item_pembayaran_tuple)])
            grand_total_formatted = f"{trans_info['grand_total']:,.0f}"
            terbilang_text = terbilang(trans_info['grand_total'])
            logo_base64 = ""
            try:
                with open(config.get("logo_path", "logo.png"), "rb") as f: logo_base64 = base64.b64encode(f.read()).decode()
            except FileNotFoundError: pass

            return f"""
            <div class='receipt-container' id="receipt-{trans_id}">
                <div class="header"> <img src="data:image/png;base64,{logo_base64}" alt="logo"> <div class="school-info"> <h4>{config.get('nama_lembaga')}</h4> <p>{config.get('alamat')}<br>Telp: {config.get('telp')} | Website: {config.get('website')}</p> </div> </div>
                <div class="title">BUKTI PEMBAYARAN SISWA</div>
                <div class="info-section"> <table> <tr><td>NO TRANS</td><td>: {trans_info['no_trans']}</td><td>NAMA SISWA</td><td>: {trans_info['nama_siswa']}</td></tr> <tr><td>TANGGAL</td><td>: {trans_info['tanggal_trans']}</td><td>KELAS</td><td>: {trans_info['kelas']}</td></tr> </table> </div>
                <table class="payment-table"> <thead><tr><th class="col-no">No.</th><th class="col-ket">Keterangan</th><th class="col-jml">Jumlah (Rp)</th></tr></thead> <tbody>{item_rows_html}</tbody> </table>
                <div class="summary-section"> <div class="terbilang-section"><b>Terbilang :</b><br>{terbilang_text}</div> <div class="total-section"><b>Grand Total :<br><span class="grand-total">{grand_total_formatted}</span></b></div> </div>
                <div class="footer-section"> <div class="disclaimer">* Simpan sebagai bukti pembayaran yang SAH.</div> <div class="signature">Karanganyar, {datetime.now().strftime('%d %B %Y')}<br>Yang Menerima,<div class="name">{trans_info['nama_petugas']}</div></div> </div>
            </div>
            """

        # Menampilkan pratinjau atau ringkasan
        if len(transaksi_terpilih_df) == 1:
            selected_id = transaksi_terpilih_df['ID'].iloc[0]
            st.write(f"**Pratinjau Nota ID: {selected_id}**")
            html_content_single = generate_receipt_html_content(selected_id)
            st.components.v1.html(f"<style>{receipt_css()}</style>{html_content_single}", height=550, scrolling=True)
        elif len(transaksi_terpilih_df) > 1:
            st.write(f"**{len(transaksi_terpilih_df)} transaksi dipilih:**")
            st.dataframe(transaksi_terpilih_df[['ID', 'Nama Siswa', 'Total Bayar']], hide_index=True, use_container_width=True)
        else:
            st.info("Centang transaksi di tabel kiri untuk melihat pratinjau atau mencetak.")

        # Tombol Aksi Cetak
        if not transaksi_terpilih_df.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(f"🖨️ Cetak {len(transaksi_terpilih_df)} Bukti Terpilih", type="primary", use_container_width=True):
                all_receipts_html = ""
                with st.spinner("Mempersiapkan semua nota..."):
                    for trans_id in transaksi_terpilih_df['ID']:
                        all_receipts_html += generate_receipt_html_content(trans_id)

                # Menampilkan dialog cetak
                st.session_state.show_print_dialog = True
                st.session_state.printable_html = all_receipts_html
    
    if st.session_state.get("show_print_dialog", False):
        st.dialog("Jendela Cetak")
        st.components.v1.html(f"""
            <html><head><title>Cetak Bukti Pembayaran</title><style>{receipt_css()}</style></head>
            <body style="background-color: #f0f2f6;">
                {st.session_state.printable_html}
                <div class="no-print" style="text-align:center; padding: 20px;">
                    <button onclick="window.print()" style="padding: 12px 25px; font-size: 16px; color: white; background-color: #28a745; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">Cetak Sekarang</button>
                </div>
            </body></html>
        """, height=600, scrolling=True)
        if st.button("Tutup Jendela Cetak"):
            st.session_state.show_print_dialog = False
            st.rerun()

def receipt_css():
    """Mengembalikan string CSS untuk nota."""
    return """
        body { font-family: 'Arial', sans-serif; font-size: 10pt; color: #000; }
        .receipt-container { width: 100%; max-width: 800px; padding: 20px; margin: 20px auto; background: #fff; box-sizing: border-box; border: 1px solid #ccc; page-break-after: always; }
        .header { display: flex; align-items: flex-start; border-bottom: 2px solid #000; padding-bottom: 8px; }
        .header img { width: 60px; height: auto; margin-right: 15px; }
        .header .school-info h4 { font-size: 14pt; font-weight: bold; margin:0; }
        .header .school-info p { font-size: 9pt; margin: 0; line-height: 1.4; }
        .title { text-align: center; font-weight: bold; font-size: 12pt; margin: 8px 0; border-bottom: 2px solid #000; padding-bottom: 8px;}
        .info-section table { width: 100%; margin-top: 10px; font-size: 10pt; }
        .info-section td { padding: 2px 4px; }
        .payment-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        .payment-table th, .payment-table td { padding: 6px; font-size: 10pt; border: 1px solid #555; }
        .payment-table th { background-color: #e9ecef; text-align: center; }
        .col-no { width: 5%; text-align:center; } .col-ket { width: 70%; } .col-jml { width: 25%; text-align: right; }
        .summary-section { border-top: 1px solid #000; padding-top: 10px; margin-top: 8px; display: flex; justify-content: space-between; font-size: 10pt;}
        .terbilang-section { font-style: italic; max-width: 60%; }
        .total-section { text-align: right; }
        .total-section .grand-total { font-weight: bold; font-size: 13pt; }
        .footer-section { border-top: 1px solid #000; padding-top: 10px; margin-top: 15px; display: flex; justify-content: space-between; align-items: flex-end; font-size: 9pt; }
        .disclaimer { font-size: 8pt; max-width: 50%; }
        .signature { text-align: center; }
        .signature .name { font-weight: bold; text-decoration: underline; margin-top: 50px; }
        @media print { .no-print { display: none !important; } .receipt-container { border: none; margin: 0; box-shadow: none; } }
    """
            
# --- FUNGSI RENDER UTAMA MODUL (DENGAN GAYA BARU) ---
def render():
    """
    Merender seluruh antarmuka untuk Modul Data Siswa dengan memuat ikon SVG
    langsung dari file dan menggunakan CSS untuk styling.
    """
    icon_kelas = load_svg("assets/modulsiswa/datakelas.svg")
    icon_siswa = load_svg("assets/modulsiswa/daftarsiswa.svg")
    icon_import = load_svg("assets/modulsiswa/importexcel.svg")
    icon_naik = load_svg("assets/modulsiswa/naikkelas.svg")
    icon_pindah = load_svg("assets/modulsiswa/pindah kelas.svg")
    icon_tinggal = load_svg("assets/modulsiswa/tinggalkelas.svg")
    icon_lulus = load_svg("assets/modulsiswa/kelulusan.svg")
    icon_kartu = load_svg("assets/modulsiswa/cetakkartu.svg")
    
    # --- CSS YANG DIPERBAIKI ---
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
                display: flex; 
                flex-direction: column; 
                padding: 1.5rem;
                max-width: 280px;
                margin: auto;
            }

            /* Efek hover pada kartu menu */
            div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] > div[data-testid="stBorderedSticker"]:hover {
                transform: translateY(-5px); 
                box-shadow: 0 8px 16px rgba(0,0,0,0.12); 
                border-color: #007BFF;
            }
            
            /* --- PERUBAHAN UTAMA DI SINI --- */
            /* Konten di dalam kartu */
            .menu-item-content { 
                text-align: center; 
                margin-bottom: 1.5rem; /* Beri jarak bawah agar tidak terlalu mepet dengan tombol */
                /* flex-grow: 1; <-- Properti ini dihapus untuk menghilangkan ruang kosong */
            }

            /* Kontainer Ikon */
            .menu-icon-container svg { width: 60px; height: 60px; } /* Ukuran ikon */
            
            /* Judul menu */
            .menu-item-content h5 { font-size: 1.1rem; font-weight: 600; color: #343A40; margin-top: 0.5rem; }
            
            /* Tombol utama di dalam kartu */
            .stButton > button {
                background-color: #007BFF !important; color: white !important; font-weight: bold;
                border-radius: 8px !important; border: none !important; width: 100% !important;
                padding: 0.75rem 0 !important; font-size: 1rem !important;
                margin-top: auto; /* Mendorong tombol ke bagian bawah jika ada ruang lebih */
            }
            .stButton > button:hover { background-color: #0056b3 !important; }
        </style>
        """, unsafe_allow_html=True)
    
    if 'data_siswa_view' not in st.session_state:
        st.session_state.data_siswa_view = 'menu'

    # --- HEADER ---
    col_title, col_button = st.columns([3, 1])
    with col_title:
        st.title("📊 Modul Data Siswa")
    with col_button:
        st.markdown('<div style="height: 2.5rem;"></div>', unsafe_allow_html=True)
        if st.session_state.data_siswa_view != 'menu':
            if st.button("⬅️ Kembali ke Menu", key="datasiswa_back_to_menu", use_container_width=True):
                st.session_state.data_siswa_view = 'menu'
                st.rerun()
        else:
            if st.button("⬅️ Menu Utama", key="datasiswa_back_to_main", use_container_width=True):
                st.session_state.page = 'home'
                if 'page' in st.query_params:
                    st.query_params.clear()
                st.rerun()
            
    st.markdown("---")
        
    if st.session_state.data_siswa_view == 'menu':
        menu_options = {
            'master_kelas': {"label": "Data Kelas", "icon": icon_kelas},
            'daftar_siswa': {"label": "Daftar Siswa", "icon": icon_siswa},
            'import_excel': {"label": "Import Excel", "icon": icon_import},
            'naik_kelas': {"label": "Naik Kelas", "icon": icon_naik},
            'pindah_kelas': {"label": "Pindah Kelas", "icon": icon_pindah},
            'tinggal_kelas': {"label": "Tinggal Kelas", "icon": icon_tinggal},
            'kelulusan': {"label": "Kelulusan", "icon": icon_lulus},
            'cetak_bukti': {"label": "Cetak Bukti Bayar", "icon": icon_kartu}
        }
        
        items = list(menu_options.items())
        num_cols = 4
        for i in range(0, len(items), num_cols):
            cols = st.columns(num_cols)
            row_items = items[i:i+num_cols]
            for j, (view, content) in enumerate(row_items):
                with cols[j]:
                    # --- PERUBAHAN UTAMA: Tambahkan kembali st.container ---
                    with st.container(border=True, height=250):
                        st.markdown(f"""
                            <div class="menu-item-content">
                                <div class="menu-icon-container">{content['icon']}</div>
                                <h5>{content['label']}</h5>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("Pilih Menu", key=f"btn_{view}", use_container_width=True):
                            st.session_state.data_siswa_view = view
                            st.rerun()

    else:
        view_function_map = {
            'master_kelas': show_master_kelas, 'daftar_siswa': show_daftar_siswa,
            'import_excel': show_import_excel, 'naik_kelas': show_naik_kelas,
            'pindah_kelas': show_pindah_kelas, 'tinggal_kelas': show_tinggal_kelas,
            'kelulusan': show_kelulusan, 'cetak_bukti': show_cetak_bukti_pembayaran
        }
        render_function = view_function_map.get(st.session_state.data_siswa_view)
        if render_function:
            render_function()