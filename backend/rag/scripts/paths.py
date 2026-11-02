from pathlib import Path

DATA = Path("data")
RAW_PDFS      = DATA / "raw_data" / "pdfs"
RAW_MD        = DATA / "raw_data" / "markdowns_raw"
CLEAN_MD      = DATA / "clean_data" / "markdowns_clean"
METADATA      = DATA / "clean_data" / "metadata"
CHUNKS        = DATA  / "chunks"
CHROMA_DIR    = Path("chroma_db")