# debug_rag.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import backend.generate as g   # use whatever import path worked for you

# ============ EDIT THESE, THEN RERUN ============
QUESTION = "What does dorsiflexion mean?"
JOINT = "ankle"
N_JOINT = 3
N_GENERAL = 3
MAX_DIST = 0.35   # or type a number, e.g. 0.45
DEDUPE = True                  # one chunk per paper; set False to see raw chunks
FETCH = 15                     # over-fetch so dedupe still leaves N papers
JOINT_KEY = "joint"
TITLE_KEY = "title"
# ================================================

col = g._collection
emb = g._embedder.encode(g.QUERY_PREFIX + QUESTION, normalize_embeddings=True).tolist()


def used_sources(joint_name, n):
    res = col.query(query_embeddings=[emb], n_results=FETCH, where={JOINT_KEY: joint_name},
                    include=["metadatas", "distances"])
    rows, seen = [], set()
    for d, m in zip(res["distances"][0], res["metadatas"][0]):
        title = m.get(TITLE_KEY)
        if DEDUPE and title in seen:
            continue                  # a closer chunk from this paper is already in
        seen.add(title)
        rows.append((d, m))
    rows = rows[:n]
    kept = [(d, m) for d, m in rows if d <= MAX_DIST]
    return kept, len(rows) - len(kept)


print(f"Q: {QUESTION}")
print(f"joint={JOINT}  N_JOINT={N_JOINT}  N_GENERAL={N_GENERAL}  MAX_DIST={MAX_DIST}  DEDUPE={DEDUPE}\n")

for label, name, n in ((f"JOINT ({JOINT})", JOINT, N_JOINT), ("GENERAL", "general", N_GENERAL)):
    kept, dropped = used_sources(name, n)
    print(f"{label}: {len(kept)} used, {dropped} dropped by cutoff")
    for d, m in kept:
        print(f"  {d:.3f}  {m.get(TITLE_KEY)}")
    print()