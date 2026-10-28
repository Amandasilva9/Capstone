import sys
import json
#use pymupdf to extract metadata from PDFs same as the extract.py script but this time we are extracting metadata instead of text.
import pymupdf  # pymupdf
from pathlib import Path
from paths import RAW_PDFS, CLEAN_MD, METADATA

#This script extracts metadata from PDFs in a specified folder and saves it to a JSON file.
#It is another helper script to help with the project it is a time saver for extracting metadata from PDFs.
#This was written using Claude AI and can be used if more pdfs are added to help speed up the process of extracting metadata from PDFs.
#-Hayden Daoust

#if the user does not provide a folder name, exit the script with a usage message
if len(sys.argv) < 2:
    sys.exit("Usage: python scripts/make_metadata.py <folder_name>")

# Get the folder name from the command line arguments
folder = sys.argv[1]
PDF_DIR = RAW_PDFS / folder
MD_DIR = CLEAN_MD / folder
OUT = METADATA / f"{folder}.json"

#error check for missing folder
if not PDF_DIR.is_dir():
    sys.exit(f"Folder not found: {PDF_DIR}")

# load existing file so hand-edited entries are preserved
if OUT.exists():
    data = json.loads(OUT.read_text(encoding="utf-8"))
else:
    data = {"topic": folder, "sources": []}

existing = {s["source_id"] for s in data["sources"]}

# Loop through all PDFs in the specified folder and extract metadata for each PDF.
# If the source_id already exists in the existing set, it will skip that PDF.
# Otherwise, it will open the PDF using pymupdf, extract relevant metadata, and append it to the data["sources"] list.
for pdf in sorted(PDF_DIR.rglob("*.pdf")):
    sid = f"{folder}/{pdf.relative_to(PDF_DIR).with_suffix('').as_posix()}"
    if sid in existing:
        continue
    try:
        doc = pymupdf.open(pdf)
        title = (doc.metadata or {}).get("title", "") or ""
        page_count = len(doc)
        doc.close()
    except Exception as e:
        print(f"FAILED {sid}: {e}")
        continue
    data["sources"].append({
        "source_id": sid,
        "title": title,
        "authors": [],
        "year": None,
        "journal": "",
        "doi": "",
        "study_type": "",
        "keywords": [],
        "pdf_path": pdf.as_posix(),
        "markdown_path": (MD_DIR / pdf.relative_to(PDF_DIR).with_suffix(".md")).as_posix(),
        "page_count": page_count,
        "notes": "",
        "reviewed": False,
    })
    print("added", sid)

# Save the updated metadata to a JSON file, creating the parent directory if it doesn't exist.
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")