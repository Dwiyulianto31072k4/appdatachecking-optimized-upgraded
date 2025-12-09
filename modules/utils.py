import pandas as pd
import io
import base64
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from datetime import datetime

def format_number(number):
    """
    Format angka dengan pemisah ribuan dan 2 digit desimal
    
    Args:
        number: Angka yang akan diformat
    
    Returns:
        str: Angka yang sudah diformat
    """
    return f"{number:,.2f}"

def format_percentage(number):
    """
    Format angka menjadi persentase dengan 2 digit desimal
    
    Args:
        number: Angka yang akan diformat (0.xx)
    
    Returns:
        str: Persentase yang sudah diformat
    """
    return f"{number * 100:.2f}%"

def get_download_link(df, filename="data.xlsx", button_text="Download data"):
    """
    Membuat link download untuk dataframe
    
    Args:
        df: DataFrame yang akan didownload
        filename: Nama file saat didownload
        button_text: Teks yang ditampilkan pada tombol
    
    Returns:
        st.download_button: Tombol download Streamlit
    """
    # Mengkonversi dataframe ke Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Sheet1', index=False)
        writer.save()
    buffer.seek(0)
    
    return st.download_button(
        label=button_text,
        data=buffer,
        file_name=filename,
        mime="application/vnd.ms-excel"
    )

def create_summary_chart(validation_results, title="Hasil Validasi"):
    """
    Membuat chart ringkasan validasi
    
    Args:
        validation_results: Dictionary dengan hasil validasi
        title: Judul chart
    
    Returns:
        fig: Figure matplotlib
    """
    # Siapkan data
    categories = list(validation_results.keys())
    valid_counts = [results['valid'] for results in validation_results.values()]
    invalid_counts = [results['invalid'] for results in validation_results.values()]
    
    # Buat chart
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plotting
    ax.bar(categories, valid_counts, label='Valid', color='green', alpha=0.7)
    ax.bar(categories, invalid_counts, bottom=valid_counts, label='Tidak Valid', color='red', alpha=0.7)
    
    # Styling
    ax.set_ylabel('Jumlah Data')
    ax.set_title(title)
    ax.legend()
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    return fig

def log_activity(activity, user=None):
    """
    Mencatat aktivitas pengguna untuk audit trail
    
    Args:
        activity: Deskripsi aktivitas
        user: Pengguna yang melakukan aktivitas (opsional)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("activity_log.txt", "a") as f:
        f.write(f"{timestamp} - {user if user else 'Anonymous'}: {activity}\n")