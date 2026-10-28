"""
Step 3: chunk one joint's articles into JSONL for embedding.

Usage:
    python chunk.py elbow                 # chunks every article in markdown/elbow/
    python chunk.py elbow --sample 8      # stats + 8 random chunks from the result
"""
import json
import random
import re
import sys
from pathlib import Path
from transformers import AutoTokenizer
from paths import CLEAN_MD, METADATA, CHUNKS


BASE = Path(__file__).resolve().parent
MARKDOWN_ROOT = CLEAN_MD    # contains one subfolder per joint
METADATA_DIR =  METADATA      # one <joint>.json per joint, covering that joint's articles
OUTPUT_DIR =  CHUNKS   # every joint's .jsonl ends up here

MARKDOWN_ROOT, METADATA_DIR, OUTPUT_DIR = Path(MARKDOWN_ROOT), Path(METADATA_DIR), Path(OUTPUT_DIR)

MAX_TOK = 420        # hard-ish ceiling (only a single table/sentence can exceed it)
MIN_MERGE = 150      # sections smaller than this get merged into the next one
OVERLAP_TOK = 60     # tail of previous chunk repeated at start of the next (text only)

#originally usedd tiktoken for higher speeds but the embedding model BAAI/bge-small-en-v1.5 works better with a huggingface tokenizer as well
_tok = AutoTokenizer.from_pretrained("BAAI/bge-small-en-v1.5", model_max_length=1_000_000)


def ntok(s):
    return len(_tok.encode(s, add_special_tokens=False))

#regexes for finding where pages, headings, and tables are in the text for chunking
PAGE_RE = re.compile(r"\[page\s+(\d+)\]", re.I)
HEAD_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
TABLE_RE = re.compile(r"^\s*\|")
SENT_RE = re.compile(r"(?<=[.!?])\s+")
LIMIT = MAX_TOK - OVERLAP_TOK  # paragraph pieces stay this small so piece + overlap fits


# Takes a text string and returns a list of blocks, where each block is a dict with keys:
# - kind: "heading", "para", or "table"
# - text: the text of the block
# - page_start: the page number where the block starts
# - page_end: the page number where the block ends
def parse_blocks(text):
    blocks, page = [], 1
    buf, kind, p0 = [], None, 1

    def flush():
        nonlocal buf, kind
        if buf:
            blocks.append({"kind": kind, "text": "\n".join(buf).strip(),
                           "page_start": p0, "page_end": page})
        buf, kind = [], None

    for line in text.splitlines():
        m = PAGE_RE.search(line)
        if m:
            page = int(m.group(1))
            line = PAGE_RE.sub("", line).rstrip()
            if not line.strip():
                continue  # marker on its own line; a paragraph in progress just continues
        if not line.strip():
            flush()
            continue
        h = HEAD_RE.match(line)
        if h:
            flush()
            blocks.append({"kind": "heading", "level": len(h.group(1)), "text": h.group(2),
                           "page_start": page, "page_end": page})
            continue
        want = "table" if TABLE_RE.match(line) else "para"
        if kind and kind != want:
            flush()
        if not buf:
            kind, p0 = want, page
        buf.append(line)
    flush()
    return blocks


#takes the list of blocks and returns a list of sections
#the sections are determined by the headings in the blocks, and each section contains a list of blocks that belong to it
#the stack keeps track of the current heading hierarchy, so that each section has a heading that reflects its position in the document structure
def to_sections(blocks):
    secs, stack = [], []
    cur = {"heading": "", "blocks": []}
    for b in blocks:
        if b["kind"] == "heading":
            secs.append(cur)
            stack = [h for h in stack if h[0] < b["level"]] + [(b["level"], b["text"])]
            cur = {"heading": " > ".join(t for _, t in stack), "blocks": []}
        else:
            cur["blocks"].append(b)
    secs.append(cur)
    return [s for s in secs if s["blocks"]]

#takes a list of sections and merges small sections into the next one 
#this is to make sure there are no sections that are too small, which could lead to chunks that are too small and not useful for embedding
#places the heading of the small section as a paragraph in the next section, so that the context is preserved
def merge_small(secs):
    out, cur = [], None
    for s in secs:
        if cur is None:
            cur = {"heading": s["heading"], "blocks": list(s["blocks"])}
        else:
            title = s["heading"].split(" > ")[-1]
            first = s["blocks"][0]
            if title:
                cur["blocks"].append({"kind": "para", "text": title,
                                      "page_start": first["page_start"], "page_end": first["page_start"]})
            cur["blocks"] += s["blocks"]
            cur["heading"] = s["heading"]  # label the chunk by the substantive (later) section
        if sum(ntok(b["text"]) for b in cur["blocks"]) >= MIN_MERGE:
            out.append(cur)
            cur = None
    if cur:
        out.append(cur)
    return out


# ---------- 3. size-split within a section ----------
def split_long_para(b):
    """Break an over-long paragraph on sentence boundaries. Tables are never touched."""
    if b["kind"] == "table" or ntok(b["text"]) <= LIMIT:
        return [b]
    pieces, cur = [], []
    for s in SENT_RE.split(b["text"]):
        if cur and ntok(" ".join(cur + [s])) > LIMIT:
            pieces.append(" ".join(cur))
            cur = []
        cur.append(s)
    if cur:
        pieces.append(" ".join(cur))
    return [{**b, "text": p} for p in pieces]

# Creates the overlap for the chunks so that the end of one chunk is repeated at the start of the next chunk, up to a maximum number of tokens defined by OVERLAP_TOK
# Done so that the context is preserved when embedding the chunks, and to avoid losing information at the boundaries of the chunks
def overlap_tail(blocks):
    last = blocks[-1]
    if last["kind"] == "table":
        return []
    tail = []
    for s in reversed(SENT_RE.split(last["text"])):
        if ntok(" ".join([s] + tail)) > OVERLAP_TOK:
            break
        tail.insert(0, s)
    if not tail:
        return []
    return [{"kind": "overlap", "text": " ".join(tail),
             "page_start": last["page_end"], "page_end": last["page_end"]}]

#checks to see if the current chunk is too long, and if so, it will create a new chunk and add the overlap from the previous chunk to the new chunk
def pack(blocks):
    chunks, cur, cur_t = [], [], 0
    for b in (x for blk in blocks for x in split_long_para(blk)):
        t = ntok(b["text"])
        if any(x["kind"] != "overlap" for x in cur) and cur_t + t > MAX_TOK:
            chunks.append(cur)
            cur = overlap_tail(cur)
            cur_t = sum(ntok(x["text"]) for x in cur)
        cur.append(b)
        cur_t += t
    if cur:
        chunks.append(cur)
    return chunks

#This is the pipline to go through the chunking process, taking the source_id, text, and metadata as input and returning a list of chunked records
#It runs the text through the parsing, sectioning, merging, and packing functions to create the final chunks, which are then returned as a list of dictionaries with the relevant metadata and chunk information
def chunk_document(source_id, text, meta):
    recs = []
    blocks = parse_blocks(text)
    # drop tables too big to embed whole; small tables (e.g. ROM norms) are kept
    blocks = [b for b in blocks if not (b["kind"] == "table" and ntok(b["text"]) > LIMIT)]
    for sec in merge_small(to_sections(blocks)):
        for blocks in pack(sec["blocks"]):
            body = "\n\n".join(b["text"] for b in blocks)
            recs.append({
                "chunk_id": None,
                "text": body,
                "token_count": ntok(body),
                "has_table": any(b["kind"] == "table" for b in blocks),
                "heading": sec["heading"],
                "page": blocks[0]["page_start"],
                "page_end": blocks[-1]["page_end"],
                "source_id": source_id,
                "title": meta.get("title"),
                "year": meta.get("year"),
                "study_type": meta.get("study_type"),
                "journal": meta.get("journal"),
                "doi": meta.get("doi"),
                "authors": "; ".join(meta.get("authors", [])),
                "keywords": ", ".join(meta.get("keywords", [])),
            })
    for i, r in enumerate(recs):
        r["chunk_index"] = i
        r["chunk_id"] = f"{source_id}-{i:04d}"
    return recs


def load_metadata(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        lists = [v for v in data.values() if isinstance(v, list)]
        if len(lists) == 1:
            data = lists[0]
    index = {}
    if isinstance(data, list):
        for m in data:
            for key in (m.get("source_id"), m.get("markdown_path")):
                if key:
                    index[Path(key).stem] = m
    else:
        for key, m in data.items():
            index[Path(key).stem] = m
    return index

# makes sure that if their is no metadata for a source_id, it will still chunk the document and return the chunks with None for the metadata fields
def run(joint):
    src = MARKDOWN_ROOT / joint
    if not src.is_dir():
        sys.exit(f"No folder {src}. Available: {sorted(p.name for p in MARKDOWN_ROOT.iterdir() if p.is_dir())}")
    mf = METADATA_DIR / f"{joint}.json"
    if not mf.exists():
        sys.exit(f"No metadata file {mf}")
    meta_all = load_metadata(mf)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)      # change 1: parents=True
    out_path = OUTPUT_DIR / f"{joint}.jsonl"
    n = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for p in sorted(src.glob("*")):
            if p.suffix not in {".md", ".txt"}:
                continue
            sid = p.stem
            meta = meta_all.get(sid)
            if not meta:
                print(f"WARNING: no entry for '{sid}' in {mf.name}. Entries are: {sorted(meta_all)}", file=sys.stderr)
                meta = {}
            elif meta.get("reviewed") is False:        # change 2: flag unreviewed metadata
                print(f"NOTE: metadata for '{sid}' not reviewed yet", file=sys.stderr)
            # change 3: no more meta = {"topic": joint, **meta}
            source_id = meta.get("source_id") or f"{joint}/{sid}"   # change 4: joint-safe fallback
            recs = chunk_document(source_id, p.read_text(encoding="utf-8"), meta)
            print(f"  {sid}: {len(recs)} chunks")
            for r in recs:
                r["joint"] = joint
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
                n += 1
    print(f"wrote {n} chunks to {out_path}")


# ---------- 5. eyeball + sanity checks ----------
def sample(path, k):
    recs = [json.loads(l) for l in open(path, encoding="utf-8")]
    if not recs:
        sys.exit("no chunks in file")
    toks = sorted(r["token_count"] for r in recs)
    print(f"{len(recs)} chunks | tokens min/median/max = {toks[0]}/{toks[len(toks)//2]}/{toks[-1]}")
    print(f"over {MAX_TOK}: {sum(t > MAX_TOK for t in toks)} (should be table-only) | "
          f"under 100: {sum(t < 100 for t in toks)} | with tables: {sum(r['has_table'] for r in recs)}")
    big = [r for r in recs if r["token_count"] > MAX_TOK and not r["has_table"]]
    print(f"oversized NON-table chunks (bug): {len(big)}")
    no_meta = [r for r in recs if not all(r[k] is not None for k in ("title", "year", "joint", "study_type"))]
    print(f"chunks with missing metadata: {len(no_meta)}")
    for r in random.sample(recs, min(k, len(recs))):
        print("\n" + "=" * 80)
        print({k2: r[k2] for k2 in r if k2 != "text"})
        print("-" * 80)
        print(r["text"])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python chunk.py <joint> [--sample N]")
    joint = sys.argv[1]
    if len(sys.argv) >= 3 and sys.argv[2] == "--sample":
        sample(OUTPUT_DIR / f"{joint}.jsonl", int(sys.argv[3]) if len(sys.argv) > 3 else 8)
    else:
        run(joint)