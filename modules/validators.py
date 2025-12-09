import pandas as pd
import re
from datetime import datetime

def validate_kk(kk_no):
    """
    Validasi nomor KK dengan aturan:
    - Harus berupa string 16 digit
    - Hanya boleh berisi angka (numerik)
    - 4 digit terakhir tidak boleh 0000
    
    Args:
        kk_no: Nilai KK_NO yang akan divalidasi
    
    Returns:
        bool: True jika KK_NO valid, False jika tidak
    """
    # Pastikan kk_no bertipe string
    if not isinstance(kk_no, str):
        # Coba konversi ke string jika bukan NaN/None
        if pd.notna(kk_no):
            kk_no = str(int(kk_no)) if isinstance(kk_no, (int, float)) else str(kk_no)
        else:
            return False
    
    # Validasi: hanya digit, panjang 16, dan 4 digit terakhir bukan 0000
    if (kk_no.isdigit() and 
        len(kk_no) == 16 and 
        kk_no[-4:] != '0000'):
        return True
    else:
        return False


def validate_nik(nik):
    """
    Validasi NIK dengan aturan:
    - Harus berupa string 16 digit
    - Hanya boleh berisi angka (numerik)
    - 4 digit terakhir tidak boleh 0000
    
    Args:
        nik: Nilai NIK yang akan divalidasi
    
    Returns:
        bool: True jika NIK valid, False jika tidak
    """
    # Pastikan nik bertipe string
    if not isinstance(nik, str):
        # Coba konversi ke string jika bukan NaN/None
        if pd.notna(nik):
            nik = str(int(nik)) if isinstance(nik, (int, float)) else str(nik)
        else:
            return False
    
    # Validasi: hanya digit, panjang 16, dan 4 digit terakhir bukan 0000
    if (nik.isdigit() and 
        len(nik) == 16 and 
        nik[-4:] != '0000'):
        return True
    else:
        return False


def validate_custname(custname):
    """
    Validasi nama customer dengan aturan:
    - Tidak boleh kosong/null
    - Tidak boleh mengandung angka
    
    Args:
        custname: Nilai CUSTNAME yang akan divalidasi
    
    Returns:
        bool: True jika CUSTNAME valid, False jika tidak
    """
    # Periksa apakah custname adalah NaN/None atau kosong
    if pd.isna(custname) or custname == '':
        return False
    
    # Pastikan custname bertipe string
    if not isinstance(custname, str):
        custname = str(custname)
    
    # Validasi: tidak mengandung angka (hanya alphabet dan karakter lain)
    if re.search(r'\d', custname):  # Cek apakah ada digit dalam string
        return False
    else:
        return True


def validate_jenis_kelamin(jenis_kelamin):
    """
    Validasi jenis kelamin dengan aturan:
    - Harus salah satu dari: "LAKI-LAKI", "LAKI - LAKI", "LAKI LAKI", "PEREMPUAN"
    
    Args:
        jenis_kelamin: Nilai JENIS_KELAMIN yang akan divalidasi
    
    Returns:
        bool: True jika JENIS_KELAMIN valid, False jika tidak
    """
    # Periksa apakah jenis_kelamin adalah NaN/None atau kosong
    if pd.isna(jenis_kelamin) or jenis_kelamin == '':
        return False
    
    # Pastikan jenis_kelamin bertipe string
    if not isinstance(jenis_kelamin, str):
        jenis_kelamin = str(jenis_kelamin)
    
    # List nilai valid untuk jenis kelamin
    valid_values = ["LAKI-LAKI", "LAKI - LAKI", "LAKI LAKI", "PEREMPUAN"]
    
    # Validasi: apakah nilainya termasuk dalam list nilai valid
    return jenis_kelamin in valid_values


def validate_tanggal_lahir(tanggal_lahir):
    """
    Validasi tanggal lahir dengan aturan:
    - Tanggal harus dalam format datetime atau pd.Timestamp
    - Tanggal tidak boleh di masa depan (melebihi hari ini)
    - Tanggal harus bisa diparse dengan benar (tidak error)
    
    Args:
        tanggal_lahir: Nilai tanggal lahir yang akan divalidasi
    
    Returns:
        bool: True jika tanggal lahir valid, False jika tidak
    """
    # Periksa apakah tanggal lahir adalah NaN/None
    if pd.isna(tanggal_lahir):
        return False
    
    try:
        # Jika sudah dalam format pd.Timestamp atau datetime, gunakan langsung
        if isinstance(tanggal_lahir, (pd.Timestamp, datetime)):
            tanggal = tanggal_lahir
        else:
            # Coba parse jika dalam format string
            try:
                tanggal = pd.to_datetime(tanggal_lahir)
            except:
                return False
        
        # Validasi tanggal tidak di masa depan
        tanggal_hari_ini = pd.Timestamp.now()
        if tanggal > tanggal_hari_ini:
            return False
        
        # Semua validasi lolos
        return True
    
    except Exception:
        # Jika ada error saat validasi
        return False


def generate_validation_notes(row):
    """
    Menghasilkan catatan validasi untuk data yang tidak valid
    
    Args:
        row: Baris data (Series) yang akan diberi catatan validasi
    
    Returns:
        str: Catatan validasi, atau None jika semua validasi lolos
    """
    notes = []

    # KK_NO
    kk = str(row['KK_NO'])
    if not row['valid_kk_no']:
        if not kk.isdigit():
            notes.append("KK_NO mengandung karakter non-digit")
        elif len(kk) != 16:
            notes.append(f"KK_NO panjang {len(kk)}, harus 16 digit")
        elif kk[-4:] == '0000':
            notes.append("KK_NO 4 digit terakhir = '0000'")

    # NIK
    nik = str(row['NIK'])
    if not row['valid_nik']:
        if not nik.isdigit():
            notes.append("NIK mengandung karakter non-digit")
        elif len(nik) != 16:
            notes.append(f"NIK panjang {len(nik)}, harus 16 digit")
        elif nik[-4:] == '0000':
            notes.append("NIK 4 digit terakhir = '0000'")

    # CUSTNAME
    name = str(row['CUSTNAME'])
    if not row['valid_custname']:
        if any(ch.isdigit() for ch in name):
            notes.append("CUSTNAME mengandung angka")
        else:
            notes.append("CUSTNAME bukan string valid")

    # JENIS KELAMIN
    if not row['valid_jenis_kelamin']:
        notes.append(f"Jenis kelamin '{row['JENIS_KELAMIN']}' tidak valid")

    # TEMPAT LAHIR
    if not row['valid_tempat_lahir']:
        notes.append(f"Tempat lahir '{row['TEMPAT_LAHIR']}' tidak ditemukan di referensi")

    # TANGGAL LAHIR
    dob = row['TANGGAL_LAHIR']
    if not row['valid_tanggal_lahir']:
        if pd.isna(dob):
            notes.append("Tanggal lahir kosong")
        else:
            now = pd.Timestamp.now()
            if dob > now:
                notes.append("Tanggal lahir di masa depan")
            elif (now.year - dob.year) > 120:
                notes.append("Usia melebihi 120 tahun")
            else:
                notes.append("Format tanggal lahir tidak valid")

    return "; ".join(notes) if notes else None