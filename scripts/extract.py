import sys
#PyMuPDF is just a pythong library to help maipulate PDFs and extract text from them. 
import pymupdf4llm  # pip install pymupdf4llm
from pathlib import Path

#This script extracts PDFs from a specified folder into Markdown files.
#This code was wrtten using Claude AI as the script is not neccisary to the project but is a time saver for extracting PDFs to Markdown files.
#The script is being left in the project for future use if more pdfs are added or attempting a diffrent extraction method.
#It is also being left in the project for ease of use for anyone running the project in the future.
#With the caveat that there are other way to extract PDFs and other file types to exract from and convert to. 
#-Hayden Daoust

#if the user does not provide a folder name, exit the script with a usage message
if len(sys.argv) < 2:
    sys.exit("Usage: python scripts/extract.py <folder_name> [--force]")

folder = sys.argv[1]
FORCE = "--force" in sys.argv

#Looks inside the data/raw_data/pdfs/<folder> for PDFs and extracts them to data/raw_data/<folder>
SRC = Path("data/raw_data/pdfs") / folder
DST = Path("data/raw_data/") / folder

#error check for missing folder
if not SRC.is_dir():
    sys.exit(f"Folder not found: {SRC}")

failures = []
pdfs = sorted(SRC.rglob("*.pdf"))

#Print the number of PDFs found in the folder
print(f"Found {len(pdfs)} PDFs in {folder}")

# Extract each PDF
for i, pdf in enumerate(pdfs, 1):
    out = DST / pdf.relative_to(SRC).with_suffix(".md")
    if out.exists() and not FORCE:
        continue
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        # Extract the PDF to Markdown with page chunks
        pages = pymupdf4llm.to_markdown(str(pdf), page_chunks=True)
        parts = []
        for n, p in enumerate(pages, 1):
            meta = p.get("metadata", {})
            page_num = meta.get("page_number", meta.get("page", n))
            parts.append(f"[page {page_num}]\n{p['text']}")
        text = "\n\n".join(parts)
        out.write_text(text, encoding="utf-8")
    except Exception as e:
        # Log the failure and continue with the next PDF
        failures.append((pdf, str(e)))
        print(f"[{i}/{len(pdfs)}] FAILED {pdf.relative_to(SRC)}: {e}")

print(f"\nDone. {len(failures)} failures.")
for pdf, err in failures:
    print(f"  {pdf}: {err}")