import chromadb
from sentence_transformers import SentenceTransformer

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
    "source_id", "title", "year", "topic", "study_type", "journal", "doi",
    "authors", "keywords", "heading", "page", "page_end", "has_table", "token_count",
]

def clean_meta(rec):
    """Chroma rejects None values, so drop them."""
    return {k: rec[k] for k in META_FIELDS if rec.get(k) is not None}

def embed_text(rec):
    """Prepend heading/title so each chunk carries its context."""
    parts = [rec.get("title"), rec.get("heading")]
    prefix = " | ".join(p for p in parts if p)
    return f"{prefix}\n{rec['text']}" if prefix else rec["text"]

def embed_and_store(recs, batch_size=64):
    # Assign stable IDs: source_id + running index within that paper
    counters = {}
    for r in recs:
        n = counters.get(r["source_id"], 0)
        r["chunk_id"] = f'{r["source_id"]}::{n:04d}'
        counters[r["source_id"]] = n + 1

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

def search(query, k=5, where=None):
    q_emb = model.encode(QUERY_PREFIX + query, normalize_embeddings=True).tolist()
    res = collection.query(query_embeddings=[q_emb], n_results=k, where=where)
    for doc, m, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        print(f"[{dist:.3f}] {m.get('title')} ({m.get('year')}), p.{m.get('page')} - {m.get('heading')}")
        print(doc[:200], "\n")



if __name__ == "__main__":
    import json, glob

    # 1. Load chunks (change the glob back to "ankle.jsonl" if you want only that file for now)
    recs = []
    for path in sorted(glob.glob("data/chunks/*.jsonl")):
        with open(path) as f:
            recs.extend(json.loads(line) for line in f)
    print(f"Loaded {len(recs)} chunks")

    # 2. Check for chunks over the model's 512-token limit
    lengths = [len(model.tokenizer(embed_text(r))["input_ids"]) for r in recs]
    print(f"max={max(lengths)}, over 512: {sum(l > 512 for l in lengths)}/{len(lengths)}")

    # 3. Embed everything (no slice)
    embed_and_store(recs)
    print("Count:", collection.count())

    # 4. Test queries
    search("ankle range of motion")
    search("how far can the foot bend upward")