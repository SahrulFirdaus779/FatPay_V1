import streamlit as st
import pandas as pd
from utils import db_functions as db
import io
import re
import barcode
from barcode.writer import ImageWriter
import base64

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

# --- FUNGSI SUB-HALAMAN (LENGKAP) ---

def show_master_kelas():
    st.subheader("Master Data Kelas")
    with st.form("form_tambah_kelas", clear_on_submit=True):
        nama_kelas = st.text_input("Nama Kelas (Contoh: X-A, XI-IPA-1)")
        tahun_ajaran = st.text_input("Tahun Ajaran (Contoh: 2024/2025)")
        if st.form_submit_button("➕ Tambah Kelas"):
            if nama_kelas and tahun_ajaran:
                with st.spinner("Menyimpan..."):
                    conn = db.create_connection()
                    db.tambah_kelas(conn, nama_kelas, tahun_ajaran)
                    conn.close()
                st.toast(f"✅ Kelas '{nama_kelas}' berhasil ditambahkan.")
                st.rerun()
            else:
                st.warning("Nama Kelas dan Tahun Ajaran tidak boleh kosong.")
    st.markdown("---")
    with st.spinner("Memuat data kelas..."):
        conn = db.create_connection()
        list_kelas = db.get_semua_kelas(conn)
        conn.close()
    if list_kelas:
        df_kelas = pd.DataFrame(list_kelas, columns=['ID', 'Nama Kelas', 'Tahun Ajaran'])
        st.dataframe(df_kelas, use_container_width=True, hide_index=True)
        with st.expander("✏️ Edit atau Hapus Data Kelas"):
            kelas_dict = {f"{nama} ({tahun})": id_kelas for id_kelas, nama, tahun in list_kelas}
            selected_kelas_nama = st.selectbox("Pilih kelas untuk diubah/dihapus", options=kelas_dict.keys())
            id_kelas_terpilih = kelas_dict.get(selected_kelas_nama)
            if id_kelas_terpilih:
                selected_details = next(item for item in list_kelas if item[0] == id_kelas_terpilih)
                with st.form(f"form_edit_kelas_{id_kelas_terpilih}"):
                    edit_nama = st.text_input("Nama Kelas Baru", value=selected_details[1])
                    edit_tahun = st.text_input("Tahun Ajaran Baru", value=selected_details[2])
                    if st.form_submit_button("Simpan Perubahan"):
                        with st.spinner("Memperbarui data..."):
                            conn = db.create_connection()
                            db.update_kelas(conn, id_kelas_terpilih, edit_nama, edit_tahun)
                            conn.close()
                        st.toast("✅ Data kelas berhasil diperbarui!")
                        st.rerun()
                if st.button(f"❌ Hapus Kelas: {selected_kelas_nama}", type="primary"):
                    with st.spinner("Memeriksa data..."):
                        conn = db.create_connection()
                        if db.get_siswa_by_kelas(conn, id_kelas_terpilih):
                            st.error("Tidak bisa menghapus kelas karena masih ada siswa di dalamnya.")
                        else:
                            db.hapus_kelas(conn, id_kelas_terpilih)
                            st.toast(f"🗑️ Kelas {selected_kelas_nama} telah dihapus.")
                            st.rerun()
                        conn.close()

def show_daftar_siswa():
    st.subheader("Data Induk Siswa")
    
    conn = db.create_connection()
    list_kelas = db.get_semua_kelas(conn)
    conn.close()
    kelas_dict = {f"{nama} ({tahun})": id_kelas for id_kelas, nama, tahun in list_kelas}
    
    with st.container(border=True):
        col1, col2 = st.columns([2, 3])
        with col1:
            pilihan_kelas_filter = ["Semua Kelas"] + list(kelas_dict.keys())
            selected_kelas_filter_nama = st.selectbox("Filter per Kelas", options=pilihan_kelas_filter)
        with col2:
            search_term = st.text_input("Cari Nama atau NIS Siswa", placeholder="Ketik di sini untuk mencari...")

    id_kelas_filter = kelas_dict.get(selected_kelas_filter_nama)

    with st.spinner("Memuat data siswa..."):
        conn = db.create_connection()
        list_siswa = db.get_filtered_siswa_detailed(conn, kelas_id=id_kelas_filter, search_term=search_term)
        conn.close()
    
    st.markdown("---")
    st.write(f"**Menampilkan data siswa:**")
    
    if list_siswa:
        df_siswa = pd.DataFrame(list_siswa, columns=['NIS', 'NIK Siswa', 'NISN', 'Nama Lengkap', 'L/P', 'No. WA Ortu', 'Kelas', 'Status']).head(10)
        df_siswa['Status'] = df_siswa['Status'].apply(format_status_badge)
        st.markdown(df_siswa.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.info("Tidak ada data siswa yang cocok dengan filter Anda.")

    # --- CRUD: CREATE (Tambah Siswa) ---
    with st.expander("➕ Tambah Siswa Baru"):
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
            selected_kelas_nama = c4.selectbox("Pilih Kelas*", options=kelas_dict.keys(), key="kelas_tambah")
            no_wa_ortu = st.text_input("No. WA Orang Tua")
            
            submitted = st.form_submit_button("Tambah Siswa")
            if submitted:
                if nis and nama_lengkap and selected_kelas_nama:
                    id_kelas_terpilih = kelas_dict[selected_kelas_nama]
                    with st.spinner("Menyimpan data siswa..."):
                        conn = db.create_connection()
                        try:
                            db.tambah_siswa(conn, nis, nik_siswa, nisn, nama_lengkap, jenis_kelamin, no_wa_ortu, id_kelas_terpilih)
                            st.toast(f"✅ Siswa '{nama_lengkap}' berhasil ditambahkan.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal menambahkan siswa. Pastikan NIS unik.")
                        finally:
                            conn.close()
                else:
                    st.warning("Input dengan tanda (*) tidak boleh kosong.")
    
    # --- CRUD: UPDATE & DELETE (Edit dan Hapus Siswa) ---
    if list_siswa:
        with st.expander("📝 Edit atau Hapus Data Siswa"):
            siswa_dict = {f"{nama} ({nis})": nis for nis, _, _, nama, _, _, _, _ in list_siswa}
            selected_siswa_nama = st.selectbox("Pilih siswa untuk diubah/dihapus", options=siswa_dict.keys())
            nis_terpilih = siswa_dict.get(selected_siswa_nama)
            
            if nis_terpilih:
                # Mengambil detail siswa yang terpilih
                selected_details = next((item for item in list_siswa if item[0] == nis_terpilih), None)
                
                if selected_details:
                    with st.form(f"form_edit_siswa_{nis_terpilih}"):
                        st.write(f"**Edit Siswa: {selected_siswa_nama}**")
                        
                        # Mengambil detail dari tuple
                        _, nik_val, nisn_val, nama_val, jk_val, no_wa_val, kelas_val, _ = selected_details
                        
                        edit_nik = st.text_input("NIK Siswa Baru", value=nik_val)
                        edit_nisn = st.text_input("NISN Baru", value=nisn_val)
                        edit_nama = st.text_input("Nama Lengkap Baru", value=nama_val)
                        
                        jk_options = ["L", "P"]
                        jk_index = jk_options.index(jk_val) if jk_val in jk_options else 0
                        edit_jk = st.selectbox("Jenis Kelamin Baru", options=jk_options, index=jk_index)
                        
                        edit_no_wa = st.text_input("No. WA Orang Tua Baru", value=no_wa_val)
                        
                        kelas_options = list(kelas_dict.keys())
                        current_kelas_nama = next((nama for nama in kelas_options if nama.startswith(kelas_val)), None)
                        kelas_index = kelas_options.index(current_kelas_nama) if current_kelas_nama in kelas_options else 0
                        edit_kelas_nama = st.selectbox("Kelas Baru", options=kelas_options, index=kelas_index)

                        if st.form_submit_button("Simpan Perubahan Siswa"):
                            id_kelas_baru = kelas_dict[edit_kelas_nama]
                            with st.spinner("Memperbarui data..."):
                                conn = db.create_connection()
                                db.update_siswa(conn, nis_terpilih, edit_nik, edit_nisn, edit_nama, edit_jk, edit_no_wa, id_kelas_baru)
                                conn.close()
                            st.toast("✅ Data siswa berhasil diperbarui!")
                            st.rerun()
                            
                    if st.button(f"❌ Hapus Siswa: {selected_siswa_nama}", type="primary"):
                        with st.spinner("Menghapus data siswa..."):
                            conn = db.create_connection()
                            db.hapus_siswa(conn, nis_terpilih)
                            conn.close()
                        st.toast(f"🗑️ Siswa {selected_siswa_nama} telah dihapus.")
                        st.rerun()
def show_import_excel():
    st.subheader("📥 Import Data Siswa dari File Excel")
    st.markdown("#### 1. Unduh Template")
    template_df = pd.DataFrame({'nis': ['1001'],'nik_siswa': ['3524...'],'nisn': ['001...'],'nama_lengkap': ['Budi Santoso'],'jenis_kelamin': ['L'],'no_wa_ortu': ['0812...']})
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        template_df.to_excel(writer, index=False, sheet_name='Sheet1')
    st.download_button(label="📥 Unduh Template Excel",data=output.getvalue(),file_name="template_siswa.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    st.markdown("---")
    
    st.markdown("#### 2. Unggah File Excel")
    conn = db.create_connection()
    list_kelas = db.get_semua_kelas(conn)
    conn.close()
    
    if not list_kelas:
        st.warning("Belum ada data kelas. Silakan tambahkan data kelas terlebih dahulu.")
        return
        
    kelas_dict = {f"{nama} ({tahun})": id_kelas for id_kelas, nama, tahun in list_kelas}
    selected_kelas_nama = st.selectbox("Pilih Kelas untuk siswa yang akan di-import", options=kelas_dict.keys())
    
    uploaded_file = st.file_uploader("Pilih file Excel", type=['xlsx'])
    
    if uploaded_file is not None:
        try:
            df_upload = pd.read_excel(uploaded_file, dtype=str).fillna('')

            # Pemetaan Kolom
            column_mapping = {
                'NO INDUK': 'nis', 'Nama Siswa': 'nama_lengkap',
                'NIK Siswa': 'nik_siswa', 'NISN': 'nisn', 'L/P': 'jenis_kelamin','No Whatsapp': 'no_wa_ortu'
            }
            df_upload.rename(columns=column_mapping, inplace=True)
            
            # FITUR BARU: Pembersihan data otomatis dari spasi ekstra
            for col in ['nis', 'nik_siswa', 'nisn', 'nama_lengkap', 'no_wa_ortu']:
                if col in df_upload.columns:
                    # Menggunakan .astype(str) untuk menghindari error jika ada data non-string
                    df_upload[col] = df_upload[col].astype(str).str.strip()

            st.write("**Preview Data dari File Anda (setelah disesuaikan):**")
            st.dataframe(df_upload.head())
            
            if st.button("🚀 Proses Import Sekarang"):
                required_columns = {'nis', 'nama_lengkap'}
                if not required_columns.issubset(df_upload.columns):
                    st.error(f"File Excel harus memiliki kolom yang bisa dipetakan ke 'nis' dan 'nama_lengkap'.")
                    return
                
                id_kelas_terpilih = kelas_dict[selected_kelas_nama]
                conn = db.create_connection()
                total_rows = len(df_upload)
                progress_bar = st.progress(0, text="Memulai proses import...")
                sukses_count, gagal_count = 0, 0
                list_gagal = [] # FITUR BARU: Daftar untuk menyimpan detail kegagalan

                for i, row in df_upload.iterrows():
                    nis_value = row.get('nis')
                    nama_value = row.get('nama_lengkap')
                    
                    # FITUR BARU: Validasi data sebelum ke database
                    if not nis_value or not nama_value:
                        gagal_count += 1
                        list_gagal.append(f"Baris {i+2}: Gagal - NIS atau Nama Lengkap tidak boleh kosong.")
                        continue # Lanjut ke baris berikutnya

                    try:
                        db.tambah_siswa(
                            conn=conn, nis=nis_value, nik_siswa=row.get('nik_siswa'), nisn=row.get('nisn'),
                            nama_lengkap=nama_value, jenis_kelamin=row.get('jenis_kelamin'),
                            no_wa_ortu=row.get('no_wa_ortu'), kelas_id=id_kelas_terpilih
                        )
                        sukses_count += 1
                    except Exception as e:
                        gagal_count += 1
                        # FITUR BARU: Pesan eror yang lebih spesifik
                        pesan_eror = str(e)
                        if "UNIQUE constraint failed" in pesan_eror:
                            pesan_eror = "NIS sudah ada di database."
                        list_gagal.append(f"Baris {i+2} (NIS: {nis_value}): Gagal - {pesan_eror}")
                    
                    progress_bar.progress((i + 1) / total_rows, text=f"Memproses baris {i+1}/{total_rows}")
                
                conn.close()
                st.success(f"Proses import selesai! Berhasil: {sukses_count}, Gagal: {gagal_count}.")

                # FITUR BARU: Tampilkan detail kegagalan jika ada
                if list_gagal:
                    with st.expander("Lihat Detail Kegagalan Impor"):
                        for pesan in list_gagal:
                            st.write(pesan)
                            
        except Exception as e:
            st.error(f"Terjadi kesalahan saat membaca atau memproses file: {e}")


def show_naik_kelas():
    st.subheader("⬆️ Posting Kenaikan Kelas")
    st.info("Fitur ini akan memindahkan SEMUA siswa dari kelas asal ke kelas tujuan.")
    conn = db.create_connection()
    list_kelas_db = db.get_semua_kelas(conn)
    conn.close()
    if len(list_kelas_db) < 2:
        st.warning("Anda memerlukan setidaknya 2 kelas untuk proses ini.")
        return
    kelas_dict = {f"{nama} ({tahun})": id_kelas for id_kelas, nama, tahun in list_kelas_db}
    col1, col2 = st.columns(2)
    kelas_asal_nama = col1.selectbox("Pilih kelas asal", options=kelas_dict.keys(), key="kelas_asal")
    pilihan_tujuan = [nama for nama in kelas_dict.keys() if nama != kelas_asal_nama]
    kelas_tujuan_nama = col2.selectbox("Pilih kelas tujuan", options=pilihan_tujuan, key="kelas_tujuan")
    if st.button("🚀 Proses Kenaikan Kelas", type="primary"):
        if not kelas_tujuan_nama:
            st.error("Kelas tujuan tidak valid.")
            return
        with st.spinner(f"Memindahkan siswa dari {kelas_asal_nama} ke {kelas_tujuan_nama}..."):
            id_kelas_asal = kelas_dict[kelas_asal_nama]
            id_kelas_tujuan = kelas_dict[kelas_tujuan_nama]
            conn = db.create_connection()
            siswa_di_kelas_asal = db.get_siswa_by_kelas(conn, id_kelas_asal)
            if not siswa_di_kelas_asal:
                st.warning(f"Tidak ada siswa di kelas {kelas_asal_nama}.")
                conn.close()
                return
            for nis, nama in siswa_di_kelas_asal:
                db.update_kelas_siswa(conn, nis, id_kelas_tujuan)
            conn.close()
            st.success(f"Selesai! {len(siswa_di_kelas_asal)} siswa telah berhasil dipindahkan.")
            st.balloons()

def show_pindah_kelas():
    st.subheader("➡️ Proses Pindah Kelas")
    st.info("Gunakan fitur ini untuk memindahkan siswa tertentu ke kelas lain.")
    conn = db.create_connection()
    list_kelas_db = db.get_semua_kelas(conn)
    conn.close()
    if not list_kelas_db:
        st.warning("Belum ada data kelas.")
        return
    kelas_dict = {f"{nama} ({tahun})": id_kelas for id_kelas, nama, tahun in list_kelas_db}
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Dari Kelas:**")
        kelas_asal_nama = st.selectbox("Pilih kelas asal", options=kelas_dict.keys(), key="pindah_kelas_asal")
        id_kelas_asal = kelas_dict.get(kelas_asal_nama)
        if id_kelas_asal:
            with st.spinner("Memuat siswa..."):
                conn = db.create_connection()
                siswa_di_kelas = db.get_siswa_by_kelas(conn, id_kelas_asal)
                conn.close()
            pilihan_siswa = {f"{nama} ({nis})": nis for nis, nama in siswa_di_kelas}
            siswa_terpilih_nama = st.multiselect("Pilih siswa yang akan dipindahkan:", options=pilihan_siswa.keys())
    with col2:
        st.write("**Ke Kelas:**")
        pilihan_tujuan = [nama for nama in kelas_dict.keys() if nama != kelas_asal_nama]
        kelas_tujuan_nama = st.selectbox("Pilih kelas tujuan", options=pilihan_tujuan, key="pindah_kelas_tujuan")
    if st.button("➡️ Pindahkan Siswa Terpilih"):
        if 'siswa_terpilih_nama' not in locals() or not siswa_terpilih_nama:
            st.error("Tidak ada siswa yang dipilih untuk dipindahkan.")
            return
        if not kelas_tujuan_nama:
            st.error("Kelas tujuan belum dipilih.")
            return
        with st.spinner("Memproses perpindahan..."):
            id_kelas_tujuan = kelas_dict[kelas_tujuan_nama]
            nis_siswa_terpilih = [pilihan_siswa[nama] for nama in siswa_terpilih_nama]
            conn = db.create_connection()
            for nis in nis_siswa_terpilih:
                db.update_kelas_siswa(conn, nis, id_kelas_tujuan)
            conn.close()
        st.toast(f"✅ {len(nis_siswa_terpilih)} siswa berhasil dipindahkan ke {kelas_tujuan_nama}.")
        st.rerun()

def show_tinggal_kelas():
    st.subheader("❌ Proses Tinggal Kelas")
    st.info("Gunakan fitur ini untuk mengubah status siswa menjadi 'Tinggal Kelas'.")
    conn = db.create_connection()
    list_kelas_db = db.get_semua_kelas(conn)
    conn.close()
    if not list_kelas_db:
        st.warning("Belum ada data kelas.")
        return
    kelas_dict = {f"{nama} ({tahun})": id_kelas for id_kelas, nama, tahun in list_kelas_db}
    kelas_asal_nama = st.selectbox("Pilih kelas", options=kelas_dict.keys(), key="tinggal_kelas_asal")
    id_kelas_asal = kelas_dict.get(kelas_asal_nama)
    if id_kelas_asal:
        with st.spinner("Memuat siswa..."):
            conn = db.create_connection()
            siswa_di_kelas = db.get_siswa_by_kelas(conn, id_kelas_asal)
            conn.close()
        pilihan_siswa = {f"{nama} ({nis})": nis for nis, nama in siswa_di_kelas}
        siswa_terpilih_nama = st.multiselect("Pilih siswa yang tinggal kelas:", options=pilihan_siswa.keys())
        if st.button("✔️ Proses Siswa Tinggal Kelas"):
            if not siswa_terpilih_nama:
                st.error("Tidak ada siswa yang dipilih.")
                return
            with st.spinner("Memperbarui status siswa..."):
                nis_siswa_terpilih = [pilihan_siswa[nama] for nama in siswa_terpilih_nama]
                conn = db.create_connection()
                for nis in nis_siswa_terpilih:
                    db.update_status_siswa(conn, nis, "Tinggal Kelas")
                conn.close()
            st.toast(f"✅ {len(nis_siswa_terpilih)} siswa berhasil ditandai 'Tinggal Kelas'.")
            st.rerun()

def show_kelulusan():
    st.subheader("🎓 Posting Kelulusan")
    st.info("Gunakan fitur ini untuk mengubah status siswa menjadi 'Lulus'.")
    conn = db.create_connection()
    list_kelas_db = db.get_semua_kelas(conn)
    conn.close()
    if not list_kelas_db:
        st.warning("Belum ada data kelas.")
        return
    kelas_dict = {f"{nama} ({tahun})": id_kelas for id_kelas, nama, tahun in list_kelas_db}
    kelas_asal_nama = st.selectbox("Pilih kelas yang akan diluluskan", options=kelas_dict.keys(), key="lulus_kelas_asal")
    id_kelas_asal = kelas_dict.get(kelas_asal_nama)
    if id_kelas_asal:
        with st.spinner("Memuat siswa..."):
            conn = db.create_connection()
            siswa_di_kelas = db.get_siswa_by_kelas(conn, id_kelas_asal)
            conn.close()
        pilihan_siswa = {f"{nama} ({nis})": nis for nis, nama in siswa_di_kelas}
        pilih_semua = st.checkbox("Pilih Semua Siswa di Kelas Ini")
        if pilih_semua:
            siswa_terpilih_nama = list(pilihan_siswa.keys())
            st.multiselect("Siswa yang akan diluluskan:", options=pilihan_siswa.keys(), default=siswa_terpilih_nama, disabled=True)
        else:
            siswa_terpilih_nama = st.multiselect("Pilih siswa yang lulus:", options=pilihan_siswa.keys())
        if st.button("🎓 Proses Kelulusan Siswa"):
            if not siswa_terpilih_nama:
                st.error("Tidak ada siswa yang dipilih.")
                return
            with st.spinner("Memproses kelulusan..."):
                nis_siswa_terpilih = [pilihan_siswa[nama] for nama in siswa_terpilih_nama]
                conn = db.create_connection()
                for nis in nis_siswa_terpilih:
                    db.update_status_siswa(conn, nis, "Lulus")
                conn.close()
            st.toast(f"✅ {len(nis_siswa_terpilih)} siswa berhasil ditandai 'Lulus'.")
            st.rerun()

def show_cetak_kartu():
    st.subheader("💳 Cetak Kartu Pembayaran Siswa")
    
    # Inisialisasi variabel di awal untuk menghindari NameError
    siswa_terpilih_nama = None

    # Bagian UI (filter, dropdown) yang tidak ingin dicetak
    with st.container():
        st.markdown('<div class="no-print">', unsafe_allow_html=True)
        with st.spinner("Memuat data siswa..."):
            conn = db.create_connection()
            list_siswa_db = db.get_filtered_siswa_detailed(conn)
            conn.close()
        
        if not list_siswa_db:
            st.warning("Belum ada data siswa untuk dicetak kartunya.")
            st.markdown('</div>', unsafe_allow_html=True)
            return
            
        pilihan_siswa_dict = {f"{nama} ({nis})": nis for nis, _, _, nama, _, _, _, _ in list_siswa_db}
        siswa_terpilih_nama = st.selectbox("Pilih Siswa:", options=pilihan_siswa_dict.keys())
        st.markdown('</div>', unsafe_allow_html=True)

    # Hanya lanjutkan jika seorang siswa sudah dipilih dari dropdown
    if siswa_terpilih_nama:
        nis_terpilih = pilihan_siswa_dict[siswa_terpilih_nama]
        
        conn = db.create_connection()
        data_siswa = db.get_single_siswa_detailed(conn, nis_terpilih)
        conn.close()

        if data_siswa:
            # Mengatur CSS untuk print
            print_css = """
            <style>
                @media print { .no-print { display: none !important; } }
            </style>
            """
            st.markdown(print_css, unsafe_allow_html=True)

            # Mengambil data untuk nama file dan konten
            nis, _, _, nama, _, no_wa, kelas, _ = data_siswa
            # Menggunakan regex untuk membersihkan nama file dari karakter tidak valid
            safe_nama = re.sub(r'[\\/*?:"<>|]', "", nama)
            safe_kelas = re.sub(r'[\\/*?:"<>|]', "", kelas)
            nama_file_pdf = f"Kartu_{safe_nama}_{safe_kelas}_{nis}.pdf"
            
            # Membuat Barcode dan Logo dalam format Base64
            logo_base64 = ""
            try:
                with open("logo.png", "rb") as image_file:
                    logo_base64 = base64.b64encode(image_file.read()).decode()
            except FileNotFoundError:
                st.warning("File logo.png tidak ditemukan. Logo tidak akan ditampilkan.")
            
            barcode_base64 = ""
            try:
                CODE128 = barcode.get_barcode_class('code128')
                code128 = CODE128(nis_terpilih, writer=ImageWriter())
                fp = io.BytesIO()
                code128.write(fp)
                barcode_base64 = base64.b64encode(fp.getvalue()).decode()
            except Exception:
                pass

            # String HTML untuk Kartu
            # Anda bisa menyesuaikan NAMA SEKOLAH dan ALAMAT di sini
            card_html = f"""
            <!DOCTYPE html><html><head><script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.9.2/html2pdf.bundle.min.js"></script><style>body {{ font-family: sans-serif; }}.card-container {{border: 1px solid #ccc;padding: 15px;width: 450px;margin: auto;}}.header {{ display: flex; align-items: center; border-bottom: 1px solid #ccc; padding-bottom: 10px; }}.header img {{ width: 60px; margin-right: 15px; }}.header-text h3, .header-text p {{ margin: 0; }}.info {{ margin-top: 15px; }}.barcode {{ text-align: center; margin-top: 15px; }}.barcode img {{ width: 60%; }}.payment-header {{ text-align: center; background-color: #e0e0e0; padding: 5px; margin-top: 15px; font-weight: bold; }}table {{ width: 100%; border-collapse: collapse; margin-top: 5px;}}th, td {{ border: 1px solid #ddd; padding: 6px; text-align: center; font-size: 12px;}}th {{ background-color: #f2f2f2; }}.download-button {{padding: 10px 20px; font-size: 16px; color: white;background-color: #007BFF; border: none; border-radius: 5px;cursor: pointer; display: block; margin: 20px auto;}}</style></head><body><div id="kartu-siswa" class="card-container"><div class="header"><img src="data:image/png;base64,{logo_base64}" alt="logo"><div class="header-text"><h3>MADRASAH FATHAN MUBINA</h3><p>Jln. Veteran III Tapos, Ciawi, Bogor.</p></div></div><div class="info"><b>NIS:</b> {nis}<br><b>NAMA:</b> {nama}<br><b>KELAS:</b> {kelas}</div><div class="barcode"><img src="data:image/png;base64,{barcode_base64}" alt="barcode"></div><div class="payment-header">KARTU PEMBAYARAN</div><table><tr><th>BULAN</th><th>TANGGAL</th><th>NOMINAL</th><th>PETUGAS</th><th>PARAF</th></tr>{''.join(['<tr><td>&nbsp;</td><td></td><td></td><td></td><td></td></tr>' for _ in range(10)])}</table></div><button onclick="generatePDF()" class="download-button no-print">Unduh Kartu sebagai PDF</button><script>function generatePDF() {{const element = document.getElementById('kartu-siswa');const opt = {{margin:0.5,filename:'{nama_file_pdf}',image:{{ type: 'jpeg', quality: 0.98 }},html2canvas:{{ scale: 2 }},jsPDF:{{ unit: 'in', format: 'letter', orientation: 'portrait' }}}};html2pdf().from(element).set(opt).save();}}</script></body></html>
            """
            st.markdown("---")
            st.write("**Pratinjau Kartu:**")
            st.components.v1.html(card_html, height=650, scrolling=True)

# --- FUNGSI RENDER UTAMA MODUL ---
def render():
# Ganti blok <style> yang lama dengan yang ini untuk GAYA "ASAH"
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
                border-color: #007BFF !important;
                transform: translateY(-5px);
            }

            /* Penyesuaian Warna Teks di Dalam Kotak Gelap */
            .st-emotion-cache-1d8vwwt h5, [data-testid="stForm"] h6, div[data-testid="stExpander"] summary,
            [data-testid="stForm"] label {
                color: #FFFFFF !important;
                font-weight: 600;
            }
            .st-emotion-cache-1d8vwwt h5::before {
                content: ''; position: absolute; left: 0; top: 50%;
                transform: translateY(-50%); width: 8px; height: 100%;
                background-color: #007BFF; border-radius: 4px;
            }
            .st-emotion-cache-1d8vwwt h5 { position: relative; padding-left: 20px; }
            .st-emotion-cache-1d8vwwt p, div[data-testid="stExpander"] p {
                color: #E0E0E0 !important;
            }
            .st-emotion-cache-1d8vwwt p { flex-grow: 1; }

            /* --- GAYA TOMBOL (REVISI AKHIR) --- */
            /* Membuat SEMUA jenis tombol menjadi biru, termasuk di dalam form */
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
        
    st.title("📊 Modul Data Siswa")
    if 'data_siswa_view' not in st.session_state:
        st.session_state.data_siswa_view = 'menu'
    if st.session_state.data_siswa_view != 'menu':
        if st.button("⬅️ Kembali ke Menu Data Siswa"):
            st.session_state.data_siswa_view = 'menu'
            st.rerun()
    if st.session_state.data_siswa_view == 'menu':
        st.markdown("---")
        menu_options = {
            'master_kelas': {"label": "📇 Data Kelas", "desc": "Kelola data master kelas dan tahun ajaran."},
            'daftar_siswa': {"label": "➕ Daftar Siswa", "desc": "Lihat, tambah, edit, dan hapus data siswa."},
            'import_excel': {"label": "📥 Import Excel", "desc": "Impor data siswa dari file template Excel."},
            'naik_kelas': {"label": "⬆️ Naik Kelas", "desc": "Proses kenaikan kelas di kelas tertentu."},
            'pindah_kelas': {"label": "➡️ Pindah Kelas", "desc": "Pindahkan beberapa siswa ke kelas lain."},
            'tinggal_kelas': {"label": "❌ Tinggal Kelas", "desc": "Ubah status siswa menjadi 'Tinggal Kelas'."},
            'kelulusan': {"label": "🎓 Kelulusan", "desc": "Proses kelulusan untuk siswa di tingkat akhir."},
            'cetak_kartu': {"label": "💳 Cetak Kartu", "desc": "Cetak kartu pembayaran siswa."}
        }
        items = list(menu_options.items())
        num_cols = 4
        for i in range(0, len(items), num_cols):
            cols = st.columns(num_cols)
            row_items = items[i:i+num_cols]
            for j, (view, content) in enumerate(row_items):
                with cols[j]:
                    container = st.container(border=True)
                    container.markdown(f"<h5>{content['label']}</h5>", unsafe_allow_html=True)
                    container.markdown(f"<p>{content['desc']}</p>", unsafe_allow_html=True)
                    if container.button("Pilih Menu", key=f"btn_{view}", use_container_width=True):
                        st.session_state.data_siswa_view = view
                        st.rerun()
        st.markdown("---")
        if st.button("⬅️ Kembali ke Menu Utama"):
            st.session_state.page = 'home'
            if 'page' in st.query_params:
                st.query_params.clear()
            st.rerun()
    else:
        view_function_map = {
            'master_kelas': show_master_kelas, 'daftar_siswa': show_daftar_siswa, 'import_excel': show_import_excel,
            'naik_kelas': show_naik_kelas, 'pindah_kelas': show_pindah_kelas, 'tinggal_kelas': show_tinggal_kelas,
            'kelulusan': show_kelulusan, 'cetak_kartu': show_cetak_kartu
        }
        render_function = view_function_map.get(st.session_state.data_siswa_view)
        if render_function:
            render_function()