import pandas as pd
import numpy as np
import re
from rapidfuzz import process, fuzz
import unicodedata

def normalize_tempat_lahir(name):
    """
    Normalisasi nama tempat lahir
    
    Args:
        name: Nama tempat lahir yang akan dinormalisasi
    
    Returns:
        str: Nama tempat lahir yang sudah dinormalisasi
    """
    if pd.isna(name):
        return name
    
    # Konversi ke uppercase
    name = str(name).upper()
    
    # Hapus karakter khusus dan angka
    name = re.sub(r'[^\w\s]', ' ', name)
    name = re.sub(r'\d+', '', name)
    
    # Hapus spasi berlebih
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Normalisasi prefix umum
    prefixes = {
        'DESA ': '',
        'KELURAHAN ': '',
        'KEL ': '',
        'DS ': '',
        'KEC ': '',
        'KECAMATAN ': '',
        'KAB ': '',
        'KABUPATEN ': '',
        'KOTA ': '',
        'PROVINSI ': '',
        'PROV ': ''
    }
    
    for prefix, replacement in prefixes.items():
        if name.startswith(prefix):
            name = replacement + name[len(prefix):]
    
    # Penanganan kasus khusus
    special_cases = {
        'JKT': 'JAKARTA',
        'JAKARTA PUSAT': 'JAKARTA',
        'JAKARTA BARAT': 'JAKARTA',
        'JAKARTA TIMUR': 'JAKARTA',
        'JAKARTA SELATAN': 'JAKARTA',
        'JAKARTA UTARA': 'JAKARTA',
        'DKI JAKARTA': 'JAKARTA',
        'JOGJAKARTA': 'YOGYAKARTA',
        'JOGJA': 'YOGYAKARTA',
        'YOGYA': 'YOGYAKARTA',

        # Tambahan validasi kabupaten/kota
        'KOTA BARU': 'KOTABARU',
        'KOTA BAROE': 'KOTABARU',
        'KOTAWARINGIN': 'KOTAWARINGIN BARAT',
        'KOTAWARINGIN BRT': 'KOTAWARINGIN BARAT',
        'KOTAWARINGIN TIMUR': 'KOTAWARINGIN TIMUR',
        'KOTAWARINGIN TMR': 'KOTAWARINGIN TIMUR',
        '50 KOTA': 'LIMA PULUH KOTA',
        'LIMA 50 KOTA': 'LIMA PULUH KOTA',
        'KOTA KOTAMOBAGU': 'KOTAMOBAGU',
        'PEKAN BARU': 'PEKANBARU',
        'LUBUK LINGGAU': 'LUBUKLINGGAU',
        'KABUPATEN BATU BARA': 'KABUPATEN BATUBARA',
    }
    
    for case, replacement in special_cases.items():
        if name == case:
            name = replacement
    
    return name



def validate_tempat_lahir_optimized(data, ref_data, ref_set, threshold=85, progress_callback=None):
    """
    OPTIMIZED: Validasi tempat lahir dengan algoritma yang lebih efisien
    """
    validated_data = data.copy()
    validated_data['tempat_lahir_normalized'] = validated_data['TEMPAT_LAHIR'].apply(normalize_tempat_lahir)
    
    # Initialize results
    validated_data['valid_tempat_lahir'] = False
    validated_data['koreksi_tempat_lahir'] = None
    validated_data['level_administrasi'] = None
    validated_data['confidence_score'] = 0.0
    
    # Exact matching (vectorized)
    exact_match_map = dict(zip(ref_data['nama_normalized'], zip(ref_data['nama'], ref_data['level'])))
    exact_mask = validated_data['tempat_lahir_normalized'].isin(ref_set)
    exact_matches = validated_data[exact_mask]
    
    # Set exact matches
    for idx in exact_matches.index:
        temp_lahir = validated_data.loc[idx, 'tempat_lahir_normalized']
        if temp_lahir in exact_match_map:
            nama_asli, level = exact_match_map[temp_lahir]
            validated_data.loc[idx, 'valid_tempat_lahir'] = True
            validated_data.loc[idx, 'confidence_score'] = 100.0
            validated_data.loc[idx, 'koreksi_tempat_lahir'] = nama_asli
            validated_data.loc[idx, 'level_administrasi'] = level
    
    # Fuzzy matching only for unique non-exact matches
    fuzzy_candidates = validated_data[~exact_mask]
    if len(fuzzy_candidates) == 0:
        return validated_data
    
    unique_fuzzy = fuzzy_candidates['tempat_lahir_normalized'].unique()
    fuzzy_results = {}
    ref_list = list(ref_set)
    
    # Process unique values only
    for i, temp_lahir in enumerate(unique_fuzzy):
        if pd.isna(temp_lahir) or temp_lahir == '':
            continue
            
        result = process.extractOne(temp_lahir, ref_list, scorer=fuzz.token_sort_ratio)
        
        if result and len(result) >= 2:
            match = result[0]
            score = result[1]
            
            if score >= threshold:
                nama_asli, level = exact_match_map.get(match, (match, 'tidak diketahui'))
                fuzzy_results[temp_lahir] = {
                    'valid': True,
                    'score': score,
                    'koreksi': nama_asli,
                    'level': level
                }
        
        if progress_callback and i % 100 == 0:
            progress_callback(min(i / len(unique_fuzzy), 1.0))
    
    # Apply fuzzy results
    for temp_lahir, result in fuzzy_results.items():
        mask = validated_data['tempat_lahir_normalized'] == temp_lahir
        validated_data.loc[mask, 'valid_tempat_lahir'] = result['valid']
        validated_data.loc[mask, 'confidence_score'] = result['score']
        validated_data.loc[mask, 'koreksi_tempat_lahir'] = result['koreksi']
        validated_data.loc[mask, 'level_administrasi'] = result['level']
    
    if progress_callback:
        progress_callback(1.0)
    
    return validated_data

def load_reference_data(filepath):
    """
    Muat data referensi dari file CSV
    
    Args:
        filepath: Path ke file CSV referensi
    
    Returns:
        tuple: (dataframe referensi, set referensi untuk matching cepat)
    """
    ref_data = pd.read_csv(filepath)
    
    # Buat DataFrames untuk setiap level administrasi
    # 1. Desa/Kelurahan
    desa_df = ref_data[['NAMOBJ', 'WADMKD']].dropna().drop_duplicates()
    desa_df = desa_df.rename(columns={'WADMKD': 'nama', 'NAMOBJ': 'kode'})
    desa_df['level'] = 'desa'
    
    # 2. Kecamatan
    kec_df = ref_data[['WADMKC']].dropna().drop_duplicates()
    kec_df = kec_df.rename(columns={'WADMKC': 'nama'})
    kec_df['kode'] = kec_df['nama']
    kec_df['level'] = 'kecamatan'
    
    # 3. Kabupaten/Kota
    kab_df = ref_data[['WADMKK']].dropna().drop_duplicates()
    kab_df = kab_df.rename(columns={'WADMKK': 'nama'})
    kab_df['kode'] = kab_df['nama']
    kab_df['level'] = 'kabupaten'
    
    # 4. Provinsi
    prov_df = ref_data[['WADMPR']].dropna().drop_duplicates()
    prov_df = prov_df.rename(columns={'WADMPR': 'nama'})
    prov_df['kode'] = prov_df['nama']
    prov_df['level'] = 'provinsi'
    
    # Gabungkan semua level
    all_locations = pd.concat([desa_df, kec_df, kab_df, prov_df])
    
    # Normalisasi nama lokasi
    all_locations['nama_normalized'] = all_locations['nama'].apply(normalize_tempat_lahir)
    
    # Buat set referensi untuk pencocokan cepat
    ref_set = set(all_locations['nama_normalized'].unique())
    
    return all_locations, ref_set

def validate_tempat_lahir(data, ref_data, ref_set, threshold=85, progress_callback=None):
    """
    Validasi tempat lahir dengan exact dan fuzzy matching
    
    Args:
        data: DataFrame yang berisi data yang akan divalidasi
        ref_data: DataFrame referensi yang berisi data lokasi yang valid
        ref_set: Set referensi untuk pencocokan cepat
        threshold: Threshold untuk fuzzy matching (default: 85)
        progress_callback: Fungsi callback untuk melaporkan progress (opsional)
    
    Returns:
        DataFrame: DataFrame dengan hasil validasi
    """
    # Buat salinan data
    validated_data = data.copy()
    
    # Normalisasi tempat lahir di data
    validated_data['tempat_lahir_normalized'] = validated_data['TEMPAT_LAHIR'].apply(normalize_tempat_lahir)
    
    # Hasil validasi
    validated_data['valid_tempat_lahir'] = False
    validated_data['koreksi_tempat_lahir'] = None
    validated_data['level_administrasi'] = None
    validated_data['confidence_score'] = 0.0
    
    # 1. Exact matching
    exact_match_map = dict(zip(ref_data['nama_normalized'], zip(ref_data['nama'], ref_data['level'])))
    
    # Jumlah total baris untuk progress reporting
    total_rows = len(validated_data)
    
    # Iterasi baris data
    for i, (idx, row) in enumerate(validated_data.iterrows()):
        temp_lahir = row['tempat_lahir_normalized']
        if pd.isna(temp_lahir) or temp_lahir == '':
            continue
            
        # Exact matching
        if temp_lahir in ref_set:
            validated_data.loc[idx, 'valid_tempat_lahir'] = True
            validated_data.loc[idx, 'confidence_score'] = 100.0
            nama_asli, level = exact_match_map.get(temp_lahir, (temp_lahir, 'tidak diketahui'))
            validated_data.loc[idx, 'koreksi_tempat_lahir'] = nama_asli
            validated_data.loc[idx, 'level_administrasi'] = level
            continue
        
        # Fuzzy matching
        result = process.extractOne(
            temp_lahir, 
            list(ref_set), 
            scorer=fuzz.token_sort_ratio
        )
        
        if result and len(result) >= 2:
            match = result[0]
            score = result[1]
            
            if score >= threshold:
                validated_data.loc[idx, 'valid_tempat_lahir'] = True
                validated_data.loc[idx, 'confidence_score'] = score
                nama_asli, level = exact_match_map.get(match, (match, 'tidak diketahui'))
                validated_data.loc[idx, 'koreksi_tempat_lahir'] = nama_asli
                validated_data.loc[idx, 'level_administrasi'] = level
        
        # Update progress setiap 10 baris atau sesuai kebutuhan
        if progress_callback and i % 10 == 0:
            progress_callback(min(i / total_rows, 1.0))
    
    # Pastikan progress mencapai 100% di akhir
    if progress_callback:
        progress_callback(1.0)
    
    return validated_data

def generate_validation_report(data):
    """
    Buat laporan hasil validasi tempat lahir
    
    Args:
        data: DataFrame dengan hasil validasi
    
    Returns:
        dict: Laporan validasi dalam bentuk dictionary
    """
    total_records = len(data)
    valid_records = data['valid_tempat_lahir'].sum()
    valid_percentage = valid_records / total_records * 100
    
    # Distribusi berdasarkan level administrasi
    level_dist = data[data['valid_tempat_lahir']]['level_administrasi'].value_counts()
    level_distribution = {}
    for level, count in level_dist.items():
        level_distribution[level] = {
            'count': int(count),
            'percentage': float(count/valid_records*100)
        }
    
    # Distribusi confidence score
    bins = [0, 70, 80, 90, 95, 100]
    labels = ['0-70', '70-80', '80-90', '90-95', '95-100']
    data['confidence_bin'] = pd.cut(data['confidence_score'], bins=bins, labels=labels)
    
    confidence_dist = data['confidence_bin'].value_counts().sort_index()
    confidence_distribution = {}
    for bin_label, count in confidence_dist.items():
        if not pd.isna(bin_label):  # Skip NaN values
            confidence_distribution[str(bin_label)] = {
                'count': int(count),
                'percentage': float(count/total_records*100)
            }
    
    # Top koreksi yang dilakukan
    corrections = data[data['tempat_lahir_normalized'] != data['koreksi_tempat_lahir']]
    corrections = corrections[~corrections['koreksi_tempat_lahir'].isna()]
    
    top_corrections = corrections.groupby(['tempat_lahir_normalized', 'koreksi_tempat_lahir', 'level_administrasi']).size().reset_index(name='count')
    top_corrections = top_corrections.sort_values('count', ascending=False).head(20)
    
    top_corrections_list = []
    for _, row in top_corrections.iterrows():
        top_corrections_list.append({
            'original': row['tempat_lahir_normalized'],
            'correction': row['koreksi_tempat_lahir'],
            'level': row['level_administrasi'],
            'count': int(row['count'])
        })
    
    # Tempat lahir yang tidak valid
    invalid = data[~data['valid_tempat_lahir']]
    invalid_sample = invalid.sample(min(20, len(invalid)))
    
    invalid_samples_list = []
    for _, row in invalid_sample.iterrows():
        invalid_samples_list.append({
            'tempat_lahir': row['TEMPAT_LAHIR'],
            'normalized': row['tempat_lahir_normalized'],
            'confidence_score': float(row['confidence_score']) if not pd.isna(row['confidence_score']) else 0.0
        })
    
    # Kompilasi laporan
    report = {
        'total_records': total_records,
        'valid_records': int(valid_records),
        'valid_percentage': float(valid_percentage),
        'invalid_records': int(total_records - valid_records),
        'invalid_percentage': float(100 - valid_percentage),
        'level_distribution': level_distribution,
        'confidence_distribution': confidence_distribution,
        'top_corrections': top_corrections_list,
        'invalid_samples': invalid_samples_list
    }
    
    return report
