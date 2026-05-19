"""Dense retrievers — encode queries and chunks, return top-k by cosine.

BGE-M3 is the default (multilingual SOTA). Two more wrappers (multilingual-e5-large,
jina-embeddings-v3) are stubs for the Week-1 baseline grid (PHASE_1.4 / §5.3).
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

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


# --- Stubs for the baseline grid (PHASE_1.4) -------------------------------


class _NotYetImplementedRetriever(BaseRetriever):
    """Raises on use. Used to reserve the names in the public API."""

    _retriever_name: str = "_stub"

    @property
    def name(self) -> str:
        return self._retriever_name

    def encode_documents(self, texts: Sequence[str]) -> np.ndarray:
        raise NotImplementedError(f"{self.name} retriever is a Week 1.4 task")

    def encode_queries(self, texts: Sequence[str]) -> np.ndarray:
        raise NotImplementedError(f"{self.name} retriever is a Week 1.4 task")


class MultilingualE5LargeRetriever(_NotYetImplementedRetriever):
    _retriever_name = "ml-e5-large"


class JinaV3Retriever(_NotYetImplementedRetriever):
    _retriever_name = "jina-v3"


__all__: list[str] = ["BaseRetriever", "BgeM3Retriever", "MultilingualE5LargeRetriever", "JinaV3Retriever"]


def _unused(_: Any) -> None:
    pass
