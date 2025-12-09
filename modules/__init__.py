# modules/__init__.py
# File ini diperlukan untuk membuat folder 'modules' menjadi package Python

from .validators import (
    validate_kk,
    validate_nik,
    validate_custname,
    validate_jenis_kelamin,
    validate_tanggal_lahir,
    generate_validation_notes
)

from .tempat_lahir import (
    normalize_tempat_lahir,
    load_reference_data,
    validate_tempat_lahir,
    validate_tempat_lahir_optimized  # ← TAMBAH INI
)

# Versi package
__version__ = '0.1.0'