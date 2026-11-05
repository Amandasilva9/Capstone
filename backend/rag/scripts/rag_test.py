"""
Demo: enter a joint and its measured angle, get 5 relevant chunks back.
Retrieval only pulls from the chosen joint's sources + "general" sources.

Usage:
    python rag_demo.py                 # interactive prompts
    python rag_demo.py knee 112        # or pass joint and angle directly
"""
import sys
import chromadb
from sentence_transformers import SentenceTransformer

# ---- Must match the embedding script ----
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "papers"
MODEL_NAME = "BAAI/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

N_JOINT = 3      # chunks from the specified joint
N_GENERAL = 2    # chunks from general info (total = 5)

# Rough normal ranges in degrees (placeholders: swap for your dictionary's thresholds).
# Keys must match your joint folder names.
NORMAL_RANGE = {
    "knee": (0, 135),
    "shoulder": (0, 180),
    "elbow": (0, 150),
    "hip": (0, 120),
    "ankle": (0, 20),
}


def describe_angle(joint, angle):
    """Turn a raw angle into words, since embeddings handle text better than numbers."""
    _, max_normal = NORMAL_RANGE[joint]
    pct = angle / max_normal
    if pct >= 0.9:
        return "full range of motion"
    if pct >= 0.7:
        return "mildly limited range of motion"
    return "significantly limited range of motion"


def get_chunks(collection, model, joint, angle):
    query = f"how to improve {joint} flexibility with {describe_angle(joint, angle)}, stretches and exercises"
    q_emb = model.encode(QUERY_PREFIX + query, normalize_embeddings=True).tolist()

    chunks = []
    for label, tag, n in (("joint", joint, N_JOINT), ("general", "general", N_GENERAL)):
        hits = collection.query(
            query_embeddings=[q_emb],
            n_results=n,
            where={"$and": [{"joint": tag}, {"has_table": False}]},  # skip raw table chunks
        )
        for doc, meta, dist in zip(hits["documents"][0], hits["metadatas"][0], hits["distances"][0]):
            chunks.append({"kind": label, "doc": doc, "meta": meta, "dist": dist})
    return query, chunks


def main():
    if len(sys.argv) == 3:
        joint, angle = sys.argv[1].lower(), float(sys.argv[2])
    else:
        joint = input(f"Joint {list(NORMAL_RANGE)}: ").strip().lower()
        angle = float(input("Angle (degrees): "))

    if joint not in NORMAL_RANGE:
        sys.exit(f"Unknown joint '{joint}'. Choose from {list(NORMAL_RANGE)}")

    model = SentenceTransformer(MODEL_NAME)
    collection = chromadb.PersistentClient(path=CHROMA_PATH).get_collection(COLLECTION_NAME)

    query, chunks = get_chunks(collection, model, joint, angle)

    print(f"\nJoint: {joint} | Angle: {angle} deg -> {describe_angle(joint, angle)}")
    print(f"Search query: {query}\n")
    for i, c in enumerate(chunks, 1):
        m = c["meta"]
        print(f"--- Chunk {i} [{c['kind']}] {m.get('title')} ({m.get('year')}), "
              f"p.{m.get('page')} | distance={c['dist']:.3f}")
        print(c["doc"][:500].strip())
        print()


if __name__ == "__main__":
    main()