# debug_rag.py
from backend.rag.generate import _collection, retrieve, build_context, MAX_DISTANCE

# 1. What does the collection actually contain?
print("count:", _collection.count())
sample = _collection.get(limit=3, include=["metadatas"])
for m in sample["metadatas"]:
    print(m)
topics = {m.get("topic") for m in _collection.get(include=["metadatas"])["metadatas"]}
print("topic values:", topics)

# 2. Raw distances with NO filter and NO cutoff
import backend.rag.generate as g
q = g._embedder.encode(g.QUERY_PREFIX + "Why was a static calf stretch recommended?",
                       normalize_embeddings=True).tolist()
res = _collection.query(query_embeddings=[q], n_results=5,
                        include=["documents", "metadatas", "distances"])
for d, m in zip(res["distances"][0], res["metadatas"][0]):
    print(round(d, 3), m.get("topic"), m.get("title"))

# 3. Filtered retrieval, as generate.py does it
print("retrieved:", len(retrieve("Why was a static calf stretch recommended?", "ankle")))