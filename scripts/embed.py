import chromadb
from sentence_transformers import SentenceTransformer
import json
from pathlib import Path

#Using this hugging face model because of speed over larger models and less intesive hardwear usage 
# Tradeoff: 512-token input cap, so chunks must stay under ~450 tokens
# (chunker is configured to match; see MAX_TOK in chunk.py).
model = SentenceTransformer("BAAI/bge-small-en-v1.5")
client = chromadb.PersistentClient(path="./chroma_db")

#using cosine distence to measure the distence between vectors
collection = client.get_or_create_collection(
    name="papers",
    metadata={"hnsw:space": "cosine"},
)

META_FIELDS = [
    "source_id", "title", "year", "joint", "study_type", "journal", "doi",
    "authors", "keywords", "heading", "page", "page_end", "has_table", "token_count",
]

def clean_meta(rec):
    """Chroma rejects None values and list values."""
    out = {}
    for k in META_FIELDS:
        v = rec.get(k)
        if v is None:
            continue
        out[k] = "; ".join(map(str, v)) if isinstance(v, list) else v
    return out

def embed_text(rec):
    """Prepend title and the innermost heading so each chunk carries its context."""
    last_heading = (rec.get("heading") or "").split(" > ")[-1]
    parts = [rec.get("title"), last_heading]
    prefix = " | ".join(p for p in parts if p)
    return f"{prefix}\n{rec['text']}" if prefix else rec["text"]

def embed_and_store(recs, batch_size=64):
    # Remove old chunks for every paper being re-embedded
    for joint, sid in {(r["joint"], r["source_id"]) for r in recs}:
        collection.delete(where={"$and": [{"joint": joint}, {"source_id": sid}]})

    for i in range(0, len(recs), batch_size):
        batch = recs[i : i + batch_size]
        embeddings = model.encode(
            [embed_text(r) for r in batch],
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

        collection.upsert(
            ids=[r["chunk_id"] for r in batch],
            documents=[r["text"] for r in batch],   # store the clean text, not the prefixed one
            embeddings=embeddings,
            metadatas=[clean_meta(r) for r in batch],
        )
    print(f"Collection now has {collection.count()} chunks.")


QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def search(query, k=5, joint=None):
    where = {"joint": {"$in": [joint, "general"]}} if joint else None
    q_emb = model.encode(QUERY_PREFIX + query, normalize_embeddings=True).tolist()
    res = collection.query(query_embeddings=[q_emb], n_results=k, where=where)
    hits = list(zip(res["documents"][0], res["metadatas"][0], res["distances"][0]))
    for doc, m, dist in hits:
        print(f"[{dist:.3f}] {m.get('title')} ({m.get('year')}), p.{m.get('page')} - {m.get('heading')}")
        print(doc[:200], "\n")
    return hits


def load_chunks(chunk_dir="data/chunks"):
    recs = []
    for path in sorted(Path(chunk_dir).glob("*.jsonl")):
        with open(path, encoding="utf-8") as f:
            recs.extend(json.loads(line) for line in f)
    return recs

if __name__ == "__main__":
    # 1. Load chunks from every joint (including general)
    recs = load_chunks()
    print(f"Loaded {len(recs)} chunks")

    # 2. Check for chunks over the model's 512-token limit
    lengths = [len(model.tokenizer(embed_text(r))["input_ids"]) for r in recs]
    print(f"max={max(lengths)}, over 512: {sum(l > 512 for l in lengths)}/{len(lengths)}")

    # 3. Embed everything
    embed_and_store(recs)
    print("Count:", collection.count())

    # 4. Test queries (joint-scoped, so this also tests the filter)
    search("how far can the foot bend upward", joint="ankle")
    search("how far can the foot bend upward", joint="hip")   # should show no ankle papers

    over = [r for r in recs if len(model.tokenizer(embed_text(r))["input_ids"]) > 512]
    tables = [r for r in over if r["has_table"]]
    chunker_bug = [r for r in over if not r["has_table"] and r["token_count"] > 450]
    prefix_overflow = [r for r in over if not r["has_table"] and r["token_count"] <= 450]
    print(len(tables), len(chunker_bug), len(prefix_overflow))