import sys
import re
#PyMuPDF is just a pythong library to help maipulate PDFs and extract text from them. 
import pymupdf4llm  # pip install pymupdf4llm
from pathlib import Path
from collections import Counter


#This script extracts PDFs from a specified folder into Markdown files.
#This code was wrtten using Claude AI as the script is a helper script for the process of entering pdfs into the vecter database. 
#The script is being left in the project for future use if more pdfs are added or attempting a diffrent extraction method.
#It is also being left in the project for ease of use for anyone running the project in the future.
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

#detects frequency of a repeted line being the first at each line to remove recuring page headers
def _norm(line):
    line = re.sub(r'[*_#]', '', line)           # ignore bold/heading marks
    return re.sub(r'\d+', '#', line.strip().lower())

def strip_running_headers(texts, edge=3, min_frac=0.3):
    counts = Counter()
    for t in texts:
        lines = [l for l in t.split('\n') if l.strip()]
        counts.update({_norm(l) for l in lines[:edge] + lines[-edge:]})
    threshold = max(3, int(len(texts) * min_frac))
    repeated = {k for k, v in counts.items() if v >= threshold}

    cleaned = []
    for t in texts:
        lines = t.split('\n')
        idx = [i for i, l in enumerate(lines) if l.strip()]
        edge_idx = set(idx[:edge] + idx[-edge:])
        cleaned.append('\n'.join(
            l for i, l in enumerate(lines)
            if not (i in edge_idx and _norm(l) in repeated)))
    return cleaned


#drops a number of headers that do not supply useful infromation 
DROP_HEADINGS = (
    "acknowledg", "funding", "conflict of interest", "conflicts of interest",
    "declaration of competing", "competing interests", "author contributions",
    "credit authorship", "ethics statement", "supplementary", "disclosure",
    "recommendations for future research","inclusion and exclusion criteria", "search strategy",
    "protocol and registration", "data extraction",
    "quality appraisal", "study selection", "additonal file"
)

def _is_heading(line):
    s = line.strip()
    return s.startswith('#') or (s.startswith('**') and s.endswith('**') and len(s) < 80)

def drop_sections(texts):
    skipping = False
    out = []
    for t in texts:
        kept = []
        for line in t.split('\n'):
            if _is_heading(line):
                title = re.sub(r'[#*_]', '', line).strip().lower()
                skipping = len(title) <= 60 and any(k in title for k in DROP_HEADINGS)
            if not skipping:
                kept.append(line)
        out.append('\n'.join(kept))
    return out


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
        texts = [p["text"] for p in pages]
        texts = strip_running_headers(texts)
        texts = drop_sections(texts)
        texts, found = drop_references(texts)
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