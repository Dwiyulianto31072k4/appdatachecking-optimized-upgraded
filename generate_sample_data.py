"""
Demo Script - Generate Sample Data untuk Testing Dashboard
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_sample_data(n_records=1000):
    """
    Generate sample data untuk testing aplikasi
    
    Args:
        n_records: Jumlah record yang akan di-generate
    
    Returns:
        DataFrame with sample data
    """
    
    # Lists untuk random selection
    names = [
        "BUDI SANTOSO", "SITI NURHALIZA", "AHMAD YANI", "DEWI LESTARI",
        "RUDI HARTONO", "MAYA SARI", "AGUS SETIAWAN", "RINA WIJAYA",
        "BAMBANG SUPRIYANTO", "LINA MARLINA", "JOKO WIDODO", "ANI YUDHOYONO",
        "ANDI PRATAMA", "SARI INDAH", "DEDI KURNIAWAN", "FITRI HANDAYANI",
        "HENDRA GUNAWAN", "IKA PUTRI", "FAJAR RAMADHAN", "GITA SAVITRI"
    ]
    
    genders = ["LAKI-LAKI", "PEREMPUAN"]
    
    places = [
        "JAKARTA", "BANDUNG", "SURABAYA", "YOGYAKARTA", "SEMARANG",
        "MEDAN", "PALEMBANG", "MAKASSAR", "DENPASAR", "MALANG",
        "BOGOR", "DEPOK", "TANGERANG", "BEKASI", "SOLO",
        "CIREBON", "TASIKMALAYA", "PONTIANAK", "BANJARMASIN", "BALIKPAPAN"
    ]
    
    # Generate data
    data = []
    
    for i in range(n_records):
        # Generate valid KK and NIK (90% valid)
        is_valid = random.random() < 0.9
        
        if is_valid:
            kk_no = f"{random.randint(1000000000000000, 9999999999999999)}"
            # Pastikan 4 digit terakhir bukan 0000
            kk_no = kk_no[:-4] + str(random.randint(1, 9999)).zfill(4)
            nik = f"{random.randint(1000000000000000, 9999999999999999)}"
            nik = nik[:-4] + str(random.randint(1, 9999)).zfill(4)
        else:
            # Generate invalid data
            if random.random() < 0.5:
                # Invalid: not 16 digits
                kk_no = f"{random.randint(10000000000, 999999999999999)}"
                nik = f"{random.randint(10000000000, 999999999999999)}"
            else:
                # Invalid: ends with 0000
                kk_no = f"{random.randint(100000000000, 999999999999)}0000"
                nik = f"{random.randint(100000000000, 999999999999)}0000"
        
        # Name (95% valid)
        if random.random() < 0.95:
            name = random.choice(names)
        else:
            # Invalid: contains numbers
            name = random.choice(names) + str(random.randint(1, 9))
        
        # Gender (98% valid)
        if random.random() < 0.98:
            gender = random.choice(genders)
        else:
            # Invalid gender
            gender = "LAKI LAKI" if random.random() < 0.5 else "P"
        
        # Place of birth (92% valid)
        if random.random() < 0.92:
            place = random.choice(places)
        else:
            # Invalid: typo or not in reference
            place = "JKRTA" if random.random() < 0.5 else "UNKNOWN CITY"
        
        # Date of birth (97% valid)
        if random.random() < 0.97:
            # Valid: between 1940 and 2020
            year = random.randint(1940, 2020)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            birth_date = datetime(year, month, day)
        else:
            # Invalid: future date
            birth_date = datetime.now() + timedelta(days=random.randint(1, 365))
        
        data.append({
            'KK_NO': kk_no,
            'NIK': nik,
            'CUSTNAME': name,
            'JENIS_KELAMIN': gender,
            'TEMPAT_LAHIR': place,
            'TANGGAL_LAHIR': birth_date
        })
    
    df = pd.DataFrame(data)
    
    return df

def generate_validated_sample_data(n_records=1000):
    """
    Generate sample data yang sudah ter-validasi
    Useful untuk testing dashboard tanpa proses validasi
    """
    
    # Generate base data
    df = generate_sample_data(n_records)
    
    # Add validation columns (simulate validation results)
    df['valid_kk_no'] = df['KK_NO'].apply(lambda x: len(str(x)) == 16 and str(x)[-4:] != '0000')
    df['valid_nik'] = df['NIK'].apply(lambda x: len(str(x)) == 16 and str(x)[-4:] != '0000')
    df['valid_custname'] = df['CUSTNAME'].apply(lambda x: not any(c.isdigit() for c in str(x)))
    df['valid_jenis_kelamin'] = df['JENIS_KELAMIN'].isin(['LAKI-LAKI', 'PEREMPUAN'])
    
    # Simulate tempat lahir validation
    valid_places = [
        "JAKARTA", "BANDUNG", "SURABAYA", "YOGYAKARTA", "SEMARANG",
        "MEDAN", "PALEMBANG", "MAKASSAR", "DENPASAR", "MALANG",
        "BOGOR", "DEPOK", "TANGERANG", "BEKASI", "SOLO",
        "CIREBON", "TASIKMALAYA", "PONTIANAK", "BANJARMASIN", "BALIKPAPAN"
    ]
    
    df['tempat_lahir_normalized'] = df['TEMPAT_LAHIR'].str.upper()
    df['valid_tempat_lahir'] = df['tempat_lahir_normalized'].isin(valid_places)
    df['koreksi_tempat_lahir'] = df.apply(
        lambda x: x['TEMPAT_LAHIR'] if x['valid_tempat_lahir'] else 'JAKARTA',
        axis=1
    )
    
    # Assign level_administrasi
    df['level_administrasi'] = df['valid_tempat_lahir'].apply(
        lambda x: random.choice(['kabupaten', 'kota', 'provinsi']) if x else None
    )
    
    # Confidence score
    df['confidence_score'] = df['valid_tempat_lahir'].apply(
        lambda x: random.uniform(85, 100) if x else random.uniform(50, 84)
    )
    
    # Tanggal lahir validation
    df['valid_tanggal_lahir'] = df['TANGGAL_LAHIR'].apply(
        lambda x: x < datetime.now() if pd.notna(x) else False
    )
    
    # All valid flag
    df['all_valid'] = (
        df['valid_kk_no'] & 
        df['valid_nik'] & 
        df['valid_custname'] & 
        df['valid_jenis_kelamin'] & 
        df['valid_tempat_lahir'] & 
        df['valid_tanggal_lahir']
    )
    
    # Catatan validasi
    df['catatan_validasi'] = df.apply(
        lambda row: None if row['all_valid'] else 
        '; '.join([
            col.replace('valid_', '').replace('_', ' ').title() + ' tidak valid'
            for col in ['valid_kk_no', 'valid_nik', 'valid_custname', 
                       'valid_jenis_kelamin', 'valid_tempat_lahir', 'valid_tanggal_lahir']
            if not row[col]
        ]),
        axis=1
    )
    
    return df

if __name__ == "__main__":
    # Generate sample data
    print("Generating sample data...")
    
    # 1. Raw data untuk upload
    raw_data = generate_sample_data(n_records=5000)
    raw_data.to_excel('sample_data_raw.xlsx', index=False)
    print(f"✓ Generated raw data: sample_data_raw.xlsx ({len(raw_data)} records)")
    
    # 2. Validated data untuk testing dashboard
    validated_data = generate_validated_sample_data(n_records=5000)
    validated_data.to_excel('sample_data_validated.xlsx', index=False)
    print(f"✓ Generated validated data: sample_data_validated.xlsx ({len(validated_data)} records)")
    
    # Statistics
    print("\n" + "="*50)
    print("STATISTICS")
    print("="*50)
    print(f"Total records: {len(validated_data)}")
    print(f"Valid records: {validated_data['all_valid'].sum()} ({validated_data['all_valid'].sum()/len(validated_data)*100:.1f}%)")
    print(f"Invalid records: {(~validated_data['all_valid']).sum()} ({(~validated_data['all_valid']).sum()/len(validated_data)*100:.1f}%)")
    print("\nPer Category:")
    for col in ['valid_kk_no', 'valid_nik', 'valid_custname', 'valid_jenis_kelamin', 'valid_tempat_lahir', 'valid_tanggal_lahir']:
        valid_count = validated_data[col].sum()
        print(f"  {col}: {valid_count} ({valid_count/len(validated_data)*100:.1f}%)")
    
    print("\n✅ Sample data generation completed!")
