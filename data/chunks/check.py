import json
from collections import Counter

recs = [json.loads(l) for l in open("general.jsonl", encoding="utf-8")]

print("Smallest 10 chunks:")
for r in sorted(recs, key=lambda r: r["token_count"])[:10]:
    print(" ", r["chunk_id"], r["token_count"], "|", r["heading"], "|", repr(r["text"][:70]))

print("\nChunks per article with no heading:")
print(Counter(r["source_id"] for r in recs if not r["heading"]))

print("\nReference-like chunks:")
for r in recs:
    if "reference" in r["heading"].lower() or r["text"].count("doi.org") > 3:
        print(" ", r["chunk_id"], r["heading"])

print("\nChunks with a table:")
for r in recs:
    if r["has_table"]:
        print(" ", r["chunk_id"], r["token_count"])