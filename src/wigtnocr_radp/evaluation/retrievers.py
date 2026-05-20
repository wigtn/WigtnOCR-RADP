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


__all__: list[str] = [
    "BaseRetriever",
    "BgeM3Retriever",
    "MultilingualE5LargeRetriever",
    "JinaV3Retriever",
]
