import streamlit as st
import os
import base64
from PIL import Image

# --- Impor modul-modul aplikasi Anda ---
from menu_items import menu_items
from utils import config_manager as cfg
from utils import db_functions as db
from modules import data_siswa, pembayaran, buku_kas, laporan, admin, info

# --- Fungsi Bantuan ---
def load_image(path):
    try:
        return Image.open(path)
    except FileNotFoundError:
        return None

logo_image = load_image("logo.png")
st.set_page_config(
    page_title="FatPay",
    page_icon=logo_image,
    layout="wide"
)

def render_svg(svg_path):
    if not os.path.exists(svg_path):
        return f'<img src="" alt="Icon not found">'
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_content = f.read()
    b64 = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
    # Mengembalikan div pembungkus agar style lama tetap berlaku
    return f'<div class="menu-icon-container"><img src="data:image/svg+xml;base64,{b64}" alt="{os.path.basename(svg_path)}"/></div>'


def render_metric_icon_svg(svg_path):
    if not os.path.exists(svg_path):
        return ''
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_content = f.read()
    b64 = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
    return f'<img src="data:image/svg+xml;base64,{b64}" alt="{os.path.basename(svg_path)}">'

def navigate_to(page_name):
    st.session_state.page = page_name
    st.rerun()

# --- Inisialisasi Session State ---
def init_session_state():
    defaults = {'logged_in': False, 'page': 'home', 'username': '', 'role': ''}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()
db.setup_database()

# --- Halaman Login ---
def show_login_page():
    st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] { background-color: #FFF7E8 !important; }
        [data-testid="stForm"] { background-color: white; padding: 2.5rem; border: 1px solid #dddddd; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.1); margin: 3rem auto; max-width: 480px; }
        .login-header { text-align: center; margin-bottom: 2rem; margin-top: 1rem; }
        .login-header h1 { font-size: 2.2rem; font-weight: bold; color: #1e1e1e; }
        .login-header p { color: #555555; font-size: 1.1rem; }
        header, footer { visibility: hidden; }
        .stButton > button { background-color: #007BFF !important; color: white !important; height: 3rem; font-weight: bold; border-radius: 8px !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)
    with st.form("login_form"):
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.image("logo.png")
        st.markdown('<div class="login-header"><h1>Selamat Datang di FatPay</h1><p>Sistem Informasi Pembayaran Sekolah</p></div>', unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="Masukkan username Anda", label_visibility="collapsed")
        password = st.text_input("Password", type="password", placeholder="Masukkan password Anda", label_visibility="collapsed")
        if st.form_submit_button("Login", use_container_width=True):
            conn = db.create_connection()
            try:
                role = db.check_login(conn, username, password)
                if role:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = role
                    navigate_to('home')
                else:
                    st.error("Username atau Password salah!")
            finally:
                conn.close()

# --- Dasbor Utama ---
def show_main_dashboard():
    st.markdown("""
    <style>
        .main, [data-testid="stAppViewContainer"] {
            background-color: #FFF7E8;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .metric-card {
            background-color: #FFF7E8; padding: 1rem 1.5rem; border-radius: 12px;
            border: 1px solid #E0E0E0; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            display: flex; align-items: center; gap: 1.5rem; height: 100%;
        }
        .metric-card-icon {
            background-color: #FFF7E8; padding: 0.8rem; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            width: 64px; height: 64px; box-sizing: border-box;
        }
        .metric-card-icon img { max-width: 30px; max-height: 30px; }
        .metric-card-label { font-size: 1rem; color: #555555; margin-bottom: 0.1rem; }
        .metric-card-value { font-size: 1.5rem; font-weight: 600; color: #1a1a1a; }
        .menu-title {
            font-size: 1.2rem; font-weight: 600; color: #1a1a1a;
            margin: 0.5rem 0; text-align: center;
        }
        .menu-icon-container { height: 80px; margin-bottom: 0.5rem; text-align: center; }
        .menu-icon-container img { max-height: 100%; max-width: 100%; }
        .stButton > button:not(.logout-button button) {
            background-color: #007BFF !important; color: white !important;
            font-weight: bold; border-radius: 8px !important; border: none !important;
            width: 100% !important; padding: 0.75rem 0 !important; font-size: 1rem !important;
        }
        .stButton > button:not(.logout-button button):hover { background-color: #0056b3 !important; }
        @media (max-width: 768px) { .menu-title { font-size: 1rem; } }
    </style>
    """, unsafe_allow_html=True)

    # --- Header ---
    config = cfg.load_config()
    col1, col2, col3 = st.columns([1.2, 4, 1.5])
    with col1:
        st.image("logo.png", width=120)
    with col2:
        st.markdown(f'<h1 class="header-title">{config.get("nama_lembaga", "FatPay")}</h1>', unsafe_allow_html=True)
        st.markdown(f'<p class="header-welcome">Selamat Datang, <strong>{st.session_state.username}</strong>!</p>', unsafe_allow_html=True)
    with col3:
        if st.button("Logout", key="btn_logout"):
            st.session_state.logged_in = False
            st.session_state.page = 'home'
            st.rerun()

    # --- Ringkasan Sistem ---
    st.markdown("---")
    st.subheader("Ringkasan Sistem")
    conn = db.create_connection()
    try:
        total_siswa, total_tunggakan, pemasukan_hari_ini = db.get_total_siswa_aktif(conn), db.get_total_tunggakan(conn), db.get_pemasukan_hari_ini(conn)
        icon_siswa_html, icon_tunggakan_html, icon_pemasukan_html = render_metric_icon_svg("assets/siswa.svg"), render_metric_icon_svg("assets/tunggakan.svg"), render_metric_icon_svg("assets/pemasukan.svg")
        col1, col2, col3 = st.columns(3, gap="large")
        col1.markdown(f'<div class="metric-card"><div class="metric-card-icon">{icon_siswa_html}</div><div><div class="metric-card-label">Siswa Aktif</div><div class="metric-card-value">{total_siswa} Siswa</div></div></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="metric-card"><div class="metric-card-icon">{icon_tunggakan_html}</div><div><div class="metric-card-label">Total Tunggakan</div><div class="metric-card-value">Rp {total_tunggakan:,.0f}</div></div></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="metric-card"><div class="metric-card-icon">{icon_pemasukan_html}</div><div><div class="metric-card-label">Pemasukan Hari Ini</div><div class="metric-card-value">Rp {pemasukan_hari_ini:,.0f}</div></div></div>', unsafe_allow_html=True)
    finally:
        conn.close()
    
    # --- Menu Navigasi (METODE RESMI STREAMLIT) ---
    st.markdown("---")
    st.subheader("Menu Utama")
    
    num_cols = 3 
    cols = st.columns(num_cols, gap="large")
    for index, item in enumerate(menu_items):
        with cols[index % num_cols]:
            # Menggunakan fitur bawaan st.container(border=True)
            with st.container(border=True):
                st.markdown(render_svg(item["image"]), unsafe_allow_html=True)
                st.markdown(f'<h3 class="menu-title">{item["title"]}</h3>', unsafe_allow_html=True)
                st.markdown(f'<p class="menu-desc">{item["desc"]}</p>', unsafe_allow_html=True)
                
                # Tombol Streamlit asli, aman untuk sesi login
                if st.button("Masuk ke Modul", key=item["key"], use_container_width=True):
                    navigate_to(item["target"])

# --- Router Utama Aplikasi (DIKEMBALIKAN KE SEMULA) ---
def main():
    if not st.session_state.logged_in:
        show_login_page()
    else:
        page = st.session_state.get('page', 'home')
        
        if page == 'home':
            show_main_dashboard()
        else:
            pages = {
                'data_siswa': data_siswa, 'pembayaran': pembayaran, 'buku_kas': buku_kas,
                'laporan': laporan, 'admin': admin, 'info': info
            }
            
            module_to_render = pages.get(page)
            if module_to_render and hasattr(module_to_render, 'render'):
                module_to_render.render()
            else:
                st.error(f"Halaman '{page}' tidak ditemukan.")
                navigate_to('home')

if __name__ == "__main__":
    main()