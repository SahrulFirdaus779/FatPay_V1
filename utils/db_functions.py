# utils/db_functions.py (Versi Final yang Benar)

import sqlite3
import hashlib
from datetime import datetime

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect("fatpay.db")
    except sqlite3.Error as e:
        print(e)
    return conn

def create_tables(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kelas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama_kelas TEXT NOT NULL,
                tahun_ajaran TEXT NOT NULL
            );
        """)
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
                FOREIGN KEY (id_kelas) REFERENCES kelas (id)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pos_pembayaran (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama_pos TEXT NOT NULL,
                tipe TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tagihan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nis_siswa TEXT NOT NULL,
                id_pos INTEGER NOT NULL,
                bulan TEXT,
                nominal_tagihan REAL NOT NULL,
                sisa_tagihan REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'Belum Lunas',
                FOREIGN KEY (nis_siswa) REFERENCES siswa (nis),
                FOREIGN KEY (id_pos) REFERENCES pos_pembayaran (id)
            );
        """)
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detail_transaksi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_transaksi INTEGER NOT NULL,
                id_tagihan INTEGER NOT NULL,
                jumlah_bayar REAL NOT NULL,
                FOREIGN KEY (id_transaksi) REFERENCES transaksi (id),
                FOREIGN KEY (id_tagihan) REFERENCES tagihan (id)
            );
        """)
        print("Pemeriksaan dan pembuatan tabel berhasil.")
    except sqlite3.Error as e:
        print(e)

def setup_database():
    conn = create_connection()
    if conn is not None:
        create_tables(conn)
        conn.close()

# --- Fungsi-fungsi untuk User ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def tambah_user(conn, username, password, role):
    hashed_pw = hash_password(password)
    sql = ''' INSERT INTO users(username,password,role) VALUES(?,?,?) '''
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (username, hashed_pw, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def check_login(conn, username, password):
    hashed_pw = hash_password(password)
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, hashed_pw))
    result = cursor.fetchone()
    return result[0] if result else None

def get_all_users(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users")
    return cursor.fetchall()

def update_user_password(conn, username, new_password):
    """Mengubah password seorang user oleh admin."""
    hashed_pw = hash_password(new_password)
    sql = ''' UPDATE users SET password = ? WHERE username = ? '''
    cursor = conn.cursor()
    cursor.execute(sql, (hashed_pw, username))
    conn.commit()

def hapus_user(conn, username):
    """Menghapus seorang user."""
    # Pastikan user 'admin' tidak bisa dihapus
    if username == 'admin':
        return False
    sql = 'DELETE FROM users WHERE username = ?'
    cursor = conn.cursor()
    cursor.execute(sql, (username,))
    conn.commit()
    return True

# --- Fungsi-fungsi untuk Kelas ---
def tambah_kelas(conn, nama_kelas, tahun_ajaran):
    sql = ''' INSERT INTO kelas(nama_kelas,tahun_ajaran) VALUES(?,?) '''
    cursor = conn.cursor()
    cursor.execute(sql, (nama_kelas, tahun_ajaran))
    conn.commit()

def get_semua_kelas(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, nama_kelas, tahun_ajaran FROM kelas")
    return cursor.fetchall()

def update_kelas(conn, id_kelas, nama_baru, tahun_ajaran_baru):
    sql = ''' UPDATE kelas SET nama_kelas = ?, tahun_ajaran = ? WHERE id = ? '''
    cursor = conn.cursor()
    cursor.execute(sql, (nama_baru, tahun_ajaran_baru, id_kelas))
    conn.commit()

def hapus_kelas(conn, id_kelas):
    sql = 'DELETE FROM kelas WHERE id = ?'
    cursor = conn.cursor()
    cursor.execute(sql, (id_kelas,))
    conn.commit()

# --- Fungsi-fungsi untuk Siswa ---
def tambah_siswa(conn, nis, nik, nisn, nama, jenis_kelamin, no_wa, id_kelas):
    sql = ''' INSERT INTO siswa(nis, nik_siswa, nisn, nama_lengkap, jenis_kelamin, no_wa_ortu, id_kelas)
              VALUES(?,?,?,?,?,?,?) '''
    cursor = conn.cursor()
    cursor.execute(sql, (nis, nik, nisn, nama, jenis_kelamin, no_wa, id_kelas))
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

def get_filtered_siswa_detailed(conn, kelas_id=None, search_term=None):
    """
    Mengambil data siswa dengan filter berdasarkan kelas dan/atau nama/NIS.
    """
    cursor = conn.cursor()
    
    # Query dasar
    query = """
        SELECT s.nis, s.nik_siswa, s.nisn, s.nama_lengkap, s.jenis_kelamin, s.no_wa_ortu, k.nama_kelas, s.status
        FROM siswa s
        LEFT JOIN kelas k ON s.id_kelas = k.id
    """
    
    conditions = []
    params = []
    
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

def update_kelas_siswa(conn, nis, id_kelas_baru):
    sql = ''' UPDATE siswa SET id_kelas = ? WHERE nis = ? '''
    cursor = conn.cursor()
    cursor.execute(sql, (id_kelas_baru, nis))
    conn.commit()

def update_status_siswa(conn, nis, status_baru):
    sql = ''' UPDATE siswa SET status = ? WHERE nis = ? '''
    cursor = conn.cursor()
    cursor.execute(sql, (status_baru, nis))
    conn.commit()

# --- Fungsi-fungsi untuk POS Pembayaran ---
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

# --- Fungsi-fungsi untuk Tagihan ---
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
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.nama_lengkap, s.no_wa_ortu, p.nama_pos, t.sisa_tagihan
        FROM tagihan t
        JOIN siswa s ON t.nis_siswa = s.nis
        JOIN pos_pembayaran p ON t.id_pos = p.id
        WHERE t.id_pos = ? AND t.status = 'Belum Lunas' AND s.no_wa_ortu IS NOT NULL
    """, (id_pos,))
    return cursor.fetchall()

# --- Fungsi-fungsi untuk Transaksi ---
def proses_pembayaran(conn, nis_siswa, petugas, list_pembayaran):
    tanggal_transaksi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_bayar = sum(item[1] for item in list_pembayaran)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transaksi (tanggal, nis_siswa, total_bayar, petugas) VALUES (?, ?, ?, ?)", (tanggal_transaksi, nis_siswa, total_bayar, petugas))
    id_transaksi_baru = cursor.lastrowid
    for id_tagihan, jumlah_bayar in list_pembayaran:
        cursor.execute("INSERT INTO detail_transaksi (id_transaksi, id_tagihan, jumlah_bayar) VALUES (?, ?, ?)", (id_transaksi_baru, id_tagihan, jumlah_bayar))
        cursor.execute("UPDATE tagihan SET sisa_tagihan = sisa_tagihan - ? WHERE id = ?", (jumlah_bayar, id_tagihan))
        cursor.execute("SELECT sisa_tagihan FROM tagihan WHERE id = ?", (id_tagihan,))
        sisa_tagihan_terbaru = cursor.fetchone()[0]
        if sisa_tagihan_terbaru <= 0:
            cursor.execute("UPDATE tagihan SET status = 'Lunas' WHERE id = ?", (id_tagihan,))
    conn.commit()
    return id_transaksi_baru

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
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.nama_pos, t.bulan, dt.jumlah_bayar
        FROM detail_transaksi dt
        JOIN tagihan t ON dt.id_tagihan = t.id
        JOIN pos_pembayaran p ON t.id_pos = p.id
        WHERE dt.id_transaksi = ?
    """, (id_transaksi,))
    return cursor.fetchall()

def get_laporan_kas_umum(conn, tanggal_mulai, tanggal_sampai, id_pos=None, kelas_id=None, search_term=None):
    """Mengambil data transaksi dengan filter lengkap."""
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
    JOIN (
        SELECT dt.id_transaksi, MIN(tgh.id_pos) as id_pos
        FROM detail_transaksi dt
        JOIN tagihan tgh ON dt.id_tagihan = tgh.id
        GROUP BY dt.id_transaksi
    ) AS detail ON t.id = detail.id_transaksi
    JOIN pos_pembayaran p ON detail.id_pos = p.id
    WHERE DATE(t.tanggal) BETWEEN ? AND ?
    """
    
    if id_pos:
        query += " AND p.id = ?"
        params.append(id_pos)
    
    # (BARU) Menambahkan filter kelas dan nama/nis
    if kelas_id:
        query += " AND s.id_kelas = ?"
        params.append(kelas_id)
        
    if search_term:
        query += " AND (s.nama_lengkap LIKE ? OR s.nis LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
        
    query += " ORDER BY t.tanggal"
    
    cursor.execute(query, tuple(params))
    return cursor.fetchall()

# TAMBAHKAN fungsi baru ini di akhir file:
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

def get_laporan_harian(conn, tanggal):
    """Mengambil semua transaksi pembayaran pada tanggal tertentu."""
    cursor = conn.cursor()
    query = """
    SELECT
        t.id,
        s.nis,
        s.nama_lengkap,
        p.nama_pos,
        dt.jumlah_bayar
    FROM transaksi t
    JOIN siswa s ON t.nis_siswa = s.nis
    JOIN detail_transaksi dt ON t.id = dt.id_transaksi
    JOIN tagihan tag ON dt.id_tagihan = tag.id
    JOIN pos_pembayaran p ON tag.id_pos = p.id
    WHERE DATE(t.tanggal) = ?
    ORDER BY t.id
    """
    cursor.execute(query, (tanggal,))
    return cursor.fetchall()

def get_semua_tunggakan(conn, kelas_id=None, search_term=None):
    """Mengambil semua data tunggakan dengan filter kelas dan nama/nis."""
    cursor = conn.cursor()
    
    query = """
        SELECT
            s.nis,
            s.nama_lengkap,
            k.nama_kelas,
            p.nama_pos,
            t.bulan,
            t.sisa_tagihan
        FROM tagihan t
        JOIN siswa s ON t.nis_siswa = s.nis
        JOIN kelas k ON s.id_kelas = k.id
        JOIN pos_pembayaran p ON t.id_pos = p.id
        WHERE t.status = 'Belum Lunas' AND t.sisa_tagihan > 0
    """
    
    params = []
    if kelas_id:
        query += " AND s.id_kelas = ?"
        params.append(kelas_id)
        
    # (BARU) Menambahkan filter pencarian nama/nis
    if search_term:
        query += " AND (s.nama_lengkap LIKE ? OR s.nis LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
        
    query += " ORDER BY k.nama_kelas, s.nama_lengkap"
    
    cursor.execute(query, tuple(params))
    return cursor.fetchall()

def get_rekap_pembayaran(conn, tanggal_mulai, tanggal_sampai, kelas_id=None, search_term=None):
    """Menghitung rekap total pemasukan per POS dengan filter lengkap."""
    cursor = conn.cursor()
    
    params = [tanggal_mulai, tanggal_sampai]
    
    query = """
    SELECT
        p.nama_pos,
        SUM(dt.jumlah_bayar) as total_diterima
    FROM detail_transaksi dt
    JOIN transaksi t ON dt.id_transaksi = t.id
    JOIN siswa s ON t.nis_siswa = s.nis
    JOIN tagihan tag ON dt.id_tagihan = tag.id
    JOIN pos_pembayaran p ON tag.id_pos = p.id
    WHERE DATE(t.tanggal) BETWEEN ? AND ?
    """
    
    if kelas_id:
        query += " AND s.id_kelas = ?"
        params.append(kelas_id)
        
    if search_term:
        query += " AND (s.nama_lengkap LIKE ? OR s.nis LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
        
    query += " GROUP BY p.nama_pos ORDER BY p.id"
    
    cursor.execute(query, tuple(params))
    return cursor.fetchall()


# --- Fungsi-fungsi untuk Dasbor ---

def get_total_siswa_aktif(conn):
    """Menghitung jumlah siswa yang statusnya 'Aktif'."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(nis) FROM siswa WHERE status = 'Aktif'")
    result = cursor.fetchone()
    return result[0] if result else 0

def get_total_tunggakan(conn):
    """Menghitung total sisa tagihan dari semua siswa."""
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(sisa_tagihan) FROM tagihan WHERE status = 'Belum Lunas'")
    result = cursor.fetchone()
    return result[0] if result and result[0] is not None else 0

def get_pemasukan_hari_ini(conn):
    """Menghitung total pembayaran yang diterima hari ini."""
    today = datetime.now().strftime("%Y-%m-%d")
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(total_bayar) FROM transaksi WHERE DATE(tanggal) = ?", (today,))
    result = cursor.fetchone()
    return result[0] if result and result[0] is not None else 0