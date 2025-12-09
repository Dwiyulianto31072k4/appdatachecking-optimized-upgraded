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

# Konfigurasi halaman
st.set_page_config(
    page_title="Aplikasi Validasi Data KK",
    page_icon="📋",
    layout="wide"
)

# Judul aplikasi
st.title("Aplikasi Validasi Data KK")
st.markdown("Aplikasi ini membantu Anda memvalidasi data KK, NIK, nama, jenis kelamin, tempat lahir, dan tanggal lahir.")

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

            
            
            # Tampilkan info data yang diupload
            st.success(f"File berhasil diupload! Total data: {len(data):,} baris")
            
            # Info ukuran data dan estimasi waktu
            data_size_mb = data.memory_usage(deep=True).sum() / 1024**2
            st.info(f"Ukuran data: {data_size_mb:.2f} MB | Estimasi waktu validasi: {'5-10 menit' if len(data) > 50000 else '1-2 menit'}")
            
            # Tampilkan sample data
            st.subheader("Sample Data")
            st.dataframe(data.head())
            
            # Validasi data
            if st.button("Validasi Data"):
                # Inisialisasi progress bar utama
                progress_bar = st.progress(0)
                
                # Hitung total langkah validasi
                total_steps = 7  # 6 validasi + 1 untuk finalisasi
                current_step = 0
                
                # Tampilkan informasi proses
                status_text = st.empty()
                time_tracker = st.empty()
                start_time = time.time()
                
                with st.spinner('Sedang memvalidasi data...'):
                    # Validasi KK_NO
                    status_text.text("Memvalidasi nomor KK...")
                    step_start = time.time()
                    data['valid_kk_no'] = data['KK_NO'].apply(validate_kk)
                    current_step += 1
                    progress_bar.progress(current_step/total_steps)
                    step_time = time.time() - step_start
                    time_tracker.text(f"KK validation: {step_time:.1f}s")
                    
                    # Validasi NIK
                    status_text.text("Memvalidasi NIK...")
                    step_start = time.time()
                    data['valid_nik'] = data['NIK'].apply(validate_nik)
                    current_step += 1
                    progress_bar.progress(current_step/total_steps)
                    step_time = time.time() - step_start
                    time_tracker.text(f"NIK validation: {step_time:.1f}s")
                    
                    # Validasi CUSTNAME
                    status_text.text("Memvalidasi nama...")
                    step_start = time.time()
                    data['valid_custname'] = data['CUSTNAME'].apply(validate_custname)
                    current_step += 1
                    progress_bar.progress(current_step/total_steps)
                    step_time = time.time() - step_start
                    time_tracker.text(f"Name validation: {step_time:.1f}s")
                    
                    # Validasi JENIS_KELAMIN
                    status_text.text("Memvalidasi jenis kelamin...")
                    step_start = time.time()
                    data['valid_jenis_kelamin'] = data['JENIS_KELAMIN'].apply(validate_jenis_kelamin)
                    current_step += 1
                    progress_bar.progress(current_step/total_steps)
                    step_time = time.time() - step_start
                    time_tracker.text(f"Gender validation: {step_time:.1f}s")
                    
                    # Validasi TEMPAT_LAHIR
                    status_text.text("Memvalidasi tempat lahir...")
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
                    status_text.text("Memvalidasi tanggal lahir...")
                    step_start = time.time()
                    data['valid_tanggal_lahir'] = data['TANGGAL_LAHIR'].apply(validate_tanggal_lahir)
                    current_step += 1
                    progress_bar.progress(current_step/total_steps)
                    step_time = time.time() - step_start
                    time_tracker.text(f"Birth date validation: {step_time:.1f}s")
                    
                    # Flag all valid
                    status_text.text("Menyelesaikan validasi...")
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
                    
                    # Total processing time
                    total_time = time.time() - start_time
                    st.success(f"✅ Validasi selesai dalam {total_time:.1f} detik!")
                    status_text.empty()
                    time_tracker.empty()
                    
                    # Tampilkan hasil validasi
                    st.subheader("Hasil Validasi")
                    
                    # Layout 2 kolom untuk statistik dan chart
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Statistik validasi
                        total_records = len(data)
                        all_valid_count = data['all_valid'].sum()
                        any_invalid_count = total_records - all_valid_count
                        
                        st.metric("Total Data", f"{total_records:,}")
                        st.metric("Data Valid", f"{all_valid_count:,} ({all_valid_count/total_records*100:.2f}%)")
                        st.metric("Data Tidak Valid", f"{any_invalid_count:,} ({any_invalid_count/total_records*100:.2f}%)")
                        
                        # Performance metrics
                        st.metric("Processing Speed", f"{total_records/total_time:.0f} rows/sec")
                    
                    with col2:
                        # Chart untuk visualisasi hasil validasi
                        fig, ax = plt.subplots(figsize=(10, 6))
                        
                        # Hasil validasi per kategori
                        validation_results = {
                            'KK_NO': data['valid_kk_no'].sum(),
                            'NIK': data['valid_nik'].sum(),
                            'Nama': data['valid_custname'].sum(),
                            'Jenis Kelamin': data['valid_jenis_kelamin'].sum(),
                            'Tempat Lahir': data['valid_tempat_lahir'].sum(),
                            'Tanggal Lahir': data['valid_tanggal_lahir'].sum()
                        }
                        
                        categories = list(validation_results.keys())
                        valid_counts = list(validation_results.values())
                        invalid_counts = [total_records - count for count in valid_counts]
                        
                        ax.bar(categories, valid_counts, label='Valid', color='green')
                        ax.bar(categories, invalid_counts, bottom=valid_counts, label='Tidak Valid', color='red')
                        
                        ax.set_ylabel('Jumlah Data')
                        ax.set_title('Hasil Validasi per Kategori')
                        ax.legend()
                        
                        # Rotasi label untuk lebih mudah dibaca
                        plt.xticks(rotation=45)
                        plt.tight_layout()
                        
                        st.pyplot(fig)
                    
                    # Tabs untuk detail hasil validasi
                    tab1, tab2, tab3 = st.tabs(["Detail Validasi", "Data Tidak Valid", "Semua Data"])
                    
                    with tab1:
                        st.subheader("Detail Validasi per Kategori")
                        
                        # Detail validasi KK
                        st.markdown("### Validasi KK")
                        kk_valid = data['valid_kk_no'].sum()
                        kk_invalid = total_records - kk_valid
                        st.write(f"KK Valid: {kk_valid:,} ({kk_valid/total_records*100:.2f}%)")
                        st.write(f"KK Tidak Valid: {kk_invalid:,} ({kk_invalid/total_records*100:.2f}%)")
                        
                        if kk_invalid > 0:
                            st.write("Contoh KK tidak valid:")
                            st.dataframe(data[~data['valid_kk_no']].head()[['KK_NO']])
                        
                        # Detail validasi NIK
                        st.markdown("### Validasi NIK")
                        nik_valid = data['valid_nik'].sum()
                        nik_invalid = total_records - nik_valid
                        st.write(f"NIK Valid: {nik_valid:,} ({nik_valid/total_records*100:.2f}%)")
                        st.write(f"NIK Tidak Valid: {nik_invalid:,} ({nik_invalid/total_records*100:.2f}%)")
                        
                        if nik_invalid > 0:
                            st.write("Contoh NIK tidak valid:")
                            st.dataframe(data[~data['valid_nik']].head()[['NIK']])
                        
                        # Detail validasi Nama
                        st.markdown("### Validasi Nama")
                        name_valid = data['valid_custname'].sum()
                        name_invalid = total_records - name_valid
                        st.write(f"Nama Valid: {name_valid:,} ({name_valid/total_records*100:.2f}%)")
                        st.write(f"Nama Tidak Valid: {name_invalid:,} ({name_invalid/total_records*100:.2f}%)")
                        
                        if name_invalid > 0:
                            st.write("Contoh Nama tidak valid:")
                            st.dataframe(data[~data['valid_custname']].head()[['CUSTNAME']])
                        
                        # Detail validasi Jenis Kelamin
                        st.markdown("### Validasi Jenis Kelamin")
                        jk_valid = data['valid_jenis_kelamin'].sum()
                        jk_invalid = total_records - jk_valid
                        st.write(f"Jenis Kelamin Valid: {jk_valid:,} ({jk_valid/total_records*100:.2f}%)")
                        st.write(f"Jenis Kelamin Tidak Valid: {jk_invalid:,} ({jk_invalid/total_records*100:.2f}%)")
                        
                        if jk_invalid > 0:
                            st.write("Contoh Jenis Kelamin tidak valid:")
                            st.dataframe(data[~data['valid_jenis_kelamin']].head()[['JENIS_KELAMIN']])
                        
                        # Detail validasi Tempat Lahir (lebih detail karena lebih kompleks)
                        st.markdown("### Validasi Tempat Lahir")
                        tempat_lahir_valid = data['valid_tempat_lahir'].sum()
                        tempat_lahir_invalid = total_records - tempat_lahir_valid
                        st.write(f"Tempat Lahir Valid: {tempat_lahir_valid:,} ({tempat_lahir_valid/total_records*100:.2f}%)")
                        st.write(f"Tempat Lahir Tidak Valid: {tempat_lahir_invalid:,} ({tempat_lahir_invalid/total_records*100:.2f}%)")
                        
                        # Distribusi level administrasi
                        if 'level_administrasi' in data.columns:
                            level_dist = data[data['valid_tempat_lahir']]['level_administrasi'].value_counts()
                            st.write("Distribusi Level Administrasi:")
                            
                            level_data = pd.DataFrame({
                                'Level': level_dist.index,
                                'Jumlah': level_dist.values,
                                'Persentase': [f"{count/tempat_lahir_valid*100:.2f}%" for count in level_dist.values]
                            })
                            
                            st.dataframe(level_data)
                        
                        # Detail validasi Tanggal Lahir
                        st.markdown("### Validasi Tanggal Lahir")
                        tl_valid = data['valid_tanggal_lahir'].sum()
                        tl_invalid = total_records - tl_valid
                        st.write(f"Tanggal Lahir Valid: {tl_valid:,} ({tl_valid/total_records*100:.2f}%)")
                        st.write(f"Tanggal Lahir Tidak Valid: {tl_invalid:,} ({tl_invalid/total_records*100:.2f}%)")
                        
                        if tl_invalid > 0:
                            st.write("Contoh Tanggal Lahir tidak valid:")
                            st.dataframe(data[~data['valid_tanggal_lahir']].head()[['TANGGAL_LAHIR']])
                        
                    with tab2:
                        st.subheader("Data Tidak Valid")
                        invalid_data = data[~data['all_valid']]
                        
                        if len(invalid_data) > 0:
                            st.write(f"Total data tidak valid: {len(invalid_data):,}")
                            
                            # Filter untuk menampilkan berdasarkan jenis validasi
                            validation_types = st.multiselect(
                                "Filter berdasarkan validasi yang gagal:",
                                ["KK_NO", "NIK", "Nama", "Jenis Kelamin", "Tempat Lahir", "Tanggal Lahir"],
                                placeholder="Pilih jenis validasi"
                            )
                            
                            filtered_data = invalid_data.copy()
                            
                            if validation_types:
                                mask = pd.Series(False, index=filtered_data.index)
                                
                                if "KK_NO" in validation_types:
                                    mask = mask | ~filtered_data['valid_kk_no']
                                if "NIK" in validation_types:
                                    mask = mask | ~filtered_data['valid_nik']
                                if "Nama" in validation_types:
                                    mask = mask | ~filtered_data['valid_custname']
                                if "Jenis Kelamin" in validation_types:
                                    mask = mask | ~filtered_data['valid_jenis_kelamin']
                                if "Tempat Lahir" in validation_types:
                                    mask = mask | ~filtered_data['valid_tempat_lahir']
                                if "Tanggal Lahir" in validation_types:
                                    mask = mask | ~filtered_data['valid_tanggal_lahir']
                                
                                filtered_data = filtered_data[mask]
                            
                            # Tampilkan data tidak valid dengan catatan validasi
                            st.dataframe(filtered_data[[
                                'KK_NO', 'NIK', 'CUSTNAME', 'JENIS_KELAMIN', 'TEMPAT_LAHIR', 'TANGGAL_LAHIR',
                                'valid_kk_no', 'valid_nik', 'valid_custname', 'valid_jenis_kelamin',
                                'valid_tempat_lahir', 'valid_tanggal_lahir', 'catatan_validasi'
                            ]])
                            
                            # Tambahkan informasi tentang koreksi tempat lahir jika tersedia
                            if 'koreksi_tempat_lahir' in filtered_data.columns:
                                tempat_lahir_issues = filtered_data[~filtered_data['valid_tempat_lahir']]
                                
                                if not tempat_lahir_issues.empty:
                                    st.subheader("Koreksi Tempat Lahir Yang Disarankan")
                                    st.write("Berikut adalah saran koreksi untuk tempat lahir yang tidak valid:")
                                    
                                    koreksi_df = tempat_lahir_issues[['TEMPAT_LAHIR', 'tempat_lahir_normalized', 'koreksi_tempat_lahir', 'confidence_score']]
                                    koreksi_df = koreksi_df.rename(columns={
                                        'TEMPAT_LAHIR': 'Tempat Lahir Asli',
                                        'tempat_lahir_normalized': 'Tempat Lahir Normalisasi',
                                        'koreksi_tempat_lahir': 'Koreksi Yang Disarankan',
                                        'confidence_score': 'Skor Kepercayaan (%)'
                                    })
                                    
                                    # Filter hanya yang memiliki saran koreksi
                                    koreksi_df = koreksi_df[~koreksi_df['Koreksi Yang Disarankan'].isna()]
                                    
                                    if not koreksi_df.empty:
                                        st.dataframe(koreksi_df)
                                    else:
                                        st.info("Tidak ada saran koreksi untuk tempat lahir yang tidak valid.")
                            
                            # Download data tidak valid
                            csv_buffer = io.BytesIO()
                            filtered_data.to_excel(csv_buffer, index=False)
                            csv_buffer.seek(0)
                            
                            st.download_button(
                                label="Download Data Tidak Valid (Excel)",
                                data=csv_buffer,
                                file_name='data_tidak_valid.xlsx',
                                mime='application/vnd.ms-excel'
                            )
                        else:
                            st.success("Semua data valid! Tidak ada data yang gagal validasi.")
                    
                    with tab3:
                        st.subheader("Semua Data Dengan Hasil Validasi")
                        
                        # Opsi untuk menampilkan kolom tertentu saja
                        columns_to_display = st.multiselect(
                            "Pilih kolom yang ingin ditampilkan:",
                            data.columns.tolist(),
                            default=['KK_NO', 'NIK', 'CUSTNAME', 'JENIS_KELAMIN', 'TEMPAT_LAHIR', 'TANGGAL_LAHIR', 'all_valid', 'catatan_validasi']
                        )
                        
                        if columns_to_display:
                            st.dataframe(data[columns_to_display])
                        else:
                            st.dataframe(data)
                        
                        # Download semua data dengan hasil validasi
                        excel_buffer = io.BytesIO()
                        data.to_excel(excel_buffer, index=False)
                        excel_buffer.seek(0)
                        
                        st.download_button(
                            label="Download Semua Data Dengan Hasil Validasi (Excel)",
                            data=excel_buffer,
                            file_name='hasil_validasi_lengkap.xlsx',
                            mime='application/vnd.ms-excel'
                        )
        
        except Exception as e:
            st.error(f"Error saat memproses file: {e}")
            st.error(f"Detail error: {str(e)}")
            
            # Debugging info
            if st.checkbox("Tampilkan informasi debug"):
                st.write("Kolom yang tersedia:", list(data.columns) if 'data' in locals() else "Data belum dimuat")
                st.write("Tipe data:", data.dtypes if 'data' in locals() else "Data belum dimuat")
else:
    st.info("Silakan upload file Excel (.xlsx atau .xls) yang berisi data KK untuk divalidasi.")
    
    # Informasi tambahan
    with st.expander("ℹ️ Informasi Format Data"):
        st.markdown("""
        **Kolom yang diperlukan:**
        - KK_NO: Nomor Kartu Keluarga (16 digit)
        - NIK: Nomor Induk Kependudukan (16 digit)
        - CUSTNAME: Nama lengkap (tanpa angka)
        - JENIS_KELAMIN: LAKI-LAKI atau PEREMPUAN
        - TEMPAT_LAHIR: Nama tempat lahir
        - TANGGAL_LAHIR: Tanggal lahir (format tanggal)
        
        **Optimasi untuk data besar:**
        - Data > 50,000 rows: Menggunakan algoritma optimized
        - Estimasi waktu: 5-10 menit untuk 300,000+ rows
        - Maximum file size: 500MB
        """)
