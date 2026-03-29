"""Keep only the most important sentences per chunk (keyword trim or optional LLM)."""

from __future__ import annotations

import re

from langchain_core.documents import Document

# Target size from STEP 6 (e.g. 2–3 key sentences per chunk).
MAX_SENTENCES_PER_CHUNK = 3

_WORD = re.compile(r"[a-zA-Z][a-zA-Z0-9\-']*")

_STOPWORDS = frozenset(
    """
    a an the and or but if in on at to for of as is was are were be been being
    it its this that these those with from by not no so do does did has have had
    what which who whom how when where why can could should would will may might
    about into through over after before between under again further then once here
    there all each both few more most other some such only own same than too very
    just also now your our their my any""".split()
)


def _split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def _query_terms(query: str) -> set[str]:
    words = _WORD.findall(query.lower())
    return {w for w in words if len(w) > 2 and w not in _STOPWORDS}


def _sentence_score(sentence: str, terms: set[str]) -> int:
    if not terms:
        return 0
    sent_words = set(_WORD.findall(sentence.lower()))
    return len(terms & sent_words)


def compress_chunk_text(
    query: str,
    text: str,
    *,
    max_sentences: int = MAX_SENTENCES_PER_CHUNK,
) -> str:
    """
    Keyword-based trim: rank sentences by overlap with query terms, keep the top
    few in original reading order. If nothing matches, keep the first sentences
    so context is not emptied.
    """
    sentences = _split_sentences(text)
    if len(sentences) <= max_sentences:
        return text.strip()

    terms = _query_terms(query)
    ranked = sorted(
        range(len(sentences)),
        key=lambda i: (-_sentence_score(sentences[i], terms), i),
    )
    chosen = sorted(ranked[:max_sentences])
    return " ".join(sentences[i] for i in chosen)


def _compress_chunk_llm(
    query: str,
    text: str,
    *,
    max_sentences: int,
) -> str:
    from langchain_openai.chat_models import ChatOpenAI
    from pydantic import BaseModel, Field

    class KeySentences(BaseModel):
        sentences: list[str] = Field(
            description="Verbatim or lightly cleaned sentences from the chunk that best help answer the query",
            max_length=max(4, max_sentences + 1),
        )

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    runnable = llm.with_structured_output(KeySentences)
    prompt = f"""You extract only the most important sentences from a retrieval chunk for answering the user query.
Return at most {max_sentences} sentences. Prefer copying exact sentences from the chunk; drop filler and repetition.

User query:
{query}

Chunk:
{text[:12000]}"""
    result = runnable.invoke(prompt)
    picked = [s.strip() for s in result.sentences if s.strip()][:max_sentences]
    return " ".join(picked) if picked else compress_chunk_text(query, text, max_sentences=max_sentences)


def compress_documents(
    query: str,
    documents: list[Document],
    *,
    max_sentences_per_chunk: int = MAX_SENTENCES_PER_CHUNK,
    use_llm: bool = False,
) -> list[Document]:
    """Return new documents with shorter ``page_content``; metadata is preserved."""
    if not documents:
        return []

    out: list[Document] = []
    for doc in documents:
        text = doc.page_content
        if use_llm:
            new_text = _compress_chunk_llm(
                query, text, max_sentences=max_sentences_per_chunk
            )
        else:
            new_text = compress_chunk_text(
                query, text, max_sentences=max_sentences_per_chunk
            )
        meta = {**(doc.metadata or {})}
        out.append(Document(page_content=new_text, metadata=meta))
    return out
