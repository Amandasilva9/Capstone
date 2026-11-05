import re
import sys
import argparse
from pathlib import Path
from collections import Counter
from paths import RAW_MD, CLEAN_MD

"""The second step on the ingestion pipeline. 
   Running the file with the name of a joint makes it go through the entire folder with that joint name
   It takes all the raw markdowns and cleans them by removing refrences, tables, and sections from the articles that are not typically used
   It has the same commands as extract with --force to overwrite over the cleaned markdowns as well as --only for one file at a time
   The script is important to make sure that the chunks are not poluted with unhelpful text."""

In_MD = RAW_MD
Out_MD = CLEAN_MD

REF_PAT = re.compile(
    r'^[ \t]*[#*_ \t]*'                          # heading marks / bold / italics
    r'(?:(?:\d+|[IVXivx]+|[A-Za-z])[.)]?[ \t]+)?'  # other header possibilities 
    r'(?:references?(?: list)?|bibliography|works cited|literature cited|' # refrences 
    r'notes and references)' #more refrences
    r'[ \t]*[*_:]*[ \t]*$',
    re.I | re.M)

def drop_big_tables(texts, max_lines=12):
    """Removing the big tables as most tablse just have numbers.
    Numbers are not helpful for giving reasons and just pollute responses"""
    out = []
    for t in texts:
        lines, kept, run = t.split("\n"), [], []
        for line in lines + [""]:          # flushes the last run
            if line.lstrip().startswith("|"): # PDF tables when converted to markdown use the pipe symbol
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
    """When converting to markdown pdfs have recurring titles at the end of pages 
    This polutes chunks so gets removed. If the header repeates more then threshold they all get removed"""
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

DROP_HEADINGS = ( #List of possible headers that are not helpful to the AI 
    "acknowledg", "funding", "conflict of interest", "conflicts of interest",
    "declaration of competing", "competing interests", "author contributions",
    "credit authorship", "ethics statement", "supplementary", "disclosure",
    "recommendations for future research", "inclusion and exclusion criteria",
    "search strategy", "protocol and registration", "data extraction",
    "quality appraisal", "study selection", "additional file",
)

def _is_heading(line): #helper function to find if something is a header or not
    s = line.strip()
    return s.startswith('#') or (s.startswith('**') and s.endswith('**') and len(s) < 80)

def drop_sections(texts):
    """Drops the unhelp sections based on the Drop_headings"""
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