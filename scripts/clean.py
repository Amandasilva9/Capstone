import re
import sys
import argparse
from pathlib import Path
from collections import Counter
from paths import RAW_MD, CLEAN_MD

# Cleans raw extracted markdown (data/raw_data/Markdowns/<joint>) into
# data/clean_data/Markdowns/<joint>. Files that already exist in the output
# are SKIPPED so hand edits are never overwritten.
# Use --only <stem> --force to deliberately redo a single file.

In_MD = RAW_MD
Out_MD = CLEAN_MD

REF_PAT = re.compile(
    r'^[ \t]*[#*_ \t]*'                          # heading marks / bold / italics
    r'(?:(?:\d+|[IVXivx]+|[A-Za-z])[.)]?[ \t]+)?'  # optional "8." / "VII." / "A."
    r'(?:references?(?: list)?|bibliography|works cited|literature cited|'
    r'notes and references)'
    r'[ \t]*[*_:]*[ \t]*$',
    re.I | re.M)

def drop_big_tables(texts, max_lines=12):
    out = []
    for t in texts:
        lines, kept, run = t.split("\n"), [], []
        for line in lines + [""]:          # trailing "" flushes the last run
            if line.lstrip().startswith("|"):
                run.append(line)
            else:
                if len(run) <= max_lines:
                    kept.extend(run)
                run = []
                kept.append(line)
        out.append("\n".join(kept[:-1]))   # remove the sentinel line
    return out


def drop_references(texts):
    """Return (kept_texts, found), with everything from the last
    references heading onward removed."""
    cut_page, cut_pos = None, None
    for i, t in enumerate(texts):
        for m in REF_PAT.finditer(t):
            cut_page, cut_pos = i, m.start()  # last match wins
    if cut_page is None:
        return texts, False
    return texts[:cut_page] + [texts[cut_page][:cut_pos]], True

def _norm(line):
    line = re.sub(r'[*_#]', '', line)
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

DROP_HEADINGS = (
    "acknowledg", "funding", "conflict of interest", "conflicts of interest",
    "declaration of competing", "competing interests", "author contributions",
    "credit authorship", "ethics statement", "supplementary", "disclosure",
    "recommendations for future research", "inclusion and exclusion criteria",
    "search strategy", "protocol and registration", "data extraction",
    "quality appraisal", "study selection", "additional file",
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

# --- page marker helpers (extract.py writes "[page N]" before each page) ---
def split_pages(md):
    parts = re.split(r'^\[page (\d+)\]\n', md, flags=re.M)
    nums = parts[1::2]
    texts = [t.rstrip("\n") for t in parts[2::2]]
    return nums, texts

def join_pages(nums, texts):
    return "\n\n".join(f"[page {n}]\n{t}" for n, t in zip(nums, texts))

# --- main ---
ap = argparse.ArgumentParser()
ap.add_argument("folder")
ap.add_argument("--only", help="process just this file (filename stem)")
ap.add_argument("--force", action="store_true", help="overwrite existing output (requires --only)")
args = ap.parse_args()

if args.force and not args.only:
    sys.exit("--force requires --only <file> so a whole folder of hand edits can't be overwritten.")

SRC = In_MD / args.folder
DST = Out_MD / args.folder
if not SRC.is_dir():
    sys.exit(f"Folder not found: {SRC}")

no_refs = []
for md in sorted(SRC.rglob("*.md")):
    if args.only and md.stem != args.only:
        continue
    out = DST / md.relative_to(SRC)
    if out.exists() and not args.force:
        continue
    out.parent.mkdir(parents=True, exist_ok=True)

    nums, texts = split_pages(md.read_text(encoding="utf-8"))
    texts = strip_running_headers(texts)
    texts = drop_sections(texts)
    texts = drop_big_tables(texts)
    texts, found = drop_references(texts)
    if not found:
        no_refs.append(md)
    out.write_text(join_pages(nums, texts), encoding="utf-8")
    print(f"cleaned: {md.relative_to(SRC)}")

if no_refs:
    print(f"\n{len(no_refs)} files had no references heading (check by hand):")
    for md in no_refs:
        print(f"  {md}")