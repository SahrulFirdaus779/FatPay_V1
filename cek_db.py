# cek_db.py
import sqlite3
import os

# Pastikan nama file ini sesuai dengan file database utama Anda
db_file = 'fatpay.db'

if not os.path.exists(db_file):
    print(f"Error: File '{db_file}' tidak ditemukan di direktori ini.")
else:
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        # Perintah untuk mengambil semua nama tabel
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()

        print(f"✅ Daftar tabel yang ditemukan di '{db_file}':")
        for table in tables:
            print(f"- {table[0]}")
    except Exception as e:
        print(f"Gagal membaca database: {e}")