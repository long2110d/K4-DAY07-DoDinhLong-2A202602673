from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv

from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    OPENAI_EMBEDDING_MODEL,
    OpenAIEmbedder,
    _mock_embed,
)
from src.models import Document
from src.store import EmbeddingStore

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# Keep this list at exactly five shared benchmark queries.
QUERIES = [
    {
        "question": "Khach hang co the huy giao dich trong khoang thoi gian nao?",
        "gold_answer": "Tu luc bam nut Dat hang den truoc thoi diem nhan hang thanh cong.",
        "gold_doc_ids": {"return-refund-guide", "return-refund-policy"},
        "evidence": "trước thời điểm nhận hàng thành công",
        "metadata_filter": None,
    },
    {
        "question": "Co nhung phuong thuc nao de huy giao dich?",
        "gold_answer": "Goi tong dai, gui email, nhan tin tren fanpage, hoac tu choi nhan hang va xac nhan huy khi giao hang.",
        "gold_doc_ids": {"return-refund-guide", "return-refund-policy"},
        "evidence": "Từ chối nhận hàng và xác nhận hủy",
        "metadata_filter": None,
    },
    {
        "question": "Thoi gian hoan tien la bao lau khi giao dich co van de?",
        "gold_answer": "Thoi gian hoan tien tu 7 den 14 ngay, khong tinh Thu bay va Chu nhat.",
        "gold_doc_ids": {"cellphones-app-regulation"},
        "evidence": "7 - 14 ngay",
        "metadata_filter": None,
    },
    {
        "question": "Voi giao dich tu 10.000.000 VNĐ tro len, nguoi mua can cung cap gi?",
        "gold_answer": "The vat ly va CCCD ban goc cua dung chu the de CellphoneS doi chieu truoc khi giao hang.",
        "gold_doc_ids": {"cellphones-app-regulation"},
        "evidence": "CCCD BẢN GỐC",
        "metadata_filter": {"audience": "buyer"},
    },
    {
        "question": "Chinh sach doi moi mien phi cho san pham keo dai bao nhieu ngay?",
        "gold_answer": "Khach hang co quyen doi moi mien phi len toi 30 ngay.",
        "gold_doc_ids": {"cellphones-app-regulation"},
        "evidence": "doi moi mien phi len toi 30 ngay",
        "metadata_filter": None,
    },
]


def parse_markdown(path: Path) -> tuple[dict[str, str], str]:
    """Read simple YAML frontmatter and the Markdown body without extra dependencies."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) != 3:
        return {}, text

    metadata: dict[str, str] = {}
    for line in parts[1].splitlines():
        match = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not match:
            continue
        value = match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1]
        metadata[match.group(1)] = value
    return metadata, parts[2].lstrip()


def load_documents(data_dir: Path, chunker: Callable[[str], list[str]]) -> list[Document]:
    documents: list[Document] = []
    for path in sorted(data_dir.glob("*.md")):
        metadata, content = parse_markdown(path)
        chunks = chunker(content)
        base_metadata = {**metadata, "doc_id": path.stem, "source_file": str(path)}
        documents.extend(
            Document(
                id=f"{path.stem}#{index}",
                content=chunk,
                metadata={**base_metadata},
            )
            for index, chunk in enumerate(chunks)
        )
    return documents


class CachedEmbedder:
    """Cache embeddings by content hash to avoid repeated API calls."""

    def __init__(self, embedder: Callable[[str], list[float]], cache_path: Path) -> None:
        self.embedder = embedder
        self.cache_path = cache_path
        try:
            self.cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            self.cache = {}
        self._backend_name = getattr(embedder, "_backend_name", embedder.__class__.__name__)

    def __call__(self, text: str) -> list[float]:
        key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if key not in self.cache:
            self.cache[key] = self.embedder(text)
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(json.dumps(self.cache), encoding="utf-8")
        return self.cache[key]


def choose_embedder(provider_override: str | None = None) -> CachedEmbedder:
    load_dotenv(override=False)
    provider = (provider_override or os.getenv(EMBEDDING_PROVIDER_ENV, "mock")).strip().lower()
    if provider == "openai":
        try:
            embedder = OpenAIEmbedder(
                model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL)
            )
        except Exception as error:
            print(f"OpenAI unavailable ({error}); using mock embeddings.")
            embedder = _mock_embed
    else:
        embedder = _mock_embed
    return CachedEmbedder(embedder, Path(".cache/bench_embeddings.json"))


def chunker_for(name: str, chunk_size: int) -> Callable[[str], list[str]]:
    if name == "fixed":
        return FixedSizeChunker(chunk_size=chunk_size).chunk
    if name == "sentence":
        return SentenceChunker().chunk
    return RecursiveChunker(chunk_size=chunk_size).chunk


def print_results(label: str, item: dict, results: list[dict]) -> int:
    evidence_found = any(item["evidence"] in result["content"] for result in results)
    gold_ranks = [
        rank
        for rank, result in enumerate(results, start=1)
        if result["metadata"].get("doc_id") in item["gold_doc_ids"]
    ]
    score = 0
    if evidence_found and gold_ranks:
        score = 2 if gold_ranks[0] == 1 else 1
    print(f"  {label}: evidence={'YES' if evidence_found else 'NO'} score={score}/2")
    for rank, result in enumerate(results, start=1):
        print(
            f"    {rank}. score={result['score']:.4f} "
            f"doc_id={result['metadata'].get('doc_id')} chunk_id={result['id']}"
        )
        preview = " ".join(result["content"].split())[:180]
        print(f"       {preview}...")
    return score


def run(data_dir: Path, chunk_size: int, strategy: str, provider: str | None) -> int:
    if not data_dir.is_dir():
        print(f"Data directory not found: {data_dir}")
        return 1

    chunker = chunker_for(strategy, chunk_size)
    documents = load_documents(data_dir, chunker)
    if not documents:
        print(f"No Markdown documents found in {data_dir}")
        return 1

    embedder = choose_embedder(provider)
    store = EmbeddingStore(collection_name="benchmark", embedding_fn=embedder)
    store.add_documents(documents)

    print(f"Data directory: {data_dir}")
    print(f"Chunker: {strategy} (chunk_size={chunk_size})")
    print(f"Embedding backend: {embedder._backend_name}")
    if "mock" in embedder._backend_name.lower():
        print("WARNING: mock embeddings are not semantic; retrieval scores are noisy.")
    print(f"Stored chunks: {store.get_collection_size()}")

    total = 0
    for index, item in enumerate(QUERIES, start=1):
        print(f"\n[{index}] {item['question']}")
        print(f"Gold: {item['gold_answer']}")
        filters = [item["metadata_filter"]]
        if item["metadata_filter"] is not None:
            filters = [None, item["metadata_filter"]]
        ab_signatures: dict[str, tuple[str, ...]] = {}
        for metadata_filter in filters:
            results = store.search_with_filter(
                item["question"], top_k=3, metadata_filter=metadata_filter
            )
            print(f"Filter: {metadata_filter or 'None'}")
            if item["metadata_filter"] is None:
                label = "retrieval"
            else:
                label = "unfiltered" if metadata_filter is None else "filtered"
            score = print_results(label, item, results)
            if item["metadata_filter"] is not None:
                ab_signatures[label] = tuple(result["id"] for result in results)
            if metadata_filter is not None or item["metadata_filter"] is None:
                total += score
        if len(ab_signatures) == 2 and ab_signatures["unfiltered"] == ab_signatures["filtered"]:
            print("  A/B WARNING: filter did not change top-3; this query may not require filtering.")
    print(f"Total score: {total}/10")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the five-query retrieval benchmark.")
    parser.add_argument(
        "data_dir",
        nargs="?",
        default="data/chinhsachdoitracellphones",
        help="Directory containing Markdown files with frontmatter.",
    )
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--strategy", choices=["fixed", "sentence", "recursive"], default="recursive")
    parser.add_argument("--provider", choices=["mock", "openai"], default=None)
    parser.add_argument("--all-strategies", action="store_true")
    args = parser.parse_args()
    strategies = ["fixed", "sentence", "recursive"] if args.all_strategies else [args.strategy]
    return max(
        run(Path(args.data_dir), args.chunk_size, strategy, args.provider)
        for strategy in strategies
    )


if __name__ == "__main__":
    raise SystemExit(main())
