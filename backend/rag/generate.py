"""
generate.py -- step 6: retrieval-grounded answer generation.
"""
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the repo root (this file is backend/rag/generate.py)
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

import chromadb
from google import genai
from google.genai import errors, types
from sentence_transformers import SentenceTransformer

# ---- config (keep in sync with embed.py) ----
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")   # run from repo root, or set an absolute path
COLLECTION = "papers"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
MODELS = [m.strip() for m in os.getenv(
    "GEMINI_MODELS", "gemini-3.5-flash,gemini-3.1-flash-lite,gemini-2.5-flash"
).split(",")]
N_JOINT, N_GENERAL = 4, 2
MAX_DISTANCE = 0.55          # your best hits were ~0.24; tune with off-topic questions
REFUSAL = "I couldn't find support for that in the research articles I have."

_embedder = SentenceTransformer(EMBED_MODEL)
_collection = chromadb.PersistentClient(path=CHROMA_PATH).get_collection(COLLECTION)
_llm = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


# ---------------- retrieval ----------------
def retrieve(question: str, joint: str) -> list[dict]:
    """Top chunks for the joint plus a few from 'general', filtered by distance."""
    q_emb = _embedder.encode(QUERY_PREFIX + question, normalize_embeddings=True).tolist()
    chunks = []
    for joint_name, n in ((joint, N_JOINT), ("general", N_GENERAL)):
        res = _collection.query(
            query_embeddings=[q_emb],
            n_results=n,
            where={"joint": joint_name},         # your metadata key is "joint"
            include=["documents", "metadatas", "distances"],
        )
        for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
            if dist <= MAX_DISTANCE:
                chunks.append({"text": doc, "meta": meta, "distance": dist})
    chunks.sort(key=lambda c: c["distance"])
    return chunks


# ---------------- prompt assembly ----------------
def _cite_label(meta: dict) -> str:
    authors = meta.get("authors") or "Unknown authors"     # already "Grieve et al."
    year = meta.get("year", "n.d.")
    p, pe = meta.get("page"), meta.get("page_end")
    pages = f"p. {p}" if (pe is None or p == pe) else f"pp. {p}-{pe}"
    return f"{authors}, {year}, {pages}"


def _note_for(meta: dict) -> str | None:
    """Hand-written note wins; otherwise flag table chunks automatically."""
    if meta.get("notes"):
        return meta["notes"]
    if meta.get("has_table"):
        return "This chunk contains a table; extracted numbers may be misaligned or wrong."
    return None


def build_context(chunks: list[dict]) -> str:
    blocks = []
    for i, c in enumerate(chunks, 1):
        header = f"[S{i}] {_cite_label(c['meta'])}"
        if c["meta"].get("title"):
            header += f' | "{c["meta"]["title"]}"'
        block = f"{header}\n{c['text']}"
        note = _note_for(c["meta"])
        if note:
            block += f"\nEXTRACTION NOTE: {note}"
        blocks.append(block)
    return "\n\n---\n\n".join(blocks)


SYSTEM_PROMPT = f"""You are the explanation assistant for a mobility-measurement app. \
You explain why specific stretches were recommended, using ONLY the numbered SOURCES provided.

RULES
1. Every factual claim about physiology, stretching, or range of motion must end with a \
citation tag like [S2] (or [S1][S3]). Cite only IDs that appear in SOURCES. Never invent \
sources, authors, numbers, or study results.
2. If the SOURCES do not support an answer, or only partly support it, say so plainly. \
If they don't support it at all, reply exactly: "{REFUSAL}" Do not fill gaps from \
general knowledge.
3. Some sources carry an EXTRACTION NOTE (e.g., a table that extracted badly). Do not quote \
numbers from a flagged chunk as fact; tell the user that source's data may be unreliable, \
or leave it out.
4. The user's measured angle and the app's recommended exercises are context from the app, \
not research findings. Don't cite them, and don't claim a norm or cutoff unless a source states it.
5. Be concise (under ~200 words), plain language, no diagnosis.
6. Always end with: "This app is not a rehabilitation tool. If you're in pain, see a doctor, \
and talk to a healthcare specialist before using it if you have an injury."
"""


def build_user_prompt(question, joint, angle, exercises, context) -> str:
    return (
        f"JOINT: {joint}\n"
        f"MEASURED ANGLE: {angle}\n"
        f"RECOMMENDED EXERCISES (from the app's dictionary): {', '.join(exercises) or 'none'}\n\n"
        f"SOURCES:\n{context}\n\n"
        f"QUESTION: {question}"
    )


# ---------------- LLM call with model fallback ----------------
def _generate(contents: str) -> str:
    last_err = None
    for model in MODELS:
        for attempt in range(2):                     # one retry per model
            try:
                resp = _llm.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT, temperature=0.2),
                )
                return (resp.text or "").strip()
            except errors.APIError as e:
                last_err = e
                if e.code in (429, 500, 503, 504):   # overloaded / rate-limited
                    time.sleep(1.5 * (attempt + 1))
                    continue
                if e.code == 404:                    # model retired or misnamed
                    break
                raise
    raise RuntimeError(f"All Gemini models failed: {last_err}")


# ---------------- main entry ----------------
@dataclass
class Answer:
    text: str
    sources: list[dict] = field(default_factory=list)
    flagged: list[str] = field(default_factory=list)
    refused: bool = False
    reason: str = ""      # "no_chunks" | "model_refused" | "no_valid_citations"


def answer(question: str, joint: str, angle: float | None = None,
           exercises: list[str] | None = None) -> Answer:
    exercises = exercises or []
    chunks = retrieve(question, joint)
    if not chunks:
        return Answer(text=REFUSAL, refused=True, reason="no_chunks")

    text = _generate(build_user_prompt(question, joint, angle, exercises, build_context(chunks)))

    if text.startswith(REFUSAL):
        return Answer(text=text, refused=True, reason="model_refused")

    cited_ids = {int(n) for n in re.findall(r"\[S(\d+)\]", text)}
    valid = {i for i in cited_ids if 1 <= i <= len(chunks)}
    if not valid:
        print("DEBUG no valid citations; model said:\n", text)
        return Answer(text=REFUSAL, refused=True, reason="no_valid_citations")
    for bad in cited_ids - valid:
        text = text.replace(f"[S{bad}]", "")

    sources, flagged = [], []
    for i in sorted(valid):
        meta = chunks[i - 1]["meta"]
        sources.append({"id": f"S{i}", "citation": _cite_label(meta), "title": meta.get("title")})
        note = _note_for(meta)
        if note:
            flagged.append(f"S{i}: {note}")
    return Answer(text=text, sources=sources, flagged=flagged)


if __name__ == "__main__":
    a = answer("Why was a static calf stretch recommended?", joint="ankle",
               angle=8.0, exercises=["Wall calf stretch"])
    print(a.text, "\n", a.reason)
    for s in a.sources:
        print(f"  {s['id']}: {s['citation']}")
    if a.flagged:
        print("Flagged:", a.flagged)