# menu_items.py
# File ini berisi konfigurasi untuk setiap item menu di dasbor.
# Memisahkan data ini membuat kode utama lebih bersih dan mudah dikelola.

menu_items = [
    {
        "title": "Data Siswa",
        "desc": "Kelola semua data master siswa, kelas, dan status akademis mereka.",
        "image": "assets/data_siswa.svg", # Pastikan path ini benar
        "key": "btn_data_siswa",
        "target": "data_siswa"
    },
    {
        "title": "Pembayaran",
        "desc": "Proses transaksi pembayaran, buat tagihan, dan lihat riwayat pembayaran.",
        "image": "assets/pembayaran.svg", # Pastikan path ini benar
        "key": "btn_pembayaran",
        "target": "pembayaran"
    },
    {
        "title": "Buku KAS",
        "desc": "Lihat laporan kas umum dan rekapitulasi saldo per jenis pembayaran.",
        "image": "assets/buku_kas.svg", # Pastikan path ini benar
        "key": "btn_buku_kas",
        "target": "buku_kas"
    },
    {
        "title": "Laporan",
        "desc": "Cetak laporan pembayaran harian, bulanan, dan laporan tunggakan siswa.",
        "image": "assets/laporan.svg", # Pastikan path ini benar
        "key": "btn_laporan",
        "target": "laporan"
    },
    {
        "title": "Admin",
        "desc": "Atur pengguna, profil lembaga, dan lakukan pemeliharaan database.",
        "image": "assets/admin.svg", # Pastikan path ini benar
        "key": "btn_admin",
        "target": "admin"
    },
    {
        "title": "Info",
        "desc": "Lihat informasi dan panduan singkat mengenai penggunaan aplikasi FatPay.",
        "image": "assets/info.svg", # Pastikan path ini benar
        "key": "btn_info",
        "target": "info"
    },
]
