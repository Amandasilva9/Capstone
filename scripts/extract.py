import sys
import re
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
DST = Path("data/raw_data/Markdowns") / folder

#error check for missing folder
if not SRC.is_dir():
    sys.exit(f"Folder not found: {SRC}")

REF_PAT = re.compile(
    r'^[ \t]*[#*_ \t]*'                          # heading marks / bold / italics
    r'(?:(?:\d+|[IVXivx]+|[A-Za-z])[.)]?[ \t]+)?'  # optional "8." / "VII." / "A."
    r'(?:references?(?: list)?|bibliography|works cited|literature cited|'
    r'notes and references)'
    r'[ \t]*[*_:]*[ \t]*$',
    re.I | re.M)

def drop_references(texts):
    """Take a list of per-page texts. Return (kept_texts, found), with
    everything from the last references heading onward removed."""
    cut_page, cut_pos = None, None
    for i, t in enumerate(texts):
        for m in REF_PAT.finditer(t):
            cut_page, cut_pos = i, m.start()  # last match wins
    if cut_page is None:
        return texts, False
    return texts[:cut_page] + [texts[cut_page][:cut_pos]], True



failures = []
no_refs = []
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
        pages = pymupdf4llm.to_markdown(str(pdf), page_chunks=True)
        texts, found = drop_references([p["text"] for p in pages])
        if not found:
            no_refs.append(pdf)

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

if no_refs:
    print(f"\n{len(no_refs)} files had no references heading (check by hand):")
    for pdf in no_refs:
        print(f"  {pdf}")