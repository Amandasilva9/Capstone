from pathlib import Path

RAG = Path(__file__).resolve().parents[1]   # backend/rag

DATA       = RAG / "data"
RAW_PDFS   = DATA / "raw_data" / "pdfs"
RAW_MD     = DATA / "raw_data" / "markdowns_raw"
CLEAN_MD   = DATA / "clean_data" / "markdowns_clean"
METADATA   = DATA / "clean_data" / "metadata"
CHUNKS     = DATA / "chunks"
CHROMA_DIR = RAG / "chroma_db"