import streamlit as st
import os
import base64
from PIL import Image
from datetime import timedelta

# --- Impor modul-modul aplikasi Anda ---
# Pastikan modul-modul ini juga disesuaikan untuk menerima 'conn' jika diperlukan
from menu_items import menu_items
from utils import config_manager as cfg
from utils import db_functions as db
from modules import data_siswa, pembayaran, buku_kas, laporan, admin, info

# --- FUNGSI KONEKSI DATABASE (SUDAH DIPERBAIKI) ---

# Decorator @st.cache_resource DIHAPUS untuk menghindari error thread pada SQLite
def get_db_connection():
    """Membuat koneksi database baru."""
    return db.create_connection()

# --- FUNGSI CACHING LAINNYA (TIDAK BERUBAH) ---

@st.cache_data
def load_dashboard_siswa_tunggakan(_conn):
    """
    Mengambil data total siswa aktif dan total tunggakan.
    Data ini tidak terlalu sering berubah.
    Parameter _conn ditambahkan agar Streamlit tahu fungsi ini bergantung pada koneksi.
    """
    total_siswa = db.get_total_siswa_aktif(_conn)
    total_tunggakan = db.get_total_tunggakan(_conn)
    return total_siswa, total_tunggakan

@st.cache_data(ttl=timedelta(minutes=5))
def load_pemasukan_hari_ini(_conn):
    """
    Mengambil data pemasukan hari ini.
    Cache akan kadaluwarsa setiap 5 menit untuk mendapatkan data yang cukup baru.
    """
    return db.get_pemasukan_hari_ini(_conn)


# --- Fungsi Bantuan ---
def load_image(path):
    """Membuka file gambar dari path yang diberikan."""
    try:
        return Image.open(path)
    except FileNotFoundError:
        st.warning(f"File gambar tidak ditemukan di: {path}")
        return None

# Konfigurasi halaman harus menjadi panggilan pertama di Streamlit
logo_image = load_image("logo.png")
st.set_page_config(
    page_title="FatPay",
    page_icon=logo_image,
    layout="wide"
)

# --- Render fungsi (tidak ada perubahan) ---
def render_svg(svg_path):
    """Merender file SVG sebagai gambar base64 untuk menu utama."""
    if not os.path.exists(svg_path):
        st.warning(f"Ikon SVG tidak ditemukan: {svg_path}")
        return f'<img src="" alt="Icon not found">'
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_content = f.read()
    b64 = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
    return f'<div class="menu-icon-container"><img src="data:image/svg+xml;base64,{b64}" alt="{os.path.basename(svg_path)}"/></div>'

def render_metric_icon_svg(svg_path):
    """Merender file SVG sebagai gambar base64 untuk kartu metrik."""
    if not os.path.exists(svg_path):
        return ''
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_content = f.read()
    b64 = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
    return f'<img src="data:image/svg+xml;base64,{b64}" alt="{os.path.basename(svg_path)}">'

def navigate_to(page_name):
    """Mengatur state halaman dan menjalankan ulang aplikasi untuk navigasi."""
    st.session_state.page = page_name
    st.rerun()

# --- FUNGSI LOGIN (DIPERBAIKI) ---
# Fungsi ini sekarang menerima 'conn' sebagai argumen
def show_login_page(conn):
    """Menampilkan form login dengan gaya baru."""
    st.markdown("""
    <style>
        /* ... CSS Anda tidak berubah ... */
        [data-testid="stAppViewContainer"] { background-color: #FFF7E8 !important; }
        [data-testid="stForm"] { 
            background-color: white; 
            padding: 2.5rem; 
            border: 1px solid #dddddd; 
            border-radius: 16px; 
            box-shadow: 0 8px 24px rgba(0,0,0,0.1); 
            margin: 3rem auto; 
            max-width: 480px; 
        }
        .login-header { text-align: center; margin-bottom: 2rem; margin-top: 1rem; }
        .login-header h1 { font-size: 2.2rem; font-weight: bold; color: #1e1e1e; }
        .login-header p { color: #555555; font-size: 1.1rem; }
        header, footer { visibility: hidden; }
        [data-testid="stForm"] .stButton > button { 
            background-color: #007BFF !important; 
            color: white !important; 
            height: 3rem; 
            font-weight: bold; 
            border-radius: 8px !important; 
            border: none !important; 
        }
    </style>
    """, unsafe_allow_html=True)
    with st.form("login_form"):
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            if logo_image:
                st.image(logo_image)
        st.markdown('<div class="login-header"><h1>Selamat Datang di FatPay</h1><p>Sistem Informasi Pembayaran Sekolah</p></div>', unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="Masukkan username Anda", label_visibility="collapsed")
        password = st.text_input("Password", type="password", placeholder="Masukkan password Anda", label_visibility="collapsed")
        
        if st.form_submit_button("Login", use_container_width=True, type="primary"):
            # Menggunakan koneksi 'conn' yang dikirim sebagai argumen
            # Tidak perlu memanggil get_db_connection() lagi di sini
            role = db.check_login(conn, username, password)
            if role:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = role
                # Hapus cache data setelah login untuk memastikan dasbor menampilkan data terbaru
                st.cache_data.clear()
                navigate_to('home')
            else:
                st.error("Username atau Password salah!")

# --- Inisialisasi Session State ---
def init_session_state():
    """Menginisialisasi session state untuk status login dan halaman."""
    defaults = {'logged_in': False, 'page': 'home', 'username': '', 'role': ''}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Panggil inisialisasi dan setup database di awal
init_session_state()
db.setup_database()

# --- Dasbor Utama (DIPERBAIKI) ---
# Fungsi ini sekarang menerima 'conn' sebagai argumen
def show_main_dashboard(conn):
    st.markdown("""
    <style>
        .main, [data-testid="stAppViewContainer"] { background-color: #FFF7E8; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .header-title { margin-top: 1rem; color: #333; }
        .header-welcome { margin-top: -1rem; color: #555; }
        .metric-card { background-color: #FFF7E8; padding: 1rem 1.5rem; border-radius: 12px; border: 1px solid #E0E0E0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); display: flex; align-items: center; gap: 1.5rem; height: 100%; }
        .metric-card-icon { background-color: #FFF7E8; padding: 0.8rem; border-radius: 50%; display: flex; align-items: center; justify-content: center; width: 64px; height: 64px; box-sizing: border-box; }
        .metric-card-icon img { max-width: 30px; max-height: 30px; }
        .metric-card-label { font-size: 1rem; color: #555555; margin-bottom: 0.1rem; }
        .metric-card-value { font-size: 1.5rem; font-weight: 600; color: #1a1a1a; }
        .menu-title { font-size: 1.1rem; font-weight: 600; color: #1a1a1a; margin: 0.5rem 0; text-align: center; }
        .menu-icon-container { height: 70px; margin-bottom: 0.5rem; text-align: center; display: flex; align-items: center; justify-content: center; }
        .menu-icon-container img { max-height: 100%; max-width: 100%; }
        .stButton > button { 
            font-weight: bold; border-radius: 8px !important; border: none !important; 
            width: 100% !important; padding: 0.75rem 0 !important; font-size: 1rem !important;
            background-color: #007BFF !important; color: white !important; 
        }
        .stButton > button:hover { background-color: #0056b3 !important; }
    </style>
    """, unsafe_allow_html=True)

    # --- Header dengan Tombol Logout ---
    config = cfg.load_config()
    col1, col2, col3 = st.columns([1, 4.5, 1])
    with col1:
        if logo_image:
            st.image(logo_image, width=120)
    with col2:
        st.markdown(f'<h1 class="header-title">{config.get("nama_lembaga", "FatPay")}</h1>', unsafe_allow_html=True)
        st.markdown(f'<p class="header-welcome">Selamat Datang, <strong>{st.session_state.username}</strong>!</p>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div style="height: 2.5rem;"></div>', unsafe_allow_html=True)
        if st.button("Logout", key="logout_button_main", help="Keluar dari aplikasi", use_container_width=True, type="primary"):
            st.session_state.show_logout_confirmation = True
    
    # --- Dialog Konfirmasi Logout (Versi Kompatibel) ---
    if st.session_state.get("show_logout_confirmation", False):
        st.warning("**Konfirmasi Logout**: Anda yakin ingin keluar dari aplikasi?")
        
        # Menggunakan kolom untuk menata tombol agar lebih rapi
        col_confirm, col_cancel, _ = st.columns([1, 1, 5]) 
        
        with col_confirm:
            if st.button("✅ Ya, Logout", use_container_width=True, type="primary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        with col_cancel:
            if st.button("❌ Batal", use_container_width=True):
                st.session_state.show_logout_confirmation = False
                st.rerun()

    # --- Ringkasan Sistem (MENGGUNAKAN FUNGSI CACHE) ---
    st.markdown("---")
    st.subheader("Ringkasan Sistem")

    # Menggunakan koneksi 'conn' yang dikirim sebagai argumen
    # Tidak perlu memanggil get_db_connection() lagi di sini
    
    # Panggil fungsi loader yang sudah di-cache
    total_siswa, total_tunggakan = load_dashboard_siswa_tunggakan(conn)
    pemasukan_hari_ini = load_pemasukan_hari_ini(conn)
    
    icon_siswa_html = render_metric_icon_svg("assets/siswa.svg")
    icon_tunggakan_html = render_metric_icon_svg("assets/tunggakan.svg")
    icon_pemasukan_html = render_metric_icon_svg("assets/pemasukan.svg")
    
    col1, col2, col3 = st.columns(3, gap="large")
    col1.markdown(f'<div class="metric-card"><div class="metric-card-icon">{icon_siswa_html}</div><div><div class="metric-card-label">Siswa Aktif</div><div class="metric-card-value">{total_siswa} Siswa</div></div></div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="metric-card"><div class="metric-card-icon">{icon_tunggakan_html}</div><div><div class="metric-card-label">Total Tunggakan</div><div class="metric-card-value">Rp {total_tunggakan:,.0f}</div></div></div>', unsafe_allow_html=True)
    col3.markdown(f'<div class="metric-card"><div class="metric-card-icon">{icon_pemasukan_html}</div><div><div class="metric-card-label">Pemasukan Hari Ini</div><div class="metric-card-value">Rp {pemasukan_hari_ini:,.0f}</div></div></div>', unsafe_allow_html=True)
    
    # --- Menu Navigasi ---
    st.markdown("---")
    st.subheader("Menu Utama")
    
    num_cols = 3 
    accessible_menu = [item for item in menu_items if st.session_state.get('role') in item.get('roles', [])]
    
    for i in range(0, len(accessible_menu), num_cols):
        cols = st.columns(num_cols, gap="large")
        row_items = accessible_menu[i:i+num_cols]
        for j, item in enumerate(row_items):
            with cols[j]:
                with st.container(border=True):
                    st.markdown(render_svg(item["image"]), unsafe_allow_html=True)
                    st.markdown(f'<h3 class="menu-title">{item["title"]}</h3>', unsafe_allow_html=True)
                    if st.button("Masuk ke Modul", key=item["key"], use_container_width=True):
                        navigate_to(item["target"])

# --- Router Utama Aplikasi (DIPERBAIKI) ---
def main():
    """Fungsi utama yang mengatur halaman mana yang akan ditampilkan."""
    # PERBAIKAN: Buat koneksi sekali di awal setiap eksekusi skrip
    conn = get_db_connection()

    if not st.session_state.get('logged_in'):
        # PERBAIKAN: Kirim koneksi ke halaman login
        show_login_page(conn)
    else:
        page = st.session_state.get('page', 'home')
        if page == 'home':
            # PERBAIKAN: Kirim koneksi ke dasbor utama
            show_main_dashboard(conn)
        else:
            pages = {
                'data_siswa': data_siswa, 'pembayaran': pembayaran, 'buku_kas': buku_kas,
                'laporan': laporan, 'admin': admin, 'info': info
            }
            module_to_render = pages.get(page)
            if module_to_render and hasattr(module_to_render, 'render'):
                # PENTING: Anda mungkin perlu menyesuaikan file modul Anda (misal: data_siswa.py)
                # agar fungsi render() di dalamnya juga menerima 'conn' sebagai argumen.
                # Contoh pemanggilan yang ideal: module_to_render.render(conn)
                module_to_render.render() # Sesuaikan ini jika modul Anda butuh koneksi
            else:
                st.error(f"Halaman '{page}' tidak ditemukan atau modul belum diimpor.")
                st.button("Kembali ke Dasbor", on_click=navigate_to, args=('home',))

if __name__ == "__main__":
    main()