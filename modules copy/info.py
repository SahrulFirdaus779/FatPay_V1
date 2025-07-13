import streamlit as st

def render():
    st.title("ℹ️ Informasi Aplikasi")
    
    if st.button("⬅️ Kembali ke Menu Utama"):
        st.session_state.page = 'home'
        st.rerun()
    st.markdown("---")

    # Informasi Tentang Aplikasi
    st.subheader("Tentang FatPay")
    st.write(
        """
        **FatPay** adalah aplikasi pembayaran sekolah digital yang dirancang khusus untuk 
        memudahkan manajemen keuangan di **Pondok Pesantren Fathan Mubina**.
        """
    )
    st.write("**Versi:** 1.0.0")
    st.write("**Pengembang:** Dibuat dengan bantuan Gemini")
    
    st.markdown("---")

    # Petunjuk Singkat Penggunaan
    st.subheader("Petunjuk Singkat")
    st.write(
        """
        Berikut adalah fungsi dari masing-masing modul utama:
        - **Data Siswa**: Digunakan untuk mengelola semua data master siswa dan kelas, termasuk proses kenaikan, pindah kelas, hingga kelulusan.
        - **Pembayaran**: Modul utama untuk proses pembayaran. Di sini Anda bisa membuat tagihan, melakukan transaksi pembayaran, hingga melihat riwayat transaksi.
        - **Buku KAS**: Berisi laporan-laporan keuangan seperti Buku Kas Umum (rincian pemasukan) dan Rekap Saldo per jenis pembayaran.
        - **Admin**: Halaman untuk mengelola pengguna aplikasi, mengubah password, serta melakukan backup dan restore database.
        - **Info**: Halaman yang sedang Anda lihat saat ini.
        """
    )
    
    st.markdown("---")

    # Kontak
    st.subheader("Bantuan atau Kontak")
    st.info("Jika mengalami kendala teknis, silakan hubungi administrator yang bertanggung jawab.")