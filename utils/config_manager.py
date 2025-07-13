import json
import os

CONFIG_FILE = "config.json"

def load_config():
    """Membaca file konfigurasi dan mengembalikannya sebagai dictionary."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        # Mengembalikan nilai default jika file tidak ada
        return {
            "nama_lembaga": "MADRASAH FATHAN MUBINA",
            "alamat": "Jl. Veteran III Raya Tapos, Bogor, No.23A", 
            "telp": "0821-1202-1127",
            "website": "https://fathanmubina.com/",
            "logo_path": "logo.png"
        }

def save_config(config_data):
    """Menyimpan dictionary konfigurasi ke dalam file JSON."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=4)