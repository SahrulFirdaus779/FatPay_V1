# utils/db_functions.py (Versi Final yang Diperbaiki)

# Pastikan Anda sudah menginstal pustaka bcrypt:
# pip install bcrypt
import sqlite3
import bcrypt
from datetime import datetime
import pandas as pd

# --- Fungsi Koneksi dan Setup Database ---

def create_connection():
    """Membuat koneksi ke database dan mengaktifkan foreign key constraints."""
    conn = None
    try:
        conn = sqlite3.connect("fatpay.db")
        conn.execute("PRAGMA foreign_keys = ON;") # Penting untuk integritas data
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
    return conn

def create_tables(conn):
    """Membuat semua tabel yang diperlukan jika belum ada."""
    try:
        cursor = conn.cursor()
        # Tabel users dengan password yang di-hash
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            );
        """)
        # Tabel kelas dengan kolom angkatan
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kelas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                angkatan TEXT NOT NULL,
                nama_kelas TEXT NOT NULL,
                tahun_ajaran TEXT NOT NULL
            );
        """)
        # Tabel siswa
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS siswa (
                nis TEXT PRIMARY KEY,
                nik_siswa TEXT,
                nisn TEXT,
                nama_lengkap TEXT NOT NULL,
                jenis_kelamin TEXT,
                no_wa_ortu TEXT,
                id_kelas INTEGER,
                status TEXT NOT NULL DEFAULT 'Aktif',
                FOREIGN KEY (id_kelas) REFERENCES kelas (id) ON DELETE SET NULL
            );
        """)
        # Tabel pos_pembayaran
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pos_pembayaran (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama_pos TEXT NOT NULL,
                tipe TEXT NOT NULL
            );
        """)
        # Tabel tagihan
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tagihan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nis_siswa TEXT NOT NULL,
                id_pos INTEGER NOT NULL,
                bulan TEXT,
                nominal_tagihan REAL NOT NULL,
                sisa_tagihan REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'Belum Lunas',
                FOREIGN KEY (nis_siswa) REFERENCES siswa (nis) ON DELETE CASCADE,
                FOREIGN KEY (id_pos) REFERENCES pos_pembayaran (id) ON DELETE CASCADE
            );
        """)
        # Tabel transaksi
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transaksi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tanggal TEXT NOT NULL,
                nis_siswa TEXT NOT NULL,
                total_bayar REAL NOT NULL,
                petugas TEXT NOT NULL,
                FOREIGN KEY (nis_siswa) REFERENCES siswa (nis)
            );
        """)
        # Tabel detail_transaksi
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detail_transaksi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_transaksi INTEGER NOT NULL,
                id_tagihan INTEGER NOT NULL,
                jumlah_bayar REAL NOT NULL,
                FOREIGN KEY (id_transaksi) REFERENCES transaksi (id) ON DELETE CASCADE,
                FOREIGN KEY (id_tagihan) REFERENCES tagihan (id)
            );
        """)
        print("Pemeriksaan dan pembuatan tabel berhasil.")
    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")

def setup_database():
    """Menjalankan setup awal database."""
    conn = create_connection()
    if conn is not None:
        create_tables(conn)
        conn.close()

# --- Fungsi-fungsi untuk User (dengan bcrypt) ---

def hash_password(password):
    """Menghasilkan hash dari password menggunakan bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(hashed_password, user_password):
    """Memverifikasi password dengan hash-nya."""
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password)

def tambah_user(conn, username, password, role):
    """Menambah user baru dengan password yang di-hash."""
    hashed_pw = hash_password(password)
    sql = ''' INSERT INTO users(username,password,role) VALUES(?,?,?) '''
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (username, hashed_pw, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Username sudah ada

def check_login(conn, username, password):
    """Memeriksa kredensial login user."""
    cursor = conn.cursor()
    cursor.execute("SELECT password, role FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    if result and check_password(result[0], password):
        return result[1] # Return role
    return None

def get_all_users(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users")
    return cursor.fetchall()

def update_user_password(conn, username, new_password):
    hashed_pw = hash_password(new_password)
    sql = ''' UPDATE users SET password = ? WHERE username = ? '''
    cursor = conn.cursor()
    cursor.execute(sql, (hashed_pw, username))
    conn.commit()

def hapus_user(conn, username):
    if username.lower() == 'admin':
        return False # Admin tidak boleh dihapus
    sql = 'DELETE FROM users WHERE username = ?'
    cursor = conn.cursor()
    cursor.execute(sql, (username,))
    conn.commit()
    return cursor.rowcount > 0

def get_transactions_for_preview(conn):
    """
    Mengambil semua data transaksi dari koneksi database yang diberikan
    untuk ditampilkan dalam pratinjau.
    Mengembalikan data sebagai Pandas DataFrame.
    """
    query = """
    SELECT
        t.id AS id_transaksi,
        t.tanggal,
        s.nama AS nama_siswa,
        s.nis,
        SUM(td.jumlah_bayar) AS total_bayar
    FROM transaksi t
    JOIN siswa s ON t.nis_siswa = s.nis
    JOIN transaksi_detail td ON t.id = td.id_transaksi
    GROUP BY t.id, t.tanggal, s.nama, s.nis
    ORDER BY t.tanggal DESC;
    """
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        # Mengembalikan DataFrame kosong jika ada error (misal: tabel tidak ada)
        print(f"Error saat pratinjau data: {e}")
        return pd.DataFrame()


# --- Fungsi-fungsi untuk Kelas (dengan Angkatan) ---

def tambah_kelas(conn, angkatan, nama_kelas, tahun_ajaran):
    sql = ''' INSERT INTO kelas(angkatan, nama_kelas, tahun_ajaran) VALUES(?,?,?) '''
    cursor = conn.cursor()
    cursor.execute(sql, (angkatan, nama_kelas, tahun_ajaran))
    conn.commit()
    return cursor.lastrowid

def get_semua_kelas(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, angkatan, nama_kelas, tahun_ajaran FROM kelas ORDER BY angkatan DESC, nama_kelas ASC")
    return cursor.fetchall()
    
def get_semua_angkatan(conn):
    """Mengambil semua angkatan unik dari tabel kelas."""
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT angkatan FROM kelas ORDER BY angkatan DESC")
    return [row[0] for row in cursor.fetchall()]

def update_kelas(conn, id_kelas, angkatan_baru, nama_baru, tahun_ajaran_baru):
    sql = ''' UPDATE kelas SET angkatan = ?, nama_kelas = ?, tahun_ajaran = ? WHERE id = ? '''
    cursor = conn.cursor()
    cursor.execute(sql, (angkatan_baru, nama_baru, tahun_ajaran_baru, id_kelas))
    conn.commit()

def update_kelas_siswa(conn, nis, id_kelas_baru):
    """
    HANYA memperbarui kolom id_kelas untuk seorang siswa berdasarkan NIS.
    Fungsi ini khusus untuk fitur pindah/naik kelas.
    """
    sql = ''' UPDATE siswa
              SET id_kelas = ?
              WHERE nis = ? '''
    cursor = conn.cursor()
    cursor.execute(sql, (id_kelas_baru, nis))
    conn.commit()

def hapus_kelas(conn, id_kelas):
    sql = 'DELETE FROM kelas WHERE id = ?'
    cursor = conn.cursor()
    cursor.execute(sql, (id_kelas,))
    conn.commit()

# Tambahkan di bagian --- Fungsi-fungsi untuk Kelas ---
def get_semua_kelas_dengan_jumlah_siswa(conn):
    """Mengambil semua data kelas beserta jumlah siswa aktif di dalamnya."""
    cursor = conn.cursor()
    query = """
        SELECT k.id, k.angkatan, k.nama_kelas, k.tahun_ajaran, COUNT(s.nis) as jumlah_siswa
        FROM kelas k
        LEFT JOIN siswa s ON k.id = s.id_kelas AND s.status = 'Aktif'
        GROUP BY k.id, k.angkatan, k.nama_kelas, k.tahun_ajaran
        ORDER BY k.angkatan DESC, k.nama_kelas ASC
    """
    cursor.execute(query)
    return cursor.fetchall()

def update_status_siswa(conn, nis, status_baru):
    """Memperbarui status seorang siswa (misal: Aktif, Lulus, Tinggal Kelas)."""
    sql = ''' UPDATE siswa
              SET status = ?
              WHERE nis = ? '''
    cursor = conn.cursor()
    cursor.execute(sql, (status_baru, nis))
    conn.commit()
    
# --- Fungsi-fungsi untuk Siswa ---

def tambah_siswa(conn, nis, nik_siswa, nisn, nama_lengkap, jenis_kelamin, no_wa_ortu, id_kelas):
    sql = ''' INSERT INTO siswa(nis, nik_siswa, nisn, nama_lengkap, jenis_kelamin, no_wa_ortu, id_kelas)
              VALUES(?,?,?,?,?,?,?) '''
    cursor = conn.cursor()
    cursor.execute(sql, (nis, nik_siswa, nisn, nama_lengkap, jenis_kelamin, no_wa_ortu, id_kelas))
    conn.commit()

def update_siswa(conn, nis, nik, nisn, nama, jenis_kelamin, no_wa, id_kelas):
    sql = ''' UPDATE siswa
              SET nik_siswa = ?, nisn = ?, nama_lengkap = ?, jenis_kelamin = ?, no_wa_ortu = ?, id_kelas = ?
              WHERE nis = ? '''
    cursor = conn.cursor()
    cursor.execute(sql, (nik, nisn, nama, jenis_kelamin, no_wa, id_kelas, nis))
    conn.commit()
    
def hapus_siswa(conn, nis):
    sql = 'DELETE FROM siswa WHERE nis = ?'
    cursor = conn.cursor()
    cursor.execute(sql, (nis,))
    conn.commit()

def get_filtered_siswa_detailed(conn, angkatan=None, kelas_id=None, search_term=None):
    """Mengambil data siswa dengan filter berdasarkan angkatan, kelas, dan/atau nama/NIS."""
    cursor = conn.cursor()
    query = """
        SELECT s.nis, s.nik_siswa, s.nisn, s.nama_lengkap, s.jenis_kelamin, s.no_wa_ortu, k.nama_kelas, s.status, k.angkatan
        FROM siswa s
        LEFT JOIN kelas k ON s.id_kelas = k.id
    """
    conditions = []
    params = []
    
    if angkatan:
        conditions.append("k.angkatan = ?")
        params.append(angkatan)
    if kelas_id:
        conditions.append("s.id_kelas = ?")
        params.append(kelas_id)
    if search_term:
        conditions.append("(s.nama_lengkap LIKE ? OR s.nis LIKE ?)")
        params.extend([f"%{search_term}%", f"%{search_term}%"])
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    cursor.execute(query, params)
    return cursor.fetchall()

def get_single_siswa_detailed(conn, nis):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.nis, s.nik_siswa, s.nisn, s.nama_lengkap, s.jenis_kelamin, s.no_wa_ortu, k.nama_kelas, s.status
        FROM siswa s
        LEFT JOIN kelas k ON s.id_kelas = k.id
        WHERE s.nis = ?
    """, (nis,))
    return cursor.fetchone()

def get_siswa_by_kelas(conn, id_kelas):
    cursor = conn.cursor()
    cursor.execute("SELECT nis, nama_lengkap FROM siswa WHERE id_kelas = ?", (id_kelas,))
    return cursor.fetchall()

def get_single_siswa_detailed(conn, nis):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.nis, s.nik_siswa, s.nisn, s.nama_lengkap, s.jenis_kelamin, s.no_wa_ortu, k.nama_kelas, s.status, k.angkatan
        FROM siswa s
        LEFT JOIN kelas k ON s.id_kelas = k.id
        WHERE s.nis = ?
    """, (nis,))
    return cursor.fetchone()

# --- Fungsi-fungsi untuk POS Pembayaran & Tagihan ---
# (Tidak ada perubahan signifikan di sini, fungsi tetap sama)

def tambah_pos_pembayaran(conn, nama_pos, tipe):
    sql = ''' INSERT INTO pos_pembayaran(nama_pos, tipe) VALUES(?,?) '''
    cursor = conn.cursor()
    cursor.execute(sql, (nama_pos, tipe))
    conn.commit()

def get_semua_pos_pembayaran(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, nama_pos, tipe FROM pos_pembayaran")
    return cursor.fetchall()

def update_pos_pembayaran(conn, id_pos, nama_baru, tipe_baru):
    sql = ''' UPDATE pos_pembayaran SET nama_pos = ?, tipe = ? WHERE id = ? '''
    cursor = conn.cursor()
    cursor.execute(sql, (nama_baru, tipe_baru, id_pos))
    conn.commit()

def hapus_pos_pembayaran(conn, id_pos):
    sql = 'DELETE FROM pos_pembayaran WHERE id = ?'
    cursor = conn.cursor()
    cursor.execute(sql, (id_pos,))
    conn.commit()

def buat_tagihan_satu_kelas(conn, id_kelas, id_pos, nominal, bulan=None):
    cursor = conn.cursor()
    cursor.execute("SELECT nis FROM siswa WHERE id_kelas = ? AND status = 'Aktif'", (id_kelas,))
    list_nis_siswa = cursor.fetchall()
    sql = ''' INSERT INTO tagihan(nis_siswa, id_pos, bulan, nominal_tagihan, sisa_tagihan)
              VALUES(?,?,?,?,?) '''
    for nis in list_nis_siswa:
        cursor.execute(sql, (nis[0], id_pos, bulan, nominal, nominal))
    conn.commit()
    return len(list_nis_siswa)

def get_tagihan_by_siswa(conn, nis):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.id, p.nama_pos, t.bulan, t.nominal_tagihan, t.sisa_tagihan, t.status
        FROM tagihan t
        JOIN pos_pembayaran p ON t.id_pos = p.id
        WHERE t.nis_siswa = ? AND t.status = 'Belum Lunas'
    """, (nis,))
    return cursor.fetchall()

def get_tagihan_by_pos(conn, id_pos):
    """
    Mengambil data tagihan yang belum lunas untuk satu jenis pembayaran (pos) tertentu.
    Hanya mengambil data siswa yang memiliki No. WA Orang Tua.
    Mengembalikan daftar berisi (nama_siswa, no_wa_ortu, nama_pembayaran, sisa_tagihan).
    """
    sql = """
        SELECT
            s.nama_lengkap,
            s.no_wa_ortu,
            pp.nama_pos,
            t.sisa_tagihan
        FROM
            tagihan t
        JOIN
            siswa s ON t.nis_siswa = s.nis
        JOIN
            pos_pembayaran pp ON t.id_pos = pp.id -- <-- PERBAIKAN 1
        WHERE
            t.id_pos = ? -- <-- PERBAIKAN 2
            AND t.sisa_tagihan > 0
            AND s.no_wa_ortu IS NOT NULL
            AND s.no_wa_ortu != ''
    """
    cursor = conn.cursor()
    cursor.execute(sql, (id_pos,))
    rows = cursor.fetchall()
    return rows

def is_pos_pembayaran_in_use(conn, id_pos):
    """
    Memeriksa apakah sebuah jenis pembayaran (POS) sudah digunakan di tabel tagihan.
    Mengembalikan True jika sudah digunakan, False jika belum.
    """
    cursor = conn.cursor()
    # Query sederhana untuk memeriksa keberadaan record
    cursor.execute("SELECT 1 FROM tagihan WHERE id_pos = ? LIMIT 1", (id_pos,))
    result = cursor.fetchone()
    # Jika fetchone() mengembalikan sesuatu (bukan None), berarti data digunakan
    return result is not None

# Tambahkan dua fungsi ini ke utils/db_functions.py

def get_tagihan_by_kelas_and_pos(conn, id_kelas, id_pos):
    """Mengambil detail tagihan yang baru dibuat untuk kelas dan pos tertentu."""
    sql = """
        SELECT s.nama_lengkap, p.nama_pos, t.bulan, t.nominal_tagihan
        FROM tagihan t
        JOIN siswa s ON t.nis_siswa = s.nis
        JOIN pos_pembayaran p ON t.id_pos = p.id
        WHERE s.id_kelas = ? AND t.id_pos = ?
        ORDER BY s.nama_lengkap
    """
    cursor = conn.cursor()
    cursor.execute(sql, (id_kelas, id_pos))
    return cursor.fetchall()

def get_all_tagihan_by_kelas(conn, id_kelas):
    """Mengambil semua tagihan (lunas/belum) untuk semua siswa di satu kelas."""
    sql = """
        SELECT s.nama_lengkap, s.nis, p.nama_pos, t.bulan, t.nominal_tagihan, t.sisa_tagihan, t.status
        FROM tagihan t
        JOIN siswa s ON t.nis_siswa = s.nis
        JOIN pos_pembayaran p ON t.id_pos = p.id
        WHERE s.id_kelas = ?
        ORDER BY s.nama_lengkap, p.nama_pos
    """
    cursor = conn.cursor()
    cursor.execute(sql, (id_kelas,))
    return cursor.fetchall()

def get_broadcast_data(conn, list_of_id_pos, angkatan=None, kelas_id=None, search_term=None):
    """
    Mengambil data untuk broadcast tagihan dari BEBERAPA jenis pembayaran sekaligus
    dengan filter lengkap, termasuk pencarian nama/NIS.
    """
    cursor = conn.cursor()
    
    if not list_of_id_pos:
        return []

    placeholders = ', '.join('?' * len(list_of_id_pos))
    params = list_of_id_pos
    
    sql = f"""
        SELECT
            s.nama_lengkap, s.no_wa_ortu, k.nama_kelas, p.nama_pos, t.sisa_tagihan
        FROM tagihan t
        JOIN siswa s ON t.nis_siswa = s.nis
        JOIN pos_pembayaran p ON t.id_pos = p.id
        LEFT JOIN kelas k ON s.id_kelas = k.id
        WHERE 
            t.id_pos IN ({placeholders})
            AND t.sisa_tagihan > 0
            AND s.no_wa_ortu IS NOT NULL AND s.no_wa_ortu != ''
    """

    if angkatan:
        sql += " AND k.angkatan = ?"
        params.append(angkatan)
    
    if kelas_id:
        sql += " AND s.id_kelas = ?"
        params.append(kelas_id)
        
    # --- TAMBAHAN: Logika untuk pencarian nama/NIS ---
    if search_term:
        sql += " AND (s.nama_lengkap LIKE ? OR s.nis LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
        
    sql += " GROUP BY s.nis, p.id ORDER BY k.angkatan, k.nama_kelas, s.nama_lengkap"
    
    cursor.execute(sql, tuple(params))
    return cursor.fetchall()
# --- Fungsi-fungsi untuk Transaksi (dengan perbaikan) ---

def proses_pembayaran(conn, nis_siswa, petugas, list_pembayaran):
    """Memproses pembayaran dalam satu transaksi atomik (semua berhasil atau semua gagal)."""
    cursor = conn.cursor()
    tanggal_transaksi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_bayar = sum(item[1] for item in list_pembayaran)
    
    try:
        # Mulai transaksi
        cursor.execute("BEGIN TRANSACTION")

        # 1. Masukkan ke tabel transaksi
        cursor.execute("INSERT INTO transaksi (tanggal, nis_siswa, total_bayar, petugas) VALUES (?, ?, ?, ?)",
                       (tanggal_transaksi, nis_siswa, total_bayar, petugas))
        id_transaksi_baru = cursor.lastrowid

        # 2. Loop untuk detail transaksi dan update tagihan
        for id_tagihan, jumlah_bayar in list_pembayaran:
            cursor.execute("INSERT INTO detail_transaksi (id_transaksi, id_tagihan, jumlah_bayar) VALUES (?, ?, ?)",
                           (id_transaksi_baru, id_tagihan, jumlah_bayar))
            
            cursor.execute("UPDATE tagihan SET sisa_tagihan = sisa_tagihan - ? WHERE id = ?",
                           (jumlah_bayar, id_tagihan))
            
            cursor.execute("SELECT sisa_tagihan FROM tagihan WHERE id = ?", (id_tagihan,))
            sisa_tagihan_terbaru = cursor.fetchone()[0]
            
            if sisa_tagihan_terbaru <= 0:
                cursor.execute("UPDATE tagihan SET status = 'Lunas', sisa_tagihan = 0 WHERE id = ?", (id_tagihan,))
        
        # Jika semua berhasil, commit transaksi
        conn.commit()
        return id_transaksi_baru

    except sqlite3.Error as e:
        # Jika ada error, batalkan semua perubahan
        print(f"Transaksi gagal: {e}")
        conn.rollback()
        return None
def get_semua_transaksi(conn, search_term=None):
    """Mengambil semua data transaksi, dengan opsi pencarian."""
    cursor = conn.cursor()
    
    query = """
        SELECT t.id, t.tanggal, t.nis_siswa, s.nama_lengkap, t.total_bayar, t.petugas
        FROM transaksi t
        JOIN siswa s ON t.nis_siswa = s.nis
    """
    
    params = []
    if search_term:
        query += " WHERE (s.nama_lengkap LIKE ? OR s.nis LIKE ? OR t.id LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
        
    query += " ORDER BY t.id DESC"
    
    cursor.execute(query, params)
    return cursor.fetchall()

def get_detail_by_transaksi(conn, id_transaksi):
    """
    Mengambil rincian item dari sebuah transaksi.
    Menggunakan LEFT JOIN agar lebih kuat terhadap data yang mungkin hilang.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            p.nama_pos, 
            t.bulan, 
            dt.jumlah_bayar
        FROM detail_transaksi dt
        LEFT JOIN tagihan t ON dt.id_tagihan = t.id
        LEFT JOIN pos_pembayaran p ON t.id_pos = p.id
        WHERE dt.id_transaksi = ?
    """, (id_transaksi,))
    return cursor.fetchall()

# --- Fungsi-fungsi untuk Laporan (dengan filter Angkatan) ---

def get_laporan_kas_umum(conn, tanggal_mulai, tanggal_sampai, angkatan=None, id_pos=None, kelas_id=None, search_term=None):
    """Mengambil data transaksi dengan filter lengkap untuk laporan kas umum."""
    cursor = conn.cursor()
    
    params = [tanggal_mulai, tanggal_sampai]
    
    query = """
    SELECT
        t.id,
        t.tanggal,
        p.nama_pos as jenis_pos,
        'Pembayaran ' || p.nama_pos || ' oleh ' || s.nama_lengkap AS uraian,
        t.total_bayar AS pemasukan
    FROM transaksi t
    JOIN siswa s ON t.nis_siswa = s.nis
    JOIN kelas k ON s.id_kelas = k.id
    JOIN (
        SELECT dt.id_transaksi, MIN(tgh.id_pos) as id_pos
        FROM detail_transaksi dt
        JOIN tagihan tgh ON dt.id_tagihan = tgh.id
        GROUP BY dt.id_transaksi
    ) AS detail ON t.id = detail.id_transaksi
    JOIN pos_pembayaran p ON detail.id_pos = p.id
    WHERE DATE(t.tanggal) BETWEEN ? AND ?
    """
    
    if angkatan:
        query += " AND k.angkatan = ?"
        params.append(angkatan)
    
    if id_pos:
        query += " AND p.id = ?"
        params.append(id_pos)
    
    if kelas_id:
        query += " AND s.id_kelas = ?"
        params.append(kelas_id)
        
    if search_term:
        query += " AND (s.nama_lengkap LIKE ? OR s.nis LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
        
    query += " ORDER BY t.tanggal"
    
    cursor.execute(query, tuple(params))
    return cursor.fetchall()


def get_rekap_saldo_per_pos(conn):
    """Menghitung total pemasukan untuk setiap jenis POS pembayaran."""
    cursor = conn.cursor()
    query = """
        SELECT
            p.nama_pos,
            SUM(dt.jumlah_bayar) as total_diterima
        FROM detail_transaksi dt
        JOIN tagihan t ON dt.id_tagihan = t.id
        JOIN pos_pembayaran p ON t.id_pos = p.id
        GROUP BY p.nama_pos
        ORDER BY p.id
    """
    cursor.execute(query)
    return cursor.fetchall()

def get_semua_tunggakan(conn, angkatan=None, kelas_id=None, search_term=None):
    """Mengambil semua data tunggakan dengan filter lengkap."""
    cursor = conn.cursor()
    query = """
        SELECT s.nis, s.nama_lengkap, k.nama_kelas, p.nama_pos, t.bulan, t.sisa_tagihan, k.angkatan
        FROM tagihan t
        JOIN siswa s ON t.nis_siswa = s.nis
        JOIN kelas k ON s.id_kelas = k.id
        JOIN pos_pembayaran p ON t.id_pos = p.id
        WHERE t.status = 'Belum Lunas' AND t.sisa_tagihan > 0
    """
    params = []
    
    if angkatan:
        query += " AND k.angkatan = ?"
        params.append(angkatan)
    if kelas_id:
        query += " AND s.id_kelas = ?"
        params.append(kelas_id)
    if search_term:
        query += " AND (s.nama_lengkap LIKE ? OR s.nis LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
        
    query += " ORDER BY k.angkatan, k.nama_kelas, s.nama_lengkap"
    cursor.execute(query, tuple(params))
    return cursor.fetchall()

def get_rekap_pembayaran(conn, tanggal_mulai, tanggal_sampai, angkatan=None, kelas_id=None, id_pos=None):
    """Menghitung rekap total pemasukan per POS dengan filter lengkap."""
    cursor = conn.cursor()
    params = [tanggal_mulai, tanggal_sampai]
    query = """
        SELECT p.nama_pos, SUM(dt.jumlah_bayar) as total_diterima
        FROM detail_transaksi dt
        JOIN transaksi t ON dt.id_transaksi = t.id
        JOIN siswa s ON t.nis_siswa = s.nis
        JOIN kelas k ON s.id_kelas = k.id
        JOIN tagihan tag ON dt.id_tagihan = tag.id
        JOIN pos_pembayaran p ON tag.id_pos = p.id
        WHERE DATE(t.tanggal) BETWEEN ? AND ?
    """
    
    if angkatan:
        query += " AND k.angkatan = ?"
        params.append(angkatan)
    if kelas_id:
        query += " AND s.id_kelas = ?"
        params.append(kelas_id)
    if id_pos:
        query += " AND p.id = ?"
        params.append(id_pos)
        
    query += " GROUP BY p.nama_pos ORDER BY p.id"
    cursor.execute(query, tuple(params))
    return cursor.fetchall()


def get_transaksi_by_id(conn, id_transaksi):
    """Mengambil data lengkap satu transaksi untuk keperluan cetak bukti."""
    cursor = conn.cursor()
    query = """
        SELECT 
            t.id, 
            t.tanggal, 
            t.nis_siswa, 
            s.nama_lengkap, 
            k.nama_kelas, 
            t.total_bayar, 
            t.petugas
        FROM transaksi t
        JOIN siswa s ON t.nis_siswa = s.nis
        LEFT JOIN kelas k ON s.id_kelas = k.id
        WHERE t.id = ?
    """
    cursor.execute(query, (id_transaksi,))
    return cursor.fetchone()

def get_filtered_transaksi(conn, search_term=None, kelas_id=None, angkatan=None):
    """
    Mengambil data transaksi dengan filter berdasarkan nama/NIS, kelas, dan angkatan.
    """
    # Query ini telah diperbaiki agar sesuai dengan skema tabel Anda
    query = """
        SELECT DISTINCT 
            t.id, 
            t.tanggal, 
            s.nis, 
            s.nama_lengkap, 
            t.total_bayar, 
            k.nama_kelas, 
            k.angkatan
        FROM transaksi t
        JOIN siswa s ON t.nis_siswa = s.nis
        LEFT JOIN kelas k ON s.id_kelas = k.id
        WHERE 1=1
    """
    params = []

    if search_term:
        query += " AND (s.nama_lengkap LIKE ? OR s.nis LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])

    if kelas_id:
        query += " AND k.id = ?"
        params.append(kelas_id)

    if angkatan:
        query += " AND k.angkatan = ?"
        params.append(angkatan)

    # Nama kolom di ORDER BY juga diperbaiki
    query += " ORDER BY t.tanggal DESC"

    cur = conn.cursor()
    cur.execute(query, tuple(params))
    return cur.fetchall()

def get_transactions_for_preview(conn):
    """
    (VERSI FINAL) Mengambil data transaksi untuk pratinjau dengan nama tabel dan kolom yang sudah benar.
    """
    # Query ini telah diperbaiki agar sesuai dengan skema database Anda.
    query = """
    SELECT
        t.id AS id_transaksi,
        t.tanggal,
        s.nama_lengkap AS nama_siswa, 
        s.nis,
        SUM(td.jumlah_bayar) AS total_bayar
    FROM transaksi t
    JOIN siswa s ON t.nis_siswa = s.nis
    JOIN detail_transaksi td ON t.id = td.id_transaksi 
    GROUP BY t.id, t.tanggal, s.nama_lengkap, s.nis
    ORDER BY t.tanggal DESC;
    """
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"Error saat pratinjau data: {e}")
        return pd.DataFrame()

def export_transactions_to_new_db(main_db_path, new_db_path, start_date, end_date):
    """
    Mengekspor data transaksi dalam rentang tanggal tertentu dari database utama
    ke sebuah file database SQLite baru.
    """
    try:
        conn_main = sqlite3.connect(main_db_path)
        query_transaksi = "SELECT * FROM transaksi WHERE DATE(tanggal) BETWEEN ? AND ?"
        df_transaksi = pd.read_sql_query(query_transaksi, conn_main, params=(start_date, end_date))

        if df_transaksi.empty:
            conn_main.close()
            return {'success': True, 'count': 0, 'message': 'Tidak ada transaksi ditemukan.'}

        conn_new = sqlite3.connect(new_db_path)
        list_id_transaksi = df_transaksi['id'].tolist()
        list_nis_siswa = df_transaksi['nis_siswa'].unique().tolist()
        placeholders_trx = ','.join('?' for _ in list_id_transaksi)
        placeholders_nis = ','.join('?' for _ in list_nis_siswa)

        df_detail = pd.read_sql_query(f"SELECT * FROM detail_transaksi WHERE id_transaksi IN ({placeholders_trx})", conn_main, params=list_id_transaksi)
        df_siswa = pd.read_sql_query(f"SELECT * FROM siswa WHERE nis IN ({placeholders_nis})", conn_main, params=list_nis_siswa)

        df_users = pd.read_sql_query("SELECT * FROM users", conn_main)
        df_kelas = pd.read_sql_query("SELECT * FROM kelas", conn_main)
        df_pos = pd.read_sql_query("SELECT * FROM pos_pembayaran", conn_main)
        df_tagihan = pd.read_sql_query(f"SELECT * FROM tagihan WHERE nis_siswa IN ({placeholders_nis})", conn_main, params=list_nis_siswa)

        df_users.to_sql('users', conn_new, if_exists='replace', index=False)
        df_kelas.to_sql('kelas', conn_new, if_exists='replace', index=False)
        df_pos.to_sql('pos_pembayaran', conn_new, if_exists='replace', index=False)
        df_tagihan.to_sql('tagihan', conn_new, if_exists='replace', index=False)
        df_siswa.to_sql('siswa', conn_new, if_exists='replace', index=False)
        df_transaksi.to_sql('transaksi', conn_new, if_exists='replace', index=False)
        df_detail.to_sql('detail_transaksi', conn_new, if_exists='replace', index=False)
        
        conn_main.close()
        conn_new.close()
        
        return {'success': True, 'count': len(df_transaksi), 'message': 'Ekspor berhasil.'}

    except Exception as e:
        error_message = f"Gagal mengekspor transaksi: {e}"
        print(error_message)
        return {'success': False, 'count': 0, 'message': error_message}
    
# Tambahkan/Ganti fungsi ini di utils/db_functions.py

def merge_transactions_from_db(main_conn, source_db_path):
    """
    Menggabungkan data dari database sumber ke database utama dengan logika cerdas.
    - Melewati transaksi yang sudah ada.
    - Menambahkan siswa baru jika belum ada.
    - Mengembalikan statistik proses.
    """
    # 1. Inisialisasi statistik
    stats = {'added': 0, 'skipped': 0, 'errors': 0}
    
    # Koneksi ke database sumber (file yang di-upload)
    source_conn = sqlite3.connect(source_db_path)
    
    main_cursor = main_conn.cursor()
    source_cursor = source_conn.cursor()

    try:
        # 2. Ambil semua ID yang sudah ada di DB utama untuk perbandingan cepat
        main_cursor.execute("SELECT id FROM transaksi")
        existing_trx_ids = {row[0] for row in main_cursor.fetchall()}
        
        main_cursor.execute("SELECT nis FROM siswa")
        existing_siswa_nis = {row[0] for row in main_cursor.fetchall()}

        # 3. Ambil semua data relevan dari DB sumber
        source_siswa = source_cursor.execute("SELECT * FROM siswa").fetchall()
        source_transaksi = source_cursor.execute("SELECT * FROM transaksi").fetchall()
        source_detail = source_cursor.execute("SELECT * FROM detail_transaksi").fetchall()

        # Mulai transaksi di DB utama
        main_cursor.execute("BEGIN TRANSACTION")

        # 4. Proses Siswa: Tambahkan siswa jika belum ada di DB utama
        for siswa in source_siswa:
            nis = siswa[0] # Asumsi NIS adalah kolom pertama
            if nis not in existing_siswa_nis:
                # Kolom harus sesuai dengan tabel siswa Anda
                main_cursor.execute("INSERT INTO siswa (nis, nik_siswa, nisn, nama_lengkap, jenis_kelamin, no_wa_ortu, id_kelas, status) VALUES (?,?,?,?,?,?,?,?)", siswa)
                existing_siswa_nis.add(nis) # Tambahkan ke set agar tidak dicek lagi

        # 5. Proses Transaksi: Tambahkan hanya transaksi yang belum ada
        for trx in source_transaksi:
            trx_id = trx[0] # Asumsi ID adalah kolom pertama
            
            if trx_id in existing_trx_ids:
                stats['skipped'] += 1
                continue # Lanjut ke transaksi berikutnya

            # Cek apakah siswa untuk transaksi ini ada di DB utama
            nis_siswa = trx[2] # Asumsi nis_siswa adalah kolom ketiga
            if nis_siswa not in existing_siswa_nis:
                stats['errors'] += 1
                continue # Siswa tidak ditemukan, lewati transaksi

            # Jika semua aman, masukkan transaksi baru
            # Kolom harus sesuai dengan tabel transaksi Anda
            main_cursor.execute("INSERT INTO transaksi (id, tanggal, nis_siswa, total_bayar, petugas) VALUES (?,?,?,?,?)", trx)
            
            # Cari dan masukkan detail transaksinya
            details_for_this_trx = [d for d in source_detail if d[1] == trx_id]
            for detail in details_for_this_trx:
                # Kolom harus sesuai dengan tabel detail_transaksi Anda
                main_cursor.execute("INSERT INTO detail_transaksi (id, id_transaksi, id_tagihan, jumlah_bayar) VALUES (?,?,?,?)", detail)

            stats['added'] += 1

        # Jika semua loop berhasil, simpan perubahan
        main_conn.commit()

    except sqlite3.Error as e:
        # Jika terjadi error apapun selama proses, batalkan semua perubahan
        main_conn.rollback()
        print(f"Merge Gagal: {e}")
        # Kita bisa mengembalikan error spesifik jika perlu
        raise e 
        
    finally:
        # Tutup koneksi ke DB sumber
        source_conn.close()

    return stats

def add_default_user(conn):
    """
    Menambahkan user default 'admin' ke database.
    Fungsi ini dipanggil setelah database direset.
    """
    try:
        # Gunakan fungsi tambah_user yang sudah ada
        # dengan kredensial default: admin/admin
        tambah_user(conn, "admin", "admin", "admin")
        print("Default user 'admin' berhasil ditambahkan.")
        return True
    except Exception as e:
        print(f"Gagal menambahkan default user: {e}")
        return False

def get_laporan_kas_umum(conn, tanggal_mulai, tanggal_sampai, angkatan=None, id_pos=None, kelas_id=None, search_term=None):
    """Mengambil data transaksi dengan filter lengkap untuk laporan kas umum,
    termasuk NIS Siswa, Nama Siswa, Angkatan, dan Kelas.
    """
    cursor = conn.cursor()
    
    params = [tanggal_mulai, tanggal_sampai]
    
    query = """
    SELECT
        t.id,                  -- No. Bukti
        t.tanggal,             -- Tanggal
        s.nis as nis_siswa,    -- NIS Siswa
        s.nama_lengkap as nama_siswa, -- Nama Siswa
        k.angkatan,            -- Angkatan
        k.nama_kelas,          -- Kelas
        p.nama_pos as jenis_pos,
        'Pembayaran ' || p.nama_pos || ' oleh ' || s.nama_lengkap AS uraian,
        t.total_bayar AS pemasukan
    FROM transaksi t
    JOIN siswa s ON t.nis_siswa = s.nis
    JOIN kelas k ON s.id_kelas = k.id
    JOIN (
        SELECT dt.id_transaksi, MIN(tgh.id_pos) as id_pos
        FROM detail_transaksi dt
        JOIN tagihan tgh ON dt.id_tagihan = tgh.id
        GROUP BY dt.id_transaksi
    ) AS detail ON t.id = detail.id_transaksi
    JOIN pos_pembayaran p ON detail.id_pos = p.id
    WHERE DATE(t.tanggal) BETWEEN ? AND ?
    """
    
    if angkatan:
        query += " AND k.angkatan = ?"
        params.append(angkatan)
    
    if id_pos:
        query += " AND p.id = ?"
        params.append(id_pos)
    
    if kelas_id:
        query += " AND s.id_kelas = ?"
        params.append(kelas_id)
        
    if search_term:
        query += " AND (s.nama_lengkap LIKE ? OR s.nis LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
        
    query += " ORDER BY t.tanggal"
    
    cursor.execute(query, tuple(params))
    return cursor.fetchall()


def get_rekap_saldo_per_pos(conn):
    """Menghitung total pemasukan untuk setiap jenis POS pembayaran."""
    cursor = conn.cursor()
    query = """
        SELECT
            p.nama_pos,
            SUM(dt.jumlah_bayar) as total_diterima
        FROM detail_transaksi dt
        JOIN tagihan t ON dt.id_tagihan = t.id
        JOIN pos_pembayaran p ON t.id_pos = p.id
        GROUP BY p.nama_pos
        ORDER BY p.id
    """
    cursor.execute(query)
    return cursor.fetchall()

# --- Fungsi-fungsi untuk Dasbor ---

def get_total_siswa_aktif(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(nis) FROM siswa WHERE status = 'Aktif'")
    result = cursor.fetchone()
    return result[0] if result else 0

def get_total_tunggakan(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(sisa_tagihan) FROM tagihan WHERE status = 'Belum Lunas'")
    result = cursor.fetchone()
    return result[0] if result and result[0] is not None else 0

def get_pemasukan_hari_ini(conn):
    today = datetime.now().strftime("%Y-%m-%d")
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(total_bayar) FROM transaksi WHERE DATE(tanggal) = ?", (today,))
    result = cursor.fetchone()
    return result[0] if result and result[0] is not None else 0


# --- FUNGSI-FUNGSI BARU UNTUK DASHBOARD INTERAKTIF ---
# Tambahkan/Ganti kode ini di akhir file db_functions.py Anda

def get_kpi_data(conn, start_date, end_date, angkatan=None, kelas_id=None):
    """Mengambil data KPI utama dengan filter lengkap."""
    cursor = conn.cursor()
    
    # Base queries
    pendapatan_query = "SELECT SUM(total_bayar) FROM transaksi WHERE DATE(tanggal) BETWEEN ? AND ?"
    tunggakan_query = "SELECT SUM(sisa_tagihan) FROM tagihan WHERE status = 'Belum Lunas'"
    siswa_query = "SELECT COUNT(nis) FROM siswa WHERE status = 'Aktif'"
    
    # Params
    pendapatan_params = [start_date, end_date]
    tunggakan_params = []
    siswa_params = []

    # Apply filters dynamically
    if kelas_id:
        pendapatan_query += " AND nis_siswa IN (SELECT nis FROM siswa WHERE id_kelas = ?)"
        pendapatan_params.append(kelas_id)
        tunggakan_query += " AND nis_siswa IN (SELECT nis FROM siswa WHERE id_kelas = ?)"
        tunggakan_params.append(kelas_id)
        siswa_query += " AND id_kelas = ?"
        siswa_params.append(kelas_id)
    elif angkatan:
        pendapatan_query += " AND nis_siswa IN (SELECT nis FROM siswa WHERE id_kelas IN (SELECT id FROM kelas WHERE angkatan = ?))"
        pendapatan_params.append(angkatan)
        tunggakan_query += " AND nis_siswa IN (SELECT nis FROM siswa WHERE id_kelas IN (SELECT id FROM kelas WHERE angkatan = ?))"
        tunggakan_params.append(angkatan)
        siswa_query += " AND id_kelas IN (SELECT id FROM kelas WHERE angkatan = ?)"
        siswa_params.append(angkatan)

    # Execute queries
    cursor.execute(pendapatan_query, tuple(pendapatan_params))
    total_pendapatan = cursor.fetchone()[0] or 0
    
    cursor.execute(tunggakan_query, tuple(tunggakan_params))
    total_tunggakan = cursor.fetchone()[0] or 0

    cursor.execute(siswa_query, tuple(siswa_params))
    total_siswa_aktif = cursor.fetchone()[0] or 0

    return {
        "total_pendapatan": total_pendapatan,
        "total_tunggakan": total_tunggakan,
        "total_siswa_aktif": total_siswa_aktif,
    }

def get_revenue_trend(conn, start_date, end_date, angkatan=None, kelas_id=None):
    """Mengambil tren pendapatan harian atau bulanan dengan filter lengkap."""
    # Menentukan agregasi berdasarkan rentang tanggal
    day_diff = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days
    if day_diff > 60:
        date_format = "SUBSTR(tanggal, 1, 7)" # Agregasi per bulan (YYYY-MM)
    else:
        date_format = "DATE(tanggal)" # Agregasi per hari

    query = f"""
        SELECT {date_format} as periode, SUM(t.total_bayar) as pendapatan
        FROM transaksi t
        LEFT JOIN siswa s ON t.nis_siswa = s.nis
        LEFT JOIN kelas k ON s.id_kelas = k.id
        WHERE DATE(t.tanggal) BETWEEN ? AND ?
    """
    params = [start_date, end_date]

    if kelas_id:
        query += " AND s.id_kelas = ?"
        params.append(kelas_id)
    elif angkatan:
        query += " AND k.angkatan = ?"
        params.append(angkatan)
        
    query += " GROUP BY periode ORDER BY periode ASC"
    
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    return cursor.fetchall()

def get_revenue_by_pos(conn, start_date, end_date, angkatan=None, kelas_id=None):
    """Mengambil total pendapatan per Jenis POS dengan filter lengkap."""
    query = """
        SELECT p.nama_pos, SUM(dt.jumlah_bayar) as pendapatan
        FROM detail_transaksi dt
        JOIN transaksi t ON dt.id_transaksi = t.id
        JOIN tagihan tag ON dt.id_tagihan = tag.id
        JOIN pos_pembayaran p ON tag.id_pos = p.id
        LEFT JOIN siswa s ON t.nis_siswa = s.nis
        LEFT JOIN kelas k ON s.id_kelas = k.id
        WHERE DATE(t.tanggal) BETWEEN ? AND ?
    """
    params = [start_date, end_date]

    if kelas_id:
        query += " AND s.id_kelas = ?"
        params.append(kelas_id)
    elif angkatan:
        query += " AND k.angkatan = ?"
        params.append(angkatan)

    query += " GROUP BY p.nama_pos ORDER BY pendapatan DESC"
    
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    return cursor.fetchall()