"""
Hybrid Multi-Channel Retriever with Reciprocal Rank Fusion (RRF)
Features:
- Pure-Python zero-dependency BM25 fallback for embedded NAS environments
- Sub-query punctuation normalization & deduplication
- Dense (Vector) + Sparse (BM25) multi-channel recall
- RRF rank fusion formula: score = sum(1 / (60 + rank))
- Dynamic relative threshold pruning: prunes chunks where score < TopScore * 0.9
"""

import re
import math
from typing import List, Dict, Any, Tuple
import numpy as np

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    class BM25Okapi:
        def __init__(self, corpus: List[List[str]], k1: float = 1.5, b: float = 0.75):
            self.corpus_size = len(corpus)
            self.k1 = k1
            self.b = b
            self.doc_lens = [len(doc) for doc in corpus]
            self.avgdl = sum(self.doc_lens) / max(1, self.corpus_size)
            self.doc_freqs: List[Dict[str, int]] = []
            self.idf: Dict[str, float] = {}
            self.nd: Dict[str, int] = {}
            for doc in corpus:
                frequencies: Dict[str, int] = {}
                for word in doc:
                    frequencies[word] = frequencies.get(word, 0) + 1
                self.doc_freqs.append(frequencies)
                for word in frequencies:
                    self.nd[word] = self.nd.get(word, 0) + 1
            for word, freq in self.nd.items():
                self.idf[word] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)

        def get_scores(self, query: List[str]) -> List[float]:
            scores = [0.0] * self.corpus_size
            for q in query:
                q_idf = self.idf.get(q, 0.0)
                if q_idf <= 0:
                    continue
                for i, doc_freq in enumerate(self.doc_freqs):
                    tf = doc_freq.get(q, 0)
                    if tf > 0:
                        doc_len = self.doc_lens[i]
                        denom = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
                        scores[i] += q_idf * (tf * (self.k1 + 1)) / denom
            return scores

from vaultmind.core.registry import RetrievedChunk

def tokenize(text: str) -> List[str]:
    # Extract clean words and sub-tokens
    return re.findall(r"\b\w+\b", text.lower())

class DeduplicatedHybridRetriever:
    def __init__(self, rrf_k: int = 60, relative_cutoff: float = 0.9):
        self.rrf_k = rrf_k
        self.relative_cutoff = relative_cutoff
        self.corpus: List[Dict[str, Any]] = []
        self.bm25: Any = None
        self.vocabulary: Dict[str, int] = {}
        self.tfidf_matrix: np.ndarray = None

    @staticmethod
    def normalize_query(query: str) -> str:
        """Strips punctuation, spaces, and lowercase for idempotent deduplication."""
        return re.sub(r"[\s？?！!。，,；;：:\"'“”]+", "", query).lower()

    @classmethod
    def dedupe_queries(cls, queries: List[str]) -> List[str]:
        seen = set()
        deduped = []
        for q in queries:
            key = cls.normalize_query(q)
            if key and key not in seen:
                seen.add(key)
                deduped.append(q.strip())
        return deduped

    def index_documents(self, documents: List[Dict[str, Any]]):
        """Indexes documents for sparse BM25 and TF-IDF cosine vector search."""
        self.corpus = documents
        tokenized_corpus = [tokenize(doc["content"]) for doc in documents]
        self.bm25 = BM25Okapi(tokenized_corpus) if tokenized_corpus else None

        # Build vocabulary
        vocab = {}
        for tokens in tokenized_corpus:
            for t in tokens:
                if t not in vocab:
                    vocab[t] = len(vocab)
        self.vocabulary = vocab

        # Build sparse TF-IDF vectors
        dim = max(1, len(vocab))
        matrix = []
        for tokens in tokenized_corpus:
            vec = np.zeros(dim)
            for t in tokens:
                if t in vocab:
                    vec[vocab[t]] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            matrix.append(vec)
        self.tfidf_matrix = np.array(matrix) if matrix else np.empty((0, dim))

    def _query_dense(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        if self.tfidf_matrix is None or len(self.tfidf_matrix) == 0:
            return []
        dim = self.tfidf_matrix.shape[1]
        qv = np.zeros(dim)
        for t in tokenize(query):
            if t in self.vocabulary:
                qv[self.vocabulary[t]] += 1.0
        norm = np.linalg.norm(qv)
        if norm == 0:
            return []
        qv = qv / norm

        scores = np.dot(self.tfidf_matrix, qv)
        ranked = np.argsort(scores)[::-1][:top_k]
        return [(idx, float(scores[idx])) for idx in ranked if scores[idx] > 0.05]

    def _query_sparse(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        if self.bm25 is None:
            return []
        tokens = tokenize(query)
        scores = self.bm25.get_scores(tokens)
        ranked = np.argsort(scores)[::-1][:top_k]
        return [(idx, float(scores[idx])) for idx in ranked if scores[idx] > 0.01]

    def retrieve(self, query: str, top_k: int = 10) -> List[RetrievedChunk]:
        """Executes hybrid retrieval with RRF fusion and relative score cutoff."""
        if not self.corpus:
            return []

        dense_hits = self._query_dense(query, top_k * 2)
        sparse_hits = self._query_sparse(query, top_k * 2)

        if not dense_hits and not sparse_hits:
            return []

        rrf_scores: Dict[int, float] = {}
        dense_score_map = {idx: s for idx, s in dense_hits}
        sparse_score_map = {idx: s for idx, s in sparse_hits}

        for rank, (idx, _) in enumerate(dense_hits):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + (1.0 / (self.rrf_k + rank + 1))

        for rank, (idx, _) in enumerate(sparse_hits):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + (1.0 / (self.rrf_k + rank + 1))

        if not rrf_scores:
            return []

        sorted_indices = sorted(rrf_scores.keys(), key=lambda i: rrf_scores[i], reverse=True)
        top_score = rrf_scores[sorted_indices[0]]
        cutoff_threshold = top_score * self.relative_cutoff

        results: List[RetrievedChunk] = []
        for idx in sorted_indices:
            score = rrf_scores[idx]
            if score < cutoff_threshold and len(results) >= 1:
                continue

            doc = self.corpus[idx]
            results.append(RetrievedChunk(
                doc_id=doc.get("id", f"doc_{idx}"),
                file_name=doc.get("file_name", "unknown"),
                page=doc.get("page", 1),
                content=doc.get("content", ""),
                dense_score=dense_score_map.get(idx, 0.0),
                sparse_score=sparse_score_map.get(idx, 0.0),
                rrf_score=score,
                metadata=doc.get("metadata", {})
            ))
            if len(results) >= top_k:
                break

        return results
