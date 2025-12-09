import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import io
import time
from modules.validators import validate_kk, validate_nik, validate_custname, validate_jenis_kelamin, validate_tanggal_lahir, generate_validation_notes
from modules.tempat_lahir import validate_tempat_lahir, load_reference_data, validate_tempat_lahir_optimized
from modules.dashboard import ValidationDashboard

# Konfigurasi halaman
st.set_page_config(
    page_title="Aplikasi Validasi Data KK",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2c3e50;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #7f8c8d;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 1rem 2rem;
        font-size: 1.1rem;
    }
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar untuk navigasi
with st.sidebar:
    st.image("https://via.placeholder.com/150x150.png?text=Logo+KK", width=150)
    st.title("Navigation")
    
    page = st.radio(
        "Pilih Menu:",
        ["🏠 Home", "📤 Upload & Validasi", "📊 Dashboard Analytics"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    st.subheader("ℹ️ Informasi")
    st.info("""
    **Fitur Aplikasi:**
    - Upload & Validasi Data KK
    - Dashboard Analytics Lengkap
    - Export PDF & Excel Report
    - Visualisasi Interaktif
    """)
    
    st.divider()
    
    st.caption("© 2024 Validasi Data KK")
    st.caption("Version 2.0")

# ===== HOME PAGE =====
if page == "🏠 Home":
    st.markdown('<div class="main-header">📋 Aplikasi Validasi Data KK</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Sistem Validasi Data Kartu Keluarga dengan Dashboard Analytics Lengkap</div>', unsafe_allow_html=True)
    
    # Feature highlights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🚀 Validasi Cepat
        - Validasi 6 kategori data
        - Support data besar (>300K rows)
        - Algoritma optimized
        - Real-time progress tracking
        """)
    
    with col2:
        st.markdown("""
        ### 📊 Dashboard Analytics
        - Visualisasi interaktif
        - Statistik lengkap
        - Heatmap validasi
        - Analisis tempat lahir
        """)
    
    with col3:
        st.markdown("""
        ### 📥 Export Report
        - PDF Report profesional
        - Excel dengan multiple sheets
        - Statistik detail
        - Ready to present
        """)
    
    st.divider()
    
    # Quick Start Guide
    with st.expander("📚 Quick Start Guide", expanded=True):
        st.markdown("""
        ### Cara Menggunakan Aplikasi:
        
        1. **Upload Data**
           - Klik menu "📤 Upload & Validasi"
           - Upload file Excel (.xlsx atau .xls)
           - Pastikan file memiliki kolom yang diperlukan
        
        2. **Validasi Data**
           - Klik tombol "Validasi Data"
           - Tunggu proses validasi selesai
           - Review hasil validasi
        
        3. **Lihat Dashboard**
           - Klik menu "📊 Dashboard Analytics"
           - Explore visualisasi dan statistik
           - Download laporan PDF atau Excel
        
        ### Kolom yang Diperlukan:
        - **KK_NO**: Nomor Kartu Keluarga (16 digit)
        - **NIK**: Nomor Induk Kependudukan (16 digit)
        - **CUSTNAME**: Nama lengkap (tanpa angka)
        - **JENIS_KELAMIN**: LAKI-LAKI atau PEREMPUAN
        - **TEMPAT_LAHIR**: Nama tempat lahir
        - **TANGGAL_LAHIR**: Tanggal lahir (format tanggal)
        """)
    
    # Sample data info
    with st.expander("📄 Contoh Format Data"):
        sample_data = pd.DataFrame({
            'KK_NO': ['1234567890123456', '9876543210987654'],
            'NIK': ['1234567890123456', '9876543210987654'],
            'CUSTNAME': ['BUDI SANTOSO', 'SITI NURHALIZA'],
            'JENIS_KELAMIN': ['LAKI-LAKI', 'PEREMPUAN'],
            'TEMPAT_LAHIR': ['JAKARTA', 'BANDUNG'],
            'TANGGAL_LAHIR': ['1990-01-15', '1992-05-20']
        })
        st.dataframe(sample_data, use_container_width=True)

# ===== UPLOAD & VALIDASI PAGE =====
elif page == "📤 Upload & Validasi":
    st.title("📤 Upload & Validasi Data KK")
    st.markdown("Upload file Excel untuk memvalidasi data KK, NIK, nama, jenis kelamin, tempat lahir, dan tanggal lahir.")
    
    # Membaca data referensi untuk validasi tempat lahir
    @st.cache_data
    def load_tempat_lahir_reference():
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ref_file_path = os.path.join(current_dir, "data", "LapakGIS_KelurahanDesa_2024.csv")
        
        try:
            ref_data, ref_set = load_reference_data(ref_file_path)
            return ref_data, ref_set
        except Exception as e:
            st.error(f"Error loading reference data: {e}")
            return None, None
    
    # Load reference data
    ref_data, ref_set = load_tempat_lahir_reference()
    
    # Upload file
    uploaded_file = st.file_uploader("Upload File Excel Data KK", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        # Tampilkan spinner selama memproses data
        with st.spinner('Memproses data...'):
            try:
                # Baca file Excel yang diupload
                data = pd.read_excel(
                    uploaded_file,
                    dtype={
                        "NIK": str,
                        "NIK_GROSS": str,
                        "KK_NO": str,
                        "KK_NO_GROSS": str,
                        "CONTRACT_NO": str
                    }
                )

                for col in ["CUSTNAME", "JENIS_KELAMIN", "TEMPAT_LAHIR"]:
                    if col in data.columns:
                        data[col] = data[col].astype(str).str.strip()

                if "TANGGAL_LAHIR" in data.columns:
                    s = data["TANGGAL_LAHIR"]
                    if pd.api.types.is_numeric_dtype(s):
                        data["TANGGAL_LAHIR"] = pd.to_datetime("1899-12-30") + pd.to_timedelta(s.astype(float), unit="D")
                    else:
                        data["TANGGAL_LAHIR"] = pd.to_datetime(
                            s.astype(str).str.strip(),
                            errors="coerce",
                            dayfirst=True
                        )
                
                # Store data in session state
                st.session_state['uploaded_data'] = data
                
                # Tampilkan info data yang diupload
                st.success(f"✅ File berhasil diupload! Total data: {len(data):,} baris")
                
                # Info ukuran data dan estimasi waktu
                data_size_mb = data.memory_usage(deep=True).sum() / 1024**2
                st.info(f"📦 Ukuran data: {data_size_mb:.2f} MB | ⏱️ Estimasi waktu validasi: {'5-10 menit' if len(data) > 50000 else '1-2 menit'}")
                
                # Tampilkan sample data
                st.subheader("Sample Data")
                st.dataframe(data.head(10), use_container_width=True)
                
                # Validasi data
                if st.button("🚀 Validasi Data", type="primary", use_container_width=True):
                    # Inisialisasi progress bar utama
                    progress_bar = st.progress(0)
                    
                    # Hitung total langkah validasi
                    total_steps = 7
                    current_step = 0
                    
                    # Tampilkan informasi proses
                    status_text = st.empty()
                    time_tracker = st.empty()
                    start_time = time.time()
                    
                    with st.spinner('🔄 Sedang memvalidasi data...'):
                        # Validasi KK_NO
                        status_text.text("✓ Memvalidasi nomor KK...")
                        step_start = time.time()
                        data['valid_kk_no'] = data['KK_NO'].apply(validate_kk)
                        current_step += 1
                        progress_bar.progress(current_step/total_steps)
                        step_time = time.time() - step_start
                        time_tracker.text(f"KK validation: {step_time:.1f}s")
                        
                        # Validasi NIK
                        status_text.text("✓ Memvalidasi NIK...")
                        step_start = time.time()
                        data['valid_nik'] = data['NIK'].apply(validate_nik)
                        current_step += 1
                        progress_bar.progress(current_step/total_steps)
                        step_time = time.time() - step_start
                        time_tracker.text(f"NIK validation: {step_time:.1f}s")
                        
                        # Validasi CUSTNAME
                        status_text.text("✓ Memvalidasi nama...")
                        step_start = time.time()
                        data['valid_custname'] = data['CUSTNAME'].apply(validate_custname)
                        current_step += 1
                        progress_bar.progress(current_step/total_steps)
                        step_time = time.time() - step_start
                        time_tracker.text(f"Name validation: {step_time:.1f}s")
                        
                        # Validasi JENIS_KELAMIN
                        status_text.text("✓ Memvalidasi jenis kelamin...")
                        step_start = time.time()
                        data['valid_jenis_kelamin'] = data['JENIS_KELAMIN'].apply(validate_jenis_kelamin)
                        current_step += 1
                        progress_bar.progress(current_step/total_steps)
                        step_time = time.time() - step_start
                        time_tracker.text(f"Gender validation: {step_time:.1f}s")
                        
                        # Validasi TEMPAT_LAHIR
                        status_text.text("✓ Memvalidasi tempat lahir...")
                        tempat_lahir_progress = st.progress(0)
                        step_start = time.time()
                        
                        def update_tempat_lahir_progress(progress):
                            tempat_lahir_progress.progress(progress)
                            elapsed = time.time() - step_start
                            if progress > 0:
                                eta = (elapsed / progress) * (1 - progress)
                                time_tracker.text(f"Tempat lahir validation: {elapsed:.1f}s (ETA: {eta:.1f}s)")
                        
                        # Gunakan algoritma optimized untuk data besar
                        if len(data) > 50000:
                            st.info("🚀 Menggunakan algoritma optimized untuk data besar...")
                            validated_tempat_lahir = validate_tempat_lahir_optimized(
                                data, ref_data, ref_set, threshold=85, 
                                progress_callback=update_tempat_lahir_progress
                            )
                        else:
                            validated_tempat_lahir = validate_tempat_lahir(
                                data, ref_data, ref_set, threshold=85, 
                                progress_callback=update_tempat_lahir_progress
                            )
                        
                        data['tempat_lahir_normalized'] = validated_tempat_lahir['tempat_lahir_normalized']
                        data['valid_tempat_lahir'] = validated_tempat_lahir['valid_tempat_lahir']
                        data['koreksi_tempat_lahir'] = validated_tempat_lahir['koreksi_tempat_lahir']
                        data['level_administrasi'] = validated_tempat_lahir['level_administrasi']
                        data['confidence_score'] = validated_tempat_lahir['confidence_score']
                        current_step += 1
                        progress_bar.progress(current_step/total_steps)
                        step_time = time.time() - step_start
                        time_tracker.text(f"Tempat lahir validation: {step_time:.1f}s")
                        
                        # Validasi TANGGAL_LAHIR
                        status_text.text("✓ Memvalidasi tanggal lahir...")
                        step_start = time.time()
                        data['valid_tanggal_lahir'] = data['TANGGAL_LAHIR'].apply(validate_tanggal_lahir)
                        current_step += 1
                        progress_bar.progress(current_step/total_steps)
                        step_time = time.time() - step_start
                        time_tracker.text(f"Birth date validation: {step_time:.1f}s")
                        
                        # Flag all valid
                        status_text.text("✓ Menyelesaikan validasi...")
                        data['all_valid'] = (data['valid_kk_no'] & 
                                           data['valid_nik'] & 
                                           data['valid_custname'] & 
                                           data['valid_jenis_kelamin'] & 
                                           data['valid_tempat_lahir'] & 
                                           data['valid_tanggal_lahir'])
                        
                        # Tambahkan catatan validasi
                        data['catatan_validasi'] = data.apply(generate_validation_notes, axis=1)
                        current_step += 1
                        progress_bar.progress(current_step/total_steps)
                        
                        # Store validated data in session state
                        st.session_state['validated_data'] = data
                        
                        # Total processing time
                        total_time = time.time() - start_time
                        st.success(f"✅ Validasi selesai dalam {total_time:.1f} detik!")
                        status_text.empty()
                        time_tracker.empty()
                        
                        # Quick summary
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Data", f"{len(data):,}")
                        with col2:
                            all_valid = data['all_valid'].sum()
                            st.metric("Data Valid", f"{all_valid:,}", f"{all_valid/len(data)*100:.1f}%")
                        with col3:
                            any_invalid = len(data) - all_valid
                            st.metric("Data Tidak Valid", f"{any_invalid:,}", f"{any_invalid/len(data)*100:.1f}%")
                        
                        st.info("💡 Lihat dashboard analytics untuk visualisasi lengkap di menu 'Dashboard Analytics'")
                        
                        # Download hasil validasi
                        excel_buffer = io.BytesIO()
                        data.to_excel(excel_buffer, index=False)
                        excel_buffer.seek(0)
                        
                        st.download_button(
                            label="⬇️ Download Hasil Validasi (Excel)",
                            data=excel_buffer,
                            file_name=f'hasil_validasi_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            use_container_width=True
                        )
            
            except Exception as e:
                st.error(f"❌ Error saat memproses file: {e}")
                st.error(f"Detail error: {str(e)}")
                
                if st.checkbox("Tampilkan informasi debug"):
                    st.write("Kolom yang tersedia:", list(data.columns) if 'data' in locals() else "Data belum dimuat")
                    st.write("Tipe data:", data.dtypes if 'data' in locals() else "Data belum dimuat")
    else:
        st.info("📁 Silakan upload file Excel (.xlsx atau .xls) yang berisi data KK untuk divalidasi.")

# ===== DASHBOARD ANALYTICS PAGE =====
elif page == "📊 Dashboard Analytics":
    st.title("📊 Dashboard Analytics")
    
    # Cek apakah ada data yang sudah divalidasi
    if 'validated_data' in st.session_state:
        data = st.session_state['validated_data']
        
        # Create dashboard instance
        dashboard = ValidationDashboard(data)
        
        # Display dashboard
        dashboard.display_dashboard()
        
    else:
        st.warning("⚠️ Belum ada data yang divalidasi.")
        st.info("Silakan upload dan validasi data terlebih dahulu di menu '📤 Upload & Validasi'")
        
        # Show sample dashboard preview
        with st.expander("👀 Preview Dashboard (Sample)"):
            st.image("https://via.placeholder.com/800x400.png?text=Dashboard+Preview", 
                    caption="Contoh tampilan dashboard analytics")
