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
    
    with st.form("form_tambah_pos", clear_on_submit=True):
        nama_pos = st.text_input("Nama Pembayaran (Contoh: SPP Juli 2025, Uang Gedung 2025)")
        tipe = st.selectbox("Tipe Pembayaran", ["Bulanan", "Bebas", "Sukarela"])
        if st.form_submit_button("➕ Tambah Jenis Pembayaran"):
            if nama_pos and tipe:
                with st.spinner("Menyimpan..."):
                    conn = db.create_connection()
                    db.tambah_pos_pembayaran(conn, nama_pos, tipe)
                    conn.close()
                st.toast(f"✅ Jenis pembayaran '{nama_pos}' berhasil ditambahkan.")
                st.rerun()
            else:
                st.error("Nama dan Tipe Pembayaran tidak boleh kosong.")
                
    st.markdown("---")
    
    with st.spinner("Memuat data..."):
        conn = db.create_connection()
        list_pos = db.get_semua_pos_pembayaran(conn)
        conn.close()
        
    if list_pos:
        df_pos = pd.DataFrame(list_pos, columns=['ID', 'Nama Pembayaran', 'Tipe'])
        st.dataframe(df_pos, use_container_width=True, hide_index=True)
        
        with st.expander("✏️ Edit atau Hapus Jenis Pembayaran"):
            pos_dict = {f"{nama} ({tipe})": id_pos for id_pos, nama, tipe in list_pos}
            selected_pos_nama = st.selectbox("Pilih item untuk diubah/dihapus", options=pos_dict.keys(), key="edit_pos_select")
            id_pos_terpilih = pos_dict.get(selected_pos_nama)

            if id_pos_terpilih:
                selected_details = next((item for item in list_pos if item[0] == id_pos_terpilih), None)
                
                with st.form(f"form_edit_pos_{id_pos_terpilih}"):
                    st.write(f"**Edit: {selected_pos_nama}**")
                    edit_nama = st.text_input("Nama Pembayaran Baru", value=selected_details[1])
                    tipe_options = ["Bulanan", "Bebas", "Sukarela"]
                    tipe_index = tipe_options.index(selected_details[2]) if selected_details[2] in tipe_options else 0
                    edit_tipe = st.selectbox("Tipe Pembayaran Baru", options=tipe_options, index=tipe_index)
                    
                    if st.form_submit_button("Simpan Perubahan"):
                        with st.spinner("Memperbarui data..."):
                            conn = db.create_connection()
                            db.update_pos_pembayaran(conn, id_pos_terpilih, edit_nama, edit_tipe)
                            conn.close()
                        st.toast("✅ Data berhasil diperbarui!")
                        st.rerun()

                if st.button(f"❌ Hapus: {selected_pos_nama}", type="primary", key=f"hapus_pos_{id_pos_terpilih}"):
                    with st.spinner("Memeriksa & menghapus data..."):
                        conn = db.create_connection()
                        if db.is_pos_pembayaran_in_use(conn, id_pos_terpilih):
                            st.error("Gagal! Jenis pembayaran ini tidak bisa dihapus karena sudah digunakan dalam tagihan.")
                        else:
                            db.hapus_pos_pembayaran(conn, id_pos_terpilih)
                            st.toast(f"🗑️ Item '{selected_pos_nama}' telah dihapus.")
                            st.rerun()
                        conn.close()
    else:
        st.info("Belum ada data jenis pembayaran.")

def show_tagihan_siswa():
    st.subheader("🧾 Buat dan Lihat Tagihan Siswa")
    
    with st.expander("Buat Tagihan untuk Satu Angkatan/Kelas"):
        with st.spinner("Memuat data master..."):
            conn = db.create_connection()
            list_kelas = db.get_semua_kelas(conn)
            list_pos = db.get_semua_pos_pembayaran(conn)
            conn.close()
        if not list_kelas or not list_pos:
            st.warning("Data Kelas atau Jenis Pembayaran belum ada.")
            return
        kelas_dict = {f"{nama} ({tahun})": id_kelas for id_kelas, nama, tahun in list_kelas}
        pos_dict = {f"{nama} ({tipe})": id_pos for id_pos, nama, tipe in list_pos}
        with st.form("form_buat_tagihan_kelas"):
            col1, col2 = st.columns(2)
            selected_kelas_nama = col1.selectbox("Pilih Kelas", options=kelas_dict.keys())
            nominal = col1.number_input("Nominal Tagihan", min_value=0, step=50000)
            selected_pos_nama = col2.selectbox("Pilih Jenis Pembayaran", options=pos_dict.keys())
            bulan = col2.text_input("Bulan (opsional, misal: Juli)")
            if st.form_submit_button("Buat Tagihan Sekarang"):
                id_kelas, id_pos = kelas_dict[selected_kelas_nama], pos_dict[selected_pos_nama]
                with st.spinner(f"Membuat tagihan untuk kelas {selected_kelas_nama}..."):
                    conn = db.create_connection()
                    jumlah_siswa = db.buat_tagihan_satu_kelas(conn, id_kelas, id_pos, nominal, bulan if bulan else None)
                    conn.close()
                st.success(f"✅ Berhasil membuat tagihan untuk {jumlah_siswa} siswa.")

    st.markdown("---")
    st.subheader("Lihat Rincian Tagihan per Siswa")

    with st.container(border=True):
        st.write("**Filter Siswa**")
        with st.spinner("Memuat data kelas..."):
            conn = db.create_connection()
            list_kelas_filter_db = db.get_semua_kelas(conn)
            conn.close()
        kelas_dict_filter = {f"{nama} ({tahun})": id_kelas for id_kelas, nama, tahun in list_kelas_filter_db}
        col1, col2 = st.columns([2, 3])
        selected_kelas_filter_nama = col1.selectbox("Filter Kelas", ["Semua Kelas"] + list(kelas_dict_filter.keys()), key="filter_kelas_tagihan")
        search_term = col2.text_input("Cari Siswa (Nama atau NIS)", key="search_tagihan")
        id_kelas_filter = kelas_dict_filter.get(selected_kelas_filter_nama)
        with st.spinner("Mencari siswa..."):
            conn = db.create_connection()
            list_siswa_db = db.get_filtered_siswa_detailed(conn, kelas_id=id_kelas_filter, search_term=search_term)
            conn.close()
        if list_siswa_db:
            pilihan_siswa_dict = {f"{nama} ({nis})": nis for nis, _, _, nama, _, _, _, _ in list_siswa_db}
            siswa_terpilih_nama = st.selectbox("Pilih Siswa untuk melihat tagihan:", options=pilihan_siswa_dict.keys())
        else:
            st.info("Tidak ada siswa yang cocok dengan filter.")
            siswa_terpilih_nama = None

    if siswa_terpilih_nama:
        nis_terpilih = pilihan_siswa_dict[siswa_terpilih_nama]
        st.write(f"**Tagihan untuk: {siswa_terpilih_nama}**")
        with st.spinner("Memuat tagihan..."):
            conn = db.create_connection()
            tagihan_siswa = db.get_tagihan_by_siswa(conn, nis_terpilih)
            conn.close()
        if tagihan_siswa:
            df_tagihan = pd.DataFrame(tagihan_siswa, columns=['ID', 'Nama Pembayaran', 'Bulan', 'Total Tagihan', 'Sisa Tagihan', 'Status'])
            df_tagihan['Status'] = df_tagihan['Status'].apply(format_status_pembayaran)
            st.markdown(df_tagihan[['Nama Pembayaran', 'Bulan', 'Total Tagihan', 'Sisa Tagihan', 'Status']].to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.info("Siswa ini tidak memiliki tagihan.")
            
def show_transaksi_pembayaran():
    st.subheader("💳 Transaksi Pembayaran")
    with st.container(border=True):
        st.write("**1. Pilih Siswa**")
        conn = db.create_connection()
        list_kelas = db.get_semua_kelas(conn)
        conn.close()
        kelas_dict_filter = {f"{nama} ({tahun})": id_kelas for id_kelas, nama, tahun in list_kelas}
        col1, col2 = st.columns([2, 3])
        selected_kelas_filter_nama = col1.selectbox("Filter Kelas", ["Semua Kelas"] + list(kelas_dict_filter.keys()), key="filter_kelas_trx")
        search_term = col2.text_input("Cari Siswa (Nama atau NIS)", key="search_trx")
        id_kelas_filter = kelas_dict_filter.get(selected_kelas_filter_nama)
        with st.spinner("Mencari siswa..."):
            conn = db.create_connection()
            list_siswa_db = db.get_filtered_siswa_detailed(conn, kelas_id=id_kelas_filter, search_term=search_term)
            conn.close()
        if not list_siswa_db:
            st.warning("Tidak ada siswa yang cocok dengan filter Anda.")
            return
        pilihan_siswa_dict = {f"{nama} ({nis})": nis for nis, _, _, nama, _, _, _, _ in list_siswa_db}
        siswa_terpilih_nama = st.selectbox("Pilih Siswa yang Akan Membayar:", options=pilihan_siswa_dict.keys())

    if siswa_terpilih_nama:
        nis_terpilih = pilihan_siswa_dict[siswa_terpilih_nama]
        with st.spinner(f"Memuat tagihan untuk {siswa_terpilih_nama}..."):
            conn = db.create_connection()
            semua_tagihan = db.get_tagihan_by_siswa(conn, nis_terpilih)
            conn.close()
            tagihan_belum_lunas = [t for t in semua_tagihan if t[5] != "Lunas"]
        if not tagihan_belum_lunas:
            st.success(f"✅ Siswa {siswa_terpilih_nama} tidak memiliki tagihan yang belum lunas.")
            return
        st.markdown("---")
        with st.form("form_pembayaran"):
            st.write(f"**2. Pilih Tagihan untuk Dibayar**")
            pembayaran_dipilih, total_akan_dibayar = [], 0
            for tagihan in tagihan_belum_lunas:
                id_tagihan, nama_pos, bulan, _, sisa_tagihan, _ = tagihan
                label = f"{nama_pos} {bulan if bulan else ''} - Sisa: Rp {sisa_tagihan:,.0f}"
                col1, col2 = st.columns([3, 2])
                if col1.checkbox(label, key=f"pilih_{id_tagihan}"):
                    jumlah_bayar = col2.number_input("Jumlah Bayar", min_value=0.0, max_value=float(sisa_tagihan), value=float(sisa_tagihan), key=f"bayar_{id_tagihan}", label_visibility="collapsed")
                    pembayaran_dipilih.append({'id_tagihan': id_tagihan, 'jumlah_bayar': jumlah_bayar, 'label': label})
                    total_akan_dibayar += jumlah_bayar
            st.markdown("---")
            st.metric("Total Akan Dibayar", f"Rp {total_akan_dibayar:,.0f}")
            if st.form_submit_button("Proses Pembayaran"):
                if not pembayaran_dipilih:
                    st.error("Tidak ada tagihan yang dipilih untuk dibayar.")
                else:
                    with st.spinner("Memproses pembayaran..."):
                        list_untuk_db = [(item['id_tagihan'], item['jumlah_bayar']) for item in pembayaran_dipilih]
                        petugas = st.session_state.get('username', 'admin')
                        conn = db.create_connection()
                        id_transaksi = db.proses_pembayaran(conn, nis_terpilih, petugas, list_untuk_db)
                        conn.close()
                    st.success(f"Pembayaran berhasil diproses! No. Transaksi: {id_transaksi}")
                    st.balloons()
                    with st.expander("Lihat Detail Pembayaran yang Baru Saja Dilakukan", expanded=True):
                        for item in pembayaran_dipilih:
                            st.write(f"- {item['label'].split(' - ')[0]}: Rp {item['jumlah_bayar']:,.0f}")
                        st.metric("Total Dibayar", f"Rp {total_akan_dibayar:,.0f}")

def show_history_transaksi():
    st.subheader("⏳ History Transaksi Pembayaran")
    with st.container(border=True):
        search_term = st.text_input("Cari Nama Siswa, NIS, atau No. Transaksi", placeholder="Ketik di sini...")
    with st.spinner("Mencari riwayat transaksi..."):
        conn = db.create_connection()
        semua_transaksi = db.get_semua_transaksi(conn, search_term=search_term)
        conn.close()
    if not semua_transaksi:
        st.info("Tidak ada data transaksi yang cocok dengan pencarian Anda.")
        return
    st.write(f"**Menampilkan {len(semua_transaksi)} Transaksi**")
    df_transaksi = pd.DataFrame(semua_transaksi, columns=['No. Transaksi', 'Tanggal', 'NIS', 'Nama Siswa', 'Total Bayar', 'Petugas'])
    st.dataframe(df_transaksi, use_container_width=True, hide_index=True)
    st.markdown("---")
    with st.expander("Lihat Detail Transaksi"):
        pilihan_transaksi_dict = {f"No. {tr[0]} - {tr[3]} - Rp {tr[4]:,.0f}": tr[0] for tr in semua_transaksi}
        transaksi_terpilih_nama = st.selectbox("Pilih transaksi untuk melihat detail:", options=pilihan_transaksi_dict.keys())
        if transaksi_terpilih_nama:
            id_transaksi_terpilih = pilihan_transaksi_dict[transaksi_terpilih_nama]
            with st.spinner("Memuat detail..."):
                conn = db.create_connection()
                detail_transaksi = db.get_detail_by_transaksi(conn, id_transaksi_terpilih)
                conn.close()
            if detail_transaksi:
                df_detail = pd.DataFrame(detail_transaksi, columns=['Item Pembayaran', 'Bulan', 'Jumlah Dibayar'])
                # --- PERBAIKAN: Format angka di kolom 'Jumlah Dibayar' ---
                df_detail['Jumlah Dibayar'] = df_detail['Jumlah Dibayar'].apply(lambda x: f"Rp {x:,.0f}")
                st.table(df_detail)
            else:
                st.warning("Detail untuk transaksi ini tidak ditemukan.")

def show_broadcast_tagihan():
    st.subheader("📡 Broadcast Tagihan ke Orang Tua")
    st.info("Pilih jenis pembayaran, lalu klik 'Lihat Daftar Tagihan'. Klik link di kolom 'Link Kirim' untuk membuka WhatsApp.")
    with st.spinner("Memuat jenis pembayaran..."):
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
        with st.spinner("Mencari tagihan..."):
            conn = db.create_connection()
            data_broadcast = db.get_tagihan_by_pos(conn, id_pos)
            conn.close()
        if not data_broadcast:
            st.info(f"Tidak ada tagihan belum lunas untuk '{selected_pos_nama}' yang memiliki No. WA.")
            return
        st.write(f"Ditemukan {len(data_broadcast)} tagihan yang siap di-broadcast:")
        display_data = []
        for nama, no_wa, item, sisa in data_broadcast:
            pesan = f"Yth. Orang Tua dari {nama}, kami informasikan tagihan {item} sebesar Rp {sisa:,.0f} belum lunas. Terima kasih."
            pesan_url = quote(pesan)
            link = f"https://wa.me/{no_wa}?text={pesan_url}"
            display_data.append([nama, no_wa, link])
        df_broadcast = pd.DataFrame(display_data, columns=["Nama Siswa", "No. WA Ortu", "Link WhatsApp"])
        st.dataframe(df_broadcast, column_config={"Link WhatsApp": st.column_config.LinkColumn("Kirim Pesan", display_text="Buka WhatsApp")}, hide_index=True, use_container_width=True)


# --- FUNGSI RENDER UTAMA MODUL ---
def render():
    st.markdown("""
    <style>
        .main, [data-testid="stAppViewContainer"] { background-color: #FFF7E8; font-family: 'Segoe UI', sans-serif; }
        body, p, li, h1, h2, h3, h4, h5, h6, label, div[data-testid="stText"], div[data-testid="stMetricLabel"] > div { color: #343A40; }
        .st-emotion-cache-1d8vwwt, [data-testid="stForm"], div[data-testid="stExpander"], .st-container[border="true"] {
            background-color: rgba(0, 0, 0, 0.7) !important;
            border: 1px solid #495057 !important; border-radius: 12px !important;
            padding: 1.5rem !important; box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        }
        .st-emotion-cache-1d8vwwt:hover { border-color: #007BFF !important; transform: translateY(-5px); }
        .st-emotion-cache-1d8vwwt h5, [data-testid="stForm"] h6, div[data-testid="stExpander"] summary, [data-testid="stForm"] label, .st-container[border="true"] div[data-testid="stText"], [data-testid="stMetric"] {
            color: #FFFFFF !important; font-weight: 600;
        }
        .st-emotion-cache-1d8vwwt h5::before { content: ''; position: absolute; left: 0; top: 50%; transform: translateY(-50%); width: 8px; height: 100%; background-color: #007BFF; border-radius: 4px; }
        .st-emotion-cache-1d8vwwt h5 { position: relative; padding-left: 20px; }
        .st-emotion-cache-1d8vwwt p, div[data-testid="stExpander"] p, div[data-testid="stExpander"] li { color: #E0E0E0 !important; }
        .st-emotion-cache-1d8vwwt p { flex-grow: 1; }
        [data-testid="stForm"] input, [data-testid="stForm"] textarea, [data-testid="stForm"] .stSelectbox > div, .st-container[border="true"] .stSelectbox > div { color: #495057 !important; background-color: #FFFFFF !important; }
        .stButton > button, [data-testid="stDownloadButton"] > button, [data-testid="stForm"] button { background-color: #007BFF !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; }
        .stButton > button:hover, [data-testid="stDownloadButton"] > button:hover, [data-testid="stForm"] button:hover { background-color: #0056b3 !important; }
        table { color: #FFFFFF !important; }
        th { background-color: #343A40; }
        td, th { border: 1px solid #495057; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("""
    <style>
        /* Latar belakang utama */
        .main, [data-testid="stAppViewContainer"] {
            background-color: #FFF7E8;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* Teks default yang lebih lembut */
        body, p, li, h1, h2, h3, h4, h5, h6, label, div[data-testid="stText"] {
            color: #343A40; 
        }

        /* Gaya Kotak Konten */
        .st-emotion-cache-1d8vwwt,
        [data-testid="stForm"],
        div[data-testid="stExpander"],
        .st-container[border="true"] {
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
        [data-testid="stForm"] label, .st-container[border="true"] div[data-testid="stText"] {
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

        /* Membuat Form Input menjadi putih */
        [data-testid="stForm"] input, [data-testid="stForm"] textarea, 
        [data-testid="stForm"] .stSelectbox > div, .st-container[border="true"] .stSelectbox > div {
            color: #495057 !important;
            background-color: #FFFFFF !important;
        }

        /* Teks di dalam form dan expander menjadi putih */
        [data-testid="stForm"] p,
        [data-testid="stForm"] label,
        [data-testid="stForm"] div[data-testid="stMetricLabel"] > div,
        [data-testid="stForm"] div[data-testid="stMetricValue"],
        /* --- UPDATE: Aturan untuk teks di dalam expander --- */
        div[data-testid="stExpander"] p,
        div[data-testid="stExpander"] li,
        div[data-testid="stExpander"] div[data-testid="stMetricLabel"] > div,
        div[data-testid="stExpander"] div[data-testid="stMetricValue"] {
             color: #FFFFFF !important;
        }

        /* Gaya Tombol */
        .stButton > button, [data-testid="stDownloadButton"] > button, 
        [data-testid="stForm"] button {
            background-color: #007BFF !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }
        .stButton > button:hover, [data-testid="stDownloadButton"] > button:hover, 
        [data-testid="stForm"] button:hover {
            background-color: #0056b3 !important;
        }

        /* Teks pada tabel di dalam kotak gelap */
        table { color: #FFFFFF !important; }
        th { background-color: #343A40; }
        td, th { border: 1px solid #495057; }
    </style>
    """, unsafe_allow_html=True)
    st.title("💵 Modul Pembayaran")
    if 'pembayaran_view' not in st.session_state:
        st.session_state.pembayaran_view = 'menu'
    if st.session_state.pembayaran_view != 'menu':
        if st.button("⬅️ Kembali ke Menu Pembayaran", key="pembayaran_back_to_menu"):
            st.session_state.pembayaran_view = 'menu'
            st.rerun()
        st.markdown("---")
    if st.session_state.pembayaran_view == 'menu':
        st.markdown("---")
        menu_options = {
            'jenis_pembayaran': {"label": "💰 Jenis Pembayaran", "desc": "Kelola item pembayaran seperti SPP, Uang Gedung, dll."},
            'tagihan_siswa': {"label": "🧾 Tagihan Siswa", "desc": "Buat tagihan pembayaran untuk siswa per kelas atau individu."},
            'transaksi_pembayaran': {"label": "💳 Transaksi Pembayaran", "desc": "Proses pembayaran tagihan dari siswa."},
            'history_transaksi': {"label": "⏳ History Transaksi", "desc": "Lihat riwayat semua transaksi yang telah dilakukan."},
            'broadcast_tagihan': {"label": "📡 Broadcast Tagihan", "desc": "Kirim pengingat tagihan massal via WhatsApp."}
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
                    if container.button("Pilih Menu", key=f"btn_pembayaran_{view}", use_container_width=True):
                        st.session_state.pembayaran_view = view
                        st.rerun()
        st.markdown("---")
        if st.button("⬅️ Kembali ke Menu Utama"):
            st.session_state.page = 'home'
            if 'page' in st.query_params:
                st.query_params.clear()
            st.rerun()
    else:
        view_function_map = {
            'jenis_pembayaran': show_jenis_pembayaran, 'tagihan_siswa': show_tagihan_siswa,
            'transaksi_pembayaran': show_transaksi_pembayaran, 'history_transaksi': show_history_transaksi,
            'broadcast_tagihan': show_broadcast_tagihan
        }
        render_function = view_function_map.get(st.session_state.pembayaran_view)
        if render_function:
            render_function()