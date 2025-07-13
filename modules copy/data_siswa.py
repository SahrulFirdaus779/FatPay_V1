import streamlit as st
import pandas as pd
from utils import db_functions as db
import io
import re
import barcode
from barcode.writer import ImageWriter
import base64

def show_master_kelas():
    st.subheader("Master Data Kelas")
    # Form Tambah Kelas
    with st.form("form_tambah_kelas", clear_on_submit=True):
        nama_kelas = st.text_input("Nama Kelas (Contoh: X-A, XI-IPA-1)")
        tahun_ajaran = st.text_input("Tahun Ajaran (Contoh: 2024/2025)")
        submitted = st.form_submit_button("Tambah Kelas")
        if submitted:
            if nama_kelas and tahun_ajaran:
                conn = db.create_connection()
                db.tambah_kelas(conn, nama_kelas, tahun_ajaran)
                conn.close()
                st.success(f"Kelas '{nama_kelas}' berhasil ditambahkan.")
                st.rerun()
            else:
                st.warning("Nama Kelas dan Tahun Ajaran tidak boleh kosong.")
    
    st.markdown("---")
    
    # Tabel Data Kelas
    conn = db.create_connection()
    list_kelas = db.get_semua_kelas(conn)
    conn.close()

    if list_kelas:
        df_kelas = pd.DataFrame(list_kelas, columns=['ID', 'Nama Kelas', 'Tahun Ajaran'])
        st.dataframe(df_kelas, use_container_width=True)
        st.markdown("---")
        
        # Opsi Edit atau Hapus
        st.subheader("Edit atau Hapus Data Kelas")
        kelas_dict = {f"{nama} ({tahun})": id_kelas for id_kelas, nama, tahun in list_kelas}
        selected_kelas_nama = st.selectbox("Pilih kelas untuk diubah/dihapus", options=kelas_dict.keys())
        id_kelas_terpilih = kelas_dict.get(selected_kelas_nama)

        if id_kelas_terpilih:
            selected_details = next(item for item in list_kelas if item[0] == id_kelas_terpilih)
            
            # Form Edit
            with st.form(f"form_edit_kelas_{id_kelas_terpilih}"):
                st.write(f"**Edit Kelas: {selected_kelas_nama}**")
                edit_nama = st.text_input("Nama Kelas Baru", value=selected_details[1])
                edit_tahun = st.text_input("Tahun Ajaran Baru", value=selected_details[2])
                if st.form_submit_button("Simpan Perubahan"):
                    conn = db.create_connection()
                    db.update_kelas(conn, id_kelas_terpilih, edit_nama, edit_tahun)
                    conn.close()
                    st.success("Data kelas berhasil diperbarui!")
                    st.rerun()
            
            # Tombol Hapus
            if st.button(f"❌ Hapus Kelas: {selected_kelas_nama}", type="primary"):
                conn = db.create_connection()
                # Tambahkan pengecekan apakah ada siswa di kelas sebelum menghapus
                if db.get_siswa_by_kelas(conn, id_kelas_terpilih):
                    st.error("Tidak bisa menghapus kelas karena masih ada siswa di dalamnya.")
                else:
                    db.hapus_kelas(conn, id_kelas_terpilih)
                    st.warning(f"Kelas {selected_kelas_nama} telah dihapus.")
                    st.rerun()
                conn.close()

def show_daftar_siswa():
    st.subheader("Data Induk Siswa")
    
    # Widget Filter
    conn = db.create_connection()
    list_kelas = db.get_semua_kelas(conn)
    conn.close()

    kelas_dict = {f"{nama} ({tahun})": id_kelas for id_kelas, nama, tahun in list_kelas}
    pilihan_kelas_filter = ["Semua Kelas"] + list(kelas_dict.keys())

    col1, col2 = st.columns([2, 3])
    with col1:
        selected_kelas_filter_nama = st.selectbox("Filter per Kelas", options=pilihan_kelas_filter)
    with col2:
        search_term = st.text_input("Cari Nama atau NIS Siswa", placeholder="Ketik di sini untuk mencari...")

    id_kelas_filter = None
    if selected_kelas_filter_nama != "Semua Kelas":
        id_kelas_filter = kelas_dict[selected_kelas_filter_nama]

    # Mengambil dan Menampilkan data siswa
    conn = db.create_connection()
    list_siswa = db.get_filtered_siswa_detailed(conn, kelas_id=id_kelas_filter, search_term=search_term)
    conn.close()
    
    st.markdown("---")
    st.write(f"**Menampilkan {len(list_siswa)} data siswa:**")
    
    if list_siswa:
        df_siswa = pd.DataFrame(list_siswa, columns=['NIS', 'NIK Siswa', 'NISN', 'Nama Lengkap', 'L/P', 'No. WA Ortu', 'Kelas', 'Status'])
        st.dataframe(df_siswa, use_container_width=True)
    else:
        st.info("Tidak ada data siswa yang cocok dengan filter Anda.")

    # Form Tambah Siswa
    with st.expander("➕ Tambah Siswa Baru"):
        with st.form("form_tambah_siswa", clear_on_submit=True):
            nis = st.text_input("NO INDUK (NIS)", help="NIS harus unik untuk setiap siswa.")
            nama_lengkap = st.text_input("Nama Siswa")
            nik_siswa = st.text_input("NIK Siswa")
            nisn = st.text_input("NISN")
            jenis_kelamin = st.selectbox("Jenis Kelamin (L/P)", ["L", "P"])
            no_wa_ortu = st.text_input("No. WA Orang Tua")
            selected_kelas_nama = st.selectbox("Pilih Kelas", options=kelas_dict.keys(), key="kelas_tambah")
            
            submitted = st.form_submit_button("Tambah Siswa")
            if submitted:
                if nis and nama_lengkap and selected_kelas_nama:
                    id_kelas_terpilih = kelas_dict[selected_kelas_nama]
                    conn = db.create_connection()
                    try:
                        db.tambah_siswa(conn, nis, nik_siswa, nisn, nama_lengkap, jenis_kelamin, no_wa_ortu, id_kelas_terpilih)
                        st.success(f"Siswa '{nama_lengkap}' berhasil ditambahkan.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menambahkan siswa. Pastikan NIS unik. Error: {e}")
                    finally:
                        conn.close()
                else:
                    st.warning("NIS dan Nama Lengkap tidak boleh kosong.")
    
    # Fitur Edit dan Hapus Siswa
    if list_siswa:
        with st.expander("📝 Edit atau Hapus Data Siswa"):
            siswa_dict = {f"{nama} ({nis})": nis for nis, _, _, nama, _, _, _, _ in list_siswa}
            selected_siswa_nama = st.selectbox("Pilih siswa dari daftar di atas untuk diubah/dihapus", options=siswa_dict.keys())
            nis_terpilih = siswa_dict.get(selected_siswa_nama)
            
            if nis_terpilih:
                selected_details = next(item for item in list_siswa if item[0] == nis_terpilih)
                with st.form(f"form_edit_siswa_{nis_terpilih}"):
                    st.write(f"**Edit Siswa: {selected_siswa_nama}**")
                    edit_nik = st.text_input("NIK Siswa Baru", value=selected_details[1])
                    edit_nisn = st.text_input("NISN Baru", value=selected_details[2])
                    edit_nama = st.text_input("Nama Lengkap Baru", value=selected_details[3])
                    jk_options = ["L", "P"]
                    jk_index = jk_options.index(selected_details[4]) if selected_details[4] in jk_options else 0
                    edit_jk = st.selectbox("Jenis Kelamin Baru", options=jk_options, index=jk_index)
                    edit_no_wa = st.text_input("No. WA Orang Tua Baru", value=selected_details[5])
                    kelas_options = list(kelas_dict.keys())
                    # Mencari nama kelas yang cocok berdasarkan string kelas dari data siswa
                    current_kelas_nama = next((nama for nama in kelas_options if nama.startswith(selected_details[6])), None)
                    kelas_index = kelas_options.index(current_kelas_nama) if current_kelas_nama in kelas_options else 0
                    edit_kelas_nama = st.selectbox("Kelas Baru", options=kelas_options, index=kelas_index)

                    if st.form_submit_button("Simpan Perubahan Siswa"):
                        id_kelas_baru = kelas_dict[edit_kelas_nama]
                        conn = db.create_connection()
                        db.update_siswa(conn, nis_terpilih, edit_nik, edit_nisn, edit_nama, edit_jk, edit_no_wa, id_kelas_baru)
                        conn.close()
                        st.success("Data siswa berhasil diperbarui!")
                        st.rerun()

                if st.button(f"❌ Hapus Siswa: {selected_siswa_nama}", type="primary"):
                    conn = db.create_connection()
                    db.hapus_siswa(conn, nis_terpilih)
                    conn.close()
                    st.warning(f"Siswa {selected_siswa_nama} telah dihapus.")
                    st.rerun()

# (Fungsi show_import_excel, show_naik_kelas, show_pindah_kelas, show_tinggal_kelas, show_kelulusan, show_cetak_kartu tidak diubah)
# ... Salin semua fungsi tersebut dari kode asli Anda ke sini ...
def show_import_excel():
    st.subheader("Import Data Siswa dari File Excel")
    st.markdown("#### 1. Unduh Template")
    template_df = pd.DataFrame({'nis': ['1001'],'nik_siswa': ['3524000000000001'],'nisn': ['0012345678'],'nama_lengkap': ['Budi Santoso'],'jenis_kelamin': ['L'],'no_wa_ortu': ['081234567890']})
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
        st.warning("Belum ada data kelas. Silakan tambahkan data kelas terlebih dahulu di menu 'Data Kelas'.")
        return
    kelas_dict = {f"{nama} ({tahun})": id_kelas for id_kelas, nama, tahun in list_kelas}
    selected_kelas_nama = st.selectbox("Pilih Kelas untuk siswa yang akan di-import", options=kelas_dict.keys())
    uploaded_file = st.file_uploader("Pilih file Excel", type=['xlsx'])
    if uploaded_file is not None:
        try:
            df_upload = pd.read_excel(uploaded_file, dtype=str)
            st.write("**Preview Data dari File Anda:**")
            st.dataframe(df_upload.head())
            if st.button("🚀 Proses Import Sekarang"):
                # Menyesuaikan dengan nama kolom di template Anda
                required_columns = {'nis', 'nama_lengkap'}
                if not required_columns.issubset(df_upload.columns):
                    st.error(f"File Excel harus memiliki kolom: {list(required_columns)}")
                    return
                
                id_kelas_terpilih = kelas_dict[selected_kelas_nama]
                conn = db.create_connection()
                total_rows = len(df_upload)
                progress_bar = st.progress(0, text="Memulai proses import...")
                sukses_count, gagal_count = 0, 0
                
                for i, row in df_upload.iterrows():
                    try:
                        db.tambah_siswa(
                            conn=conn,
                            nis=row.get('nis', ''),
                            nik_siswa=row.get('nik_siswa', ''),
                            nisn=row.get('nisn', ''),
                            nama_lengkap=row.get('nama_lengkap', ''),
                            jenis_kelamin=row.get('jenis_kelamin', ''),
                            no_wa_ortu=row.get('no_wa_ortu', ''),
                            kelas_id=id_kelas_terpilih
                        )
                        sukses_count += 1
                    except Exception as e:
                        gagal_count += 1
                        st.warning(f"Gagal menambahkan NIS {row.get('nis', 'N/A')}: Pastikan NIS unik.")
                    progress_bar.progress((i + 1) / total_rows, text=f"Memproses baris {i+1}/{total_rows}")
                
                conn.close()
                st.success(f"Proses import selesai! Berhasil: {sukses_count}, Gagal: {gagal_count}.")
        except Exception as e:
            st.error(f"Terjadi kesalahan saat membaca file: {e}")

def show_naik_kelas():
    st.subheader("⬆️ Posting Kenaikan Kelas")
    st.info("Fitur ini akan memindahkan SEMUA siswa dari kelas asal ke kelas tujuan.")
    conn = db.create_connection()
    list_kelas_db = db.get_semua_kelas(conn)
    conn.close()
    if not list_kelas_db or len(list_kelas_db) < 2:
        st.warning("Data kelas tidak cukup. Anda memerlukan setidaknya 2 kelas untuk proses ini.")
        return
    kelas_dict = {f"{nama} ({tahun})": id_kelas for id_kelas, nama, tahun in list_kelas_db}
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Dari Kelas:**")
        kelas_asal_nama = st.selectbox("Pilih kelas asal", options=kelas_dict.keys(), key="kelas_asal")
    with col2:
        st.write("**Ke Kelas:**")
        pilihan_tujuan = [nama for nama in kelas_dict.keys() if nama != kelas_asal_nama]
        kelas_tujuan_nama = st.selectbox("Pilih kelas tujuan", options=pilihan_tujuan, key="kelas_tujuan")
    
    if st.button("🚀 Proses Kenaikan Kelas"):
        if not kelas_tujuan_nama or kelas_asal_nama == kelas_tujuan_nama:
            st.error("Kelas asal dan kelas tujuan tidak valid.")
            return
        
        id_kelas_asal = kelas_dict[kelas_asal_nama]
        id_kelas_tujuan = kelas_dict[kelas_tujuan_nama]
        
        conn = db.create_connection()
        siswa_di_kelas_asal = db.get_siswa_by_kelas(conn, id_kelas_asal)
        
        if not siswa_di_kelas_asal:
            st.warning(f"Tidak ada siswa di kelas {kelas_asal_nama}.")
            conn.close()
            return
            
        total_siswa = len(siswa_di_kelas_asal)
        progress_bar = st.progress(0, text=f"Memproses {total_siswa} siswa...")
        for i, (nis, nama) in enumerate(siswa_di_kelas_asal):
            db.update_kelas_siswa(conn, nis, id_kelas_tujuan)
            progress_bar.progress((i + 1) / total_siswa, text=f"Memindahkan {nama}...")
        
        conn.close()
        st.success(f"Selesai! {total_siswa} siswa telah berhasil dipindahkan dari {kelas_asal_nama} ke {kelas_tujuan_nama}.")
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
    pilihan_siswa = {} # Inisialisasi
    
    with col1:
        st.write("**Dari Kelas:**")
        kelas_asal_nama = st.selectbox("Pilih kelas asal", options=kelas_dict.keys(), key="pindah_kelas_asal")
        id_kelas_asal = kelas_dict.get(kelas_asal_nama)
        
        if id_kelas_asal:
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
            
        id_kelas_tujuan = kelas_dict[kelas_tujuan_nama]
        nis_siswa_terpilih = [pilihan_siswa[nama] for nama in siswa_terpilih_nama]
        
        conn = db.create_connection()
        for nis in nis_siswa_terpilih:
            db.update_kelas_siswa(conn, nis, id_kelas_tujuan)
        conn.close()
        st.success(f"{len(nis_siswa_terpilih)} siswa berhasil dipindahkan ke {kelas_tujuan_nama}.")
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
        conn = db.create_connection()
        siswa_di_kelas = db.get_siswa_by_kelas(conn, id_kelas_asal)
        conn.close()
        
        if not siswa_di_kelas:
            st.info("Tidak ada siswa di kelas ini.")
            return
            
        pilihan_siswa = {f"{nama} ({nis})": nis for nis, nama in siswa_di_kelas}
        siswa_terpilih_nama = st.multiselect("Pilih siswa yang tinggal kelas:", options=pilihan_siswa.keys())
        
        if st.button("✔️ Proses Siswa Tinggal Kelas"):
            if not siswa_terpilih_nama:
                st.error("Tidak ada siswa yang dipilih.")
                return
            
            nis_siswa_terpilih = [pilihan_siswa[nama] for nama in siswa_terpilih_nama]
            conn = db.create_connection()
            for nis in nis_siswa_terpilih:
                db.update_status_siswa(conn, nis, "Tinggal Kelas")
            conn.close()
            st.success(f"{len(nis_siswa_terpilih)} siswa berhasil ditandai 'Tinggal Kelas'.")
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
        conn = db.create_connection()
        siswa_di_kelas = db.get_siswa_by_kelas(conn, id_kelas_asal)
        conn.close()
        
        if not siswa_di_kelas:
            st.info("Tidak ada siswa di kelas ini.")
            return
            
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
                
            nis_siswa_terpilih = [pilihan_siswa[nama] for nama in siswa_terpilih_nama]
            conn = db.create_connection()
            for nis in nis_siswa_terpilih:
                db.update_status_siswa(conn, nis, "Lulus")
            conn.close()
            st.success(f"{len(nis_siswa_terpilih)} siswa berhasil ditandai 'Lulus'.")
            st.rerun()

def show_cetak_kartu():
    st.subheader("💳 Cetak Kartu Pembayaran Siswa")
    
    # CSS untuk menyembunyikan elemen saat print
    print_css = """
    <style>
        @media print {
            .no-print { display: none !important; }
            header, [data-testid="stSidebar"], [data-testid="stToolbar"] { display: none !important; }
            .main > div {
                padding-top: 0 !important;
                padding-left: 0 !important;
                padding-right: 0 !important;
            }
        }
    </style>
    """
    st.markdown(print_css, unsafe_allow_html=True)
    
    # Kontainer untuk widget yang tidak ingin dicetak
    with st.container(border=False):
        st.markdown('<div class="no-print">', unsafe_allow_html=True)
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

    if siswa_terpilih_nama:
        nis_terpilih = pilihan_siswa_dict[siswa_terpilih_nama]
        conn = db.create_connection()
        data_siswa = db.get_single_siswa_detailed(conn, nis_terpilih)
        conn.close()

        if data_siswa:
            # Mengambil data untuk kartu
            nis, _, _, nama, _, _, kelas, _ = data_siswa
            
            # Membuat Barcode dan Logo dalam format Base64
            logo_base64 = ""
            try:
                with open("logo.png", "rb") as image_file:
                    logo_base64 = base64.b64encode(image_file.read()).decode()
            except FileNotFoundError:
                st.warning("File logo.png tidak ditemukan.")
            
            barcode_base64 = ""
            try:
                CODE128 = barcode.get_barcode_class('code128')
                code128 = CODE128(nis_terpilih, writer=ImageWriter())
                fp = io.BytesIO()
                code128.write(fp, {'module_width':0.2, 'module_height':8, 'font_size': 8, 'text_distance': 3})
                barcode_base64 = base64.b64encode(fp.getvalue()).decode()
            except Exception as e:
                st.warning(f"Gagal membuat barcode: {e}")

            # Kontainer untuk pratinjau kartu
            with st.container():
                st.markdown("---", help="Garis ini tidak akan tercetak")
                st.write("**Pratinjau Kartu:**")
                # HTML untuk Kartu
                card_html = f"""
                <div style="border: 2px solid black; padding: 15px; width: 3.375in; height: 2.125in; box-sizing: border-box; font-family: Arial, sans-serif; margin: auto;">
                    <div style="display: flex; align-items: center; border-bottom: 1px solid black; padding-bottom: 5px;">
                        <img src="data:image/png;base64,{logo_base64}" alt="logo" style="width: 40px; height: 40px; margin-right: 10px;">
                        <div style="font-size: 8px;">
                            <h4 style="margin: 0; font-size: 9px; font-weight: bold;">NAMA SEKOLAH ANDA</h4>
                            <p style="margin: 0;">Alamat sekolah Anda di sini</p>
                        </div>
                    </div>
                    <div style="font-size: 9px; margin-top: 10px;">
                        <b>NIS:</b> {nis}<br>
                        <b>NAMA:</b> {nama.upper()}<br>
                        <b>KELAS:</b> {kelas}
                    </div>
                    <div style="text-align: center; margin-top: 8px;">
                        <img src="data:image/png;base64,{barcode_base64}" alt="barcode" style="width: 80%;">
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)

            # Tombol Cetak
            st.markdown('<div class="no-print" style="text-align: center; margin-top: 20px;"><button onclick="window.print()">Cetak Kartu</button></div>', unsafe_allow_html=True)


# --- FUNGSI RENDER UTAMA MODUL ---
def render():
    # --- UPDATE: Blok CSS diperbarui untuk UI yang lebih menarik ---
    st.markdown("""
    <style>
        /* Latar belakang utama tetap krem */
        .main, [data-testid="stAppViewContainer"] {
            background-color: #FFF7E8;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* Memberi background putih pada Form dan Expander agar menonjol */
        [data-testid="stForm"], div[data-testid="stExpander"] {
            background-color: #FFFFFF;
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #E0E0E0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            margin-top: 1rem;
        }

        /* Menghilangkan padding ganda pada expander */
        div[data-testid="stExpander"] > div[role="button"] + div {
            padding-top: 1rem !important;
        }

        /* Menambahkan sedikit jarak di atas form */
        [data-testid="stForm"] {
            margin-top: 1rem;
        }

        /* Style umum untuk tombol di dalam modul ini */
        .stButton > button {
            background-color: #007BFF !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 0.5rem 1rem !important;
            font-weight: 600;
        }
        .stButton > button:hover {
            background-color: #0056b3 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("📊 Modul Data Siswa")
    
    # Logika navigasi sub-menu
    if 'data_siswa_view' not in st.session_state:
        st.session_state.data_siswa_view = 'menu'

    # Tampilkan tombol kembali jika tidak di halaman menu utama modul
    if st.session_state.data_siswa_view != 'menu':
        if st.button("⬅️ Kembali ke Menu Data Siswa"):
            st.session_state.data_siswa_view = 'menu'
            st.rerun()

    # Router untuk sub-menu
    if st.session_state.data_siswa_view == 'menu':
        st.markdown("---")
        # Layout menu dengan 4 kolom
        col1, col2, col3, col4 = st.columns(4)
        menu_options = {
            '📇 Data Kelas': 'master_kelas', '➕ Daftar Siswa': 'daftar_siswa',
            '📥 Import Excel': 'import_excel', '⬆️ Naik Kelas': 'naik_kelas',
            '➡️ Pindah Kelas': 'pindah_kelas', '❌ Tinggal Kelas': 'tinggal_kelas',
            '🎓 Kelulusan': 'kelulusan', '💳 Cetak Kartu': 'cetak_kartu'
        }
        
        # Mendistribusikan tombol ke dalam kolom
        items = list(menu_options.items())
        
        # Membagi tombol secara merata
        buttons_per_col = (len(items) + 3) // 4
        
        with col1:
            for label, view in items[0:buttons_per_col]:
                if st.button(label, use_container_width=True):
                    st.session_state.data_siswa_view = view
                    st.rerun()
        with col2:
            for label, view in items[buttons_per_col:2*buttons_per_col]:
                if st.button(label, use_container_width=True):
                    st.session_state.data_siswa_view = view
                    st.rerun()
        with col3:
            for label, view in items[2*buttons_per_col:3*buttons_per_col]:
                if st.button(label, use_container_width=True):
                    st.session_state.data_siswa_view = view
                    st.rerun()
        with col4:
            for label, view in items[3*buttons_per_col:]:
                if st.button(label, use_container_width=True):
                    st.session_state.data_siswa_view = view
                    st.rerun()
        
        st.markdown("---")
        if st.button("⬅️ Kembali ke Menu Utama"):
            st.session_state.page = 'home'
            # Membersihkan parameter URL saat kembali ke dasbor
            if 'page' in st.query_params:
                st.query_params.clear()
            st.rerun()
    
    # Memanggil fungsi berdasarkan pilihan sub-menu
    elif st.session_state.data_siswa_view == 'master_kelas':
        show_master_kelas()
    elif st.session_state.data_siswa_view == 'daftar_siswa':
        show_daftar_siswa()
    elif st.session_state.data_siswa_view == 'import_excel':
        show_import_excel()
    elif st.session_state.data_siswa_view == 'naik_kelas':
        show_naik_kelas()
    elif st.session_state.data_siswa_view == 'pindah_kelas':
        show_pindah_kelas()
    elif st.session_state.data_siswa_view == 'tinggal_kelas':
        show_tinggal_kelas()
    elif st.session_state.data_siswa_view == 'kelulusan':
        show_kelulusan()
    elif st.session_state.data_siswa_view == 'cetak_kartu':
        show_cetak_kartu()