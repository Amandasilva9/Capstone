import sys
#PyMuPDF is just a pythong library to help maipulate PDFs and extract text from them. 
import pymupdf4llm  # pip install pymupdf4llm
from pathlib import Path
import argparse
from paths import RAW_PDFS, RAW_MD

#This script extracts PDFs from a specified folder into Markdown files.
#This code was wrtten using Claude AI as the script is a helper script for the process of entering pdfs into the vecter database. 
#The script is being left in the project for future use if more pdfs are added or attempting a diffrent extraction method.
#It is also being left in the project for ease of use for anyone running the project in the future.
#-Hayden Daoust

ap = argparse.ArgumentParser()
ap.add_argument("folder")
ap.add_argument("--only", help="process just this PDF (filename stem)")
ap.add_argument("--force", action="store_true", help="overwrite existing output")
args = ap.parse_args()
folder = args.folder

SRC = RAW_PDFS / folder
DST = RAW_MD / folder

#error check for missing folder
if not SRC.is_dir():
    sys.exit(f"Folder not found: {SRC}")

failures = []
pdfs = sorted(SRC.rglob("*.pdf"))
if args.only:
    pdfs = [p for p in pdfs if p.stem == args.only]

#Print the number of PDFs found in the folder
print(f"Found {len(pdfs)} PDFs in {folder}")

# Extract each PDF
for i, pdf in enumerate(pdfs, 1):
    out = DST / pdf.relative_to(SRC).with_suffix(".md")
    if out.exists() and not args.force: 
        print(f"[{i}/{len(pdfs)}] skipped (exists): {out}")
        continue
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        pages = pymupdf4llm.to_markdown(str(pdf), page_chunks=True)
        texts = [p["text"] for p in pages]
        parts = []
        for n, t in enumerate(texts, 1):
            meta = pages[n - 1].get("metadata", {})
            page_num = meta.get("page_number", meta.get("page", n))
            parts.append(f"[page {page_num}]\n{t}")
        out.write_text("\n\n".join(parts), encoding="utf-8")
    except Exception as e:
        # Log the failure and continue with the next PDF
        failures.append((pdf, str(e)))
        print(f"[{i}/{len(pdfs)}] FAILED {pdf.relative_to(SRC)}: {e}")

print(f"\nDone. {len(failures)} failures.")
for pdf, err in failures:
    print(f"  {pdf}: {err}")