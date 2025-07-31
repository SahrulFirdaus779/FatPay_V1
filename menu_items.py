# utils/menu_items.py

"""
Konfigurasi untuk item-item menu utama di dasbor.
Setiap item adalah sebuah dictionary yang berisi:
- title: Teks yang akan ditampilkan sebagai judul menu.
- image: Path ke file ikon SVG untuk menu tersebut.
- key: Kunci unik untuk widget tombol Streamlit.
- target: Nama halaman/modul yang akan dituju saat menu diklik.
- roles: Daftar peran (role) yang diizinkan untuk melihat menu ini.
"""

menu_items = [
    {
        "title": "Data Siswa",
        "image": "assets/menu/data_siswa.svg",
        "key": "modul_data_siswa",
        "target": "data_siswa",
        "roles": ["admin", "operator"]
    },
    {
        "title": "Pembayaran",
        "image": "assets/menu/pembayaran.svg",
        "key": "modul_pembayaran",
        "target": "pembayaran",
        "roles": ["admin", "operator"]
    },
    {
        "title": "Buku Kas",
        "image": "assets/menu/buku_kas.svg",
        "key": "modul_buku_kas",
        "target": "buku_kas",
        "roles": ["admin", "operator"]
    },
    {
        "title": "Laporan",
        "image": "assets/menu/laporan.svg",
        "key": "modul_laporan",
        "target": "laporan",
        "roles": ["admin", "operator"]
    },
    {
        "title": "Administrasi",
        "image": "assets/menu/admin.svg",
        "key": "modul_admin",
        "target": "admin",
        "roles": ["admin", "operator"] # Nantinya bisa diubah menjadi ["admin"] saja
    },
    {
        "title": "Info Aplikasi",
        "image": "assets/menu/info.svg",
        "key": "modul_info",
        "target": "info",
        "roles": ["admin", "operator"]
    }
]