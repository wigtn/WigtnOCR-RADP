"""Dense retrievers — encode queries and chunks, return top-k by cosine.

BGE-M3 is the default (multilingual SOTA). Two more wrappers (multilingual-e5-large,
jina-embeddings-v3) are stubs for the Week-1 baseline grid (PHASE_1.4 / §5.3).
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np

from wigtnocr_radp.evaluation.types import Chunk, ChunkRetrievalResult, QAPair

if TYPE_CHECKING:  # avoid hard import of torch/transformers at module load
    from sentence_transformers import SentenceTransformer  # noqa: F401


logger = logging.getLogger("wigtnocr_radp.evaluation.retrievers")


class BaseRetriever(ABC):
    """Encode-then-rank retriever interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier (e.g. 'bge-m3') used in result tables and configs."""

    @abstractmethod
    def encode_documents(self, texts: Sequence[str]) -> np.ndarray:
        """Return shape (n, d) L2-normalized embedding matrix."""

    @abstractmethod
    def encode_queries(self, texts: Sequence[str]) -> np.ndarray:
        """Return shape (n, d) L2-normalized embedding matrix."""

    def index(self, chunks: Sequence[Chunk]) -> None:
        """Pre-compute and cache document embeddings."""
        self._chunks: list[Chunk] = list(chunks)
        if not self._chunks:
            self._doc_emb = np.zeros((0, 0), dtype=np.float32)
            return
        self._doc_emb = self.encode_documents([c.text for c in self._chunks])

    def search(self, qa_pairs: Sequence[QAPair], top_k: int) -> list[ChunkRetrievalResult]:
        """Return ranked chunks per query. Uses pre-indexed corpus."""
        if not hasattr(self, "_chunks") or not self._chunks:
            raise RuntimeError("Call index(chunks) before search().")
        if not qa_pairs:
            return []
        q_emb = self.encode_queries([qa.question for qa in qa_pairs])
        # Cosine = dot product on L2-normalized vectors
        sims = q_emb @ self._doc_emb.T  # (Q, N)
        results: list[ChunkRetrievalResult] = []
        top_k_eff = min(top_k, len(self._chunks))
        # argpartition + sort for top-k (fast even when N is large)
        for qi in range(sims.shape[0]):
            row = sims[qi]
            if top_k_eff >= len(row):
                idx = np.argsort(-row)
            else:
                part = np.argpartition(-row, top_k_eff)[:top_k_eff]
                idx = part[np.argsort(-row[part])]
            ranked = tuple((self._chunks[int(i)], float(row[int(i)])) for i in idx)
            results.append(ChunkRetrievalResult(qa_id=qa_pairs[qi].qa_id, ranked=ranked))
        return results


class BgeM3Retriever(BaseRetriever):
    """BGE-M3 (BAAI/bge-m3) via sentence-transformers.

    Multilingual (KR/EN/CN). 1024-dim dense embeddings. ~2GB on disk.
    CPU works (~1-2 min / 1000 docs). GPU recommended for baseline grid scale.
    """

    MODEL_ID = "BAAI/bge-m3"

    def __init__(
        self,
        device: str = "cpu",
        batch_size: int = 32,
        max_seq_length: int = 1024,
        cache_folder: str | None = None,
    ) -> None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading BGE-M3 on %s ...", device)
        self.model = SentenceTransformer(
            self.MODEL_ID,
            device=device,
            cache_folder=cache_folder,
        )
        self.model.max_seq_length = max_seq_length
        self.batch_size = batch_size
        self.device = device

    @property
    def name(self) -> str:
        return "bge-m3"

    def _encode(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.model.get_sentence_embedding_dimension()), dtype=np.float32)
        emb = self.model.encode(
            list(texts),
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=len(texts) >= 64,
        )
        return emb.astype(np.float32)

    def encode_documents(self, texts: Sequence[str]) -> np.ndarray:
        return self._encode(texts)

    def encode_queries(self, texts: Sequence[str]) -> np.ndarray:
        return self._encode(texts)


# --- multilingual-e5-large (PHASE_1.4 / §5.3) ------------------------------


class MultilingualE5LargeRetriever(BaseRetriever):
    """intfloat/multilingual-e5-large via sentence-transformers.

    e5 models require an instruction prefix: 'query: ' for queries and
    'passage: ' for documents. 1024-dim, multilingual.
    """

    MODEL_ID = "intfloat/multilingual-e5-large"

    def __init__(
        self,
        device: str = "cpu",
        batch_size: int = 32,
        max_seq_length: int = 512,
        cache_folder: str | None = None,
    ) -> None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading multilingual-e5-large on %s ...", device)
        self.model = SentenceTransformer(self.MODEL_ID, device=device, cache_folder=cache_folder)
        self.model.max_seq_length = max_seq_length
        self.batch_size = batch_size
        self.device = device

    @property
    def name(self) -> str:
        return "ml-e5-large"

    def _encode(self, texts: Sequence[str], prefix: str) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.model.get_sentence_embedding_dimension()), dtype=np.float32)
        emb = self.model.encode(
            [prefix + t for t in texts],
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=len(texts) >= 64,
        )
        return emb.astype(np.float32)

    def encode_documents(self, texts: Sequence[str]) -> np.ndarray:
        return self._encode(list(texts), "passage: ")

    def encode_queries(self, texts: Sequence[str]) -> np.ndarray:
        return self._encode(list(texts), "query: ")


# --- jina-embeddings-v3 (PHASE_1.4 / §5.3) ---------------------------------


class JinaV3Retriever(BaseRetriever):
    """jinaai/jina-embeddings-v3 via sentence-transformers (trust_remote_code).

    Task-specific adapters: 'retrieval.query' for queries, 'retrieval.passage'
    for documents. 1024-dim, multilingual.

    NOT USED — its remote code is incompatible with the pinned transformers 5.8
    and intermittently yields NaN embeddings (see memory: jina-v3-retriever-broken).
    Kept for the record; the 3rd RCPS retriever is MultilingualMpnetRetriever.
    """

    MODEL_ID = "jinaai/jina-embeddings-v3"

    def __init__(
        self,
        device: str = "cpu",
        batch_size: int = 16,
        cache_folder: str | None = None,
    ) -> None:
        from sentence_transformers import SentenceTransformer
        from transformers import PreTrainedModel

        # transformers 5.8 compat shim: jina-v3's bundled remote modeling code
        # predates `all_tied_weights_keys` (set per-instance in newer
        # transformers). Provide a class-level fallback so its custom model
        # loads — plumbing to run the PRD-specified retriever.
        if "all_tied_weights_keys" not in vars(PreTrainedModel):
            PreTrainedModel.all_tied_weights_keys = {}

        logger.info("Loading jina-embeddings-v3 on %s ...", device)
        self.model = SentenceTransformer(
            self.MODEL_ID, device=device, trust_remote_code=True, cache_folder=cache_folder
        )
        # Force fp32: without flash_attn jina-v3 falls back to a native attention
        # path that intermittently produces NaN embeddings in fp16/bf16.
        self.model = self.model.float()
        self.batch_size = batch_size
        self.device = device

    @property
    def name(self) -> str:
        return "jina-v3"

    def _encode(self, texts: Sequence[str], task: str) -> np.ndarray:
        if not texts:
            return np.zeros((0, 1024), dtype=np.float32)
        emb = self.model.encode(
            list(texts),
            task=task,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=len(texts) >= 64,
        )
        return emb.astype(np.float32)

    def encode_documents(self, texts: Sequence[str]) -> np.ndarray:
        return self._encode(texts, "retrieval.passage")

    def encode_queries(self, texts: Sequence[str]) -> np.ndarray:
        return self._encode(texts, "retrieval.query")


# --- Qwen3-Embedding-8B (PHASE_1.4 / §5.3) ---------------------------------


class Qwen3EmbeddingRetriever(BaseRetriever):
    """Qwen/Qwen3-Embedding-8B via sentence-transformers.

    A recent (2025) top-tier multilingual embedding model — the 3rd RCPS
    retriever, replacing jina-v3 (broken on transformers 5.8; see memory:
    jina-v3-retriever-broken). Standard Qwen3 architecture, no remote code.
    Queries use the model's instruction 'query' prompt; documents are encoded
    plain. Last-token pooling (handled by the sentence-transformers module).
    """

    MODEL_ID = "Qwen/Qwen3-Embedding-8B"

    def __init__(
        self,
        device: str = "cpu",
        batch_size: int = 8,
        max_seq_length: int = 1024,
        cache_folder: str | None = None,
    ) -> None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading Qwen3-Embedding-8B on %s ...", device)
        self.model = SentenceTransformer(
            self.MODEL_ID,
            device=device,
            cache_folder=cache_folder,
            model_kwargs={"dtype": "bfloat16"},
        )
        self.model.max_seq_length = max_seq_length
        self.batch_size = batch_size
        self.device = device

    @property
    def name(self) -> str:
        return "qwen3-emb-8b"

    def _encode(self, texts: Sequence[str], prompt_name: str | None = None) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.model.get_sentence_embedding_dimension()), dtype=np.float32)
        kwargs = {"prompt_name": prompt_name} if prompt_name else {}
        emb = self.model.encode(
            list(texts),
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=len(texts) >= 64,
            **kwargs,
        )
        return emb.astype(np.float32)

    def encode_documents(self, texts: Sequence[str]) -> np.ndarray:
        return self._encode(texts)

    def encode_queries(self, texts: Sequence[str]) -> np.ndarray:
        return self._encode(texts, prompt_name="query")


# --- Late Chunking (PHASE_1.5 / §5.3) --------------------------------------


class LateChunkingRetriever(BaseRetriever):
    """Late Chunking (Günther et al., 2024; arXiv:2409.04701).

    Chunk boundaries come from an external chunker, but each chunk's embedding
    is the mean of its token vectors taken from a single forward pass over the
    *whole page* — so chunk embeddings carry document context. Query and chunk
    embeddings both use mean pooling (kept consistent). Backbone: BGE-M3
    (the paper uses jina, which is broken here — see jina-v3-retriever-broken).
    """

    MODEL_ID = "BAAI/bge-m3"

    def __init__(
        self, device: str = "cpu", batch_size: int = 32, max_tokens: int = 8192,
        late: bool = True, cache_folder: str | None = None,
    ) -> None:
        import torch
        from sentence_transformers import SentenceTransformer

        logger.info("Loading Late-Chunking (BGE-M3, late=%s) on %s ...", late, device)
        st = SentenceTransformer(self.MODEL_ID, device=device, cache_folder=cache_folder)
        self.tokenizer = st.tokenizer
        self.auto_model = st[0].auto_model.eval()  # underlying HF transformer
        self.device = device
        self.batch_size = batch_size
        self.max_tokens = max_tokens
        self.late = late  # False = naive (each chunk embedded independently)
        self._torch = torch

    @property
    def name(self) -> str:
        return "late-chunk-bge" if self.late else "naive-bge-meanpool"

    def _mean_pool(self, texts: Sequence[str]) -> np.ndarray:
        """Standard mean-pooled embedding of each text."""
        torch = self._torch
        out: list[np.ndarray] = []
        for i in range(0, len(texts), self.batch_size):
            enc = self.tokenizer(list(texts[i : i + self.batch_size]), padding=True,
                                 truncation=True, max_length=self.max_tokens, return_tensors="pt")
            enc = {k: v.to(self.device) for k, v in enc.items()}
            with torch.inference_mode():
                hidden = self.auto_model(**enc).last_hidden_state  # (B, T, D)
            mask = enc["attention_mask"].unsqueeze(-1).to(hidden.dtype)
            pooled = (hidden * mask).sum(1) / mask.sum(1).clamp_min(1.0)
            pooled = torch.nn.functional.normalize(pooled, dim=-1)
            out.append(pooled.float().cpu().numpy())
        return np.concatenate(out).astype(np.float32) if out else np.zeros((0, 1024), np.float32)

    def encode_documents(self, texts: Sequence[str]) -> np.ndarray:  # fallback; index() overrides
        return self._mean_pool(list(texts))

    def encode_queries(self, texts: Sequence[str]) -> np.ndarray:
        return self._mean_pool(list(texts))

    def index(self, chunks: Sequence[Chunk]) -> None:
        if not self.late:  # naive: embed each chunk independently
            BaseRetriever.index(self, chunks)
            return
        torch = self._torch
        self._chunks = list(chunks)
        if not self._chunks:
            self._doc_emb = np.zeros((0, 1024), dtype=np.float32)
            return
        by_page: dict[str, list[Chunk]] = {}
        for c in self._chunks:
            by_page.setdefault(c.page_id, []).append(c)
        for cs in by_page.values():  # restore document order from chunk_id "...#i"
            cs.sort(key=lambda c: int(c.chunk_id.rsplit("#", 1)[-1]) if "#" in c.chunk_id else 0)

        emb: dict[str, np.ndarray] = {}
        for cs in by_page.values():
            full, spans = "", []
            for c in cs:
                spans.append((len(full), len(full) + len(c.text)))
                full += c.text + "\n"
            enc = self.tokenizer(full, return_offsets_mapping=True, truncation=True,
                                 max_length=self.max_tokens, return_tensors="pt")
            offsets = enc.pop("offset_mapping")[0].tolist()
            enc = {k: v.to(self.device) for k, v in enc.items()}
            with torch.inference_mode():
                hidden = self.auto_model(**enc).last_hidden_state[0]  # (T, D)
            for c, (cs0, cs1) in zip(cs, spans, strict=True):
                idx = [i for i, (o0, o1) in enumerate(offsets) if o1 > o0 and o0 < cs1 and o1 > cs0]
                v = hidden[idx].mean(0) if idx else hidden.mean(0)
                v = torch.nn.functional.normalize(v, dim=-1)
                emb[c.chunk_id] = v.float().cpu().numpy()
        self._doc_emb = np.stack([emb[c.chunk_id] for c in self._chunks]).astype(np.float32)


__all__: list[str] = [
    "BaseRetriever",
    "BgeM3Retriever",
    "MultilingualE5LargeRetriever",
    "Qwen3EmbeddingRetriever",
    "LateChunkingRetriever",
    "JinaV3Retriever",
]
