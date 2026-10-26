"""Persistent Chroma storage, token-aware chunking, and pantry reranking."""
from __future__ import annotations

import json
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
from tokenizers import Tokenizer

from recipes import Recipe, pantry_match, unmapped_ingredients, main_pantry
from categories import query_categories, matches_category
from filters import validate_filters, matches_filters

ROOT = Path(__file__).resolve().parent


def rank_matches(candidates: list[dict], has_pantry: bool) -> list[dict]:
    def key(item):
        semantic = (item["distance"], item["recipe"].id)
        if not has_pantry:
            return semantic
        # Unmapped ingredient lines may require shopping too. Do not reward
        # incomplete extraction by treating those ingredients as already owned.
        uncertain = len(item["unverified"])
        extra = len(item["missing"]) + uncertain
        total = len(item["have"]) + extra
        coverage = len(item["have"]) / total if total else 0
        return (not bool(item["have"]), extra, -coverage, *semantic)
    return sorted(candidates, key=key)


class RecipeStore:
    def __init__(self, path: Path = ROOT / "chroma_store"):
        # Explicit cache location keeps downloads inside the project.
        self.embedding = ONNXMiniLM_L6_V2(preferred_providers=["CPUExecutionProvider"])
        self.embedding.DOWNLOAD_PATH = ROOT / ".cache/all-MiniLM-L6-v2"
        self.client = chromadb.PersistentClient(path=str(Path(path).resolve()))
        self.collection = self.client.get_or_create_collection(
            name="pantry-recipes-v1", embedding_function=self.embedding,
            configuration={"hnsw": {"space": "cosine"}},
        )
        self._tokenizer = None

    @property
    def tokenizer(self):
        if self._tokenizer is None:
            # First call downloads Chroma's model with its built-in checksum check.
            self.embedding(["Recipe search"])
            self._tokenizer = Tokenizer.from_str(self.embedding.tokenizer.to_str())
            self._tokenizer.no_truncation()
            self._tokenizer.no_padding()
        return self._tokenizer

    def chunks(self, text: str) -> list[str]:
        encoding = self.tokenizer.encode(text, add_special_tokens=False)
        chunks = []
        for start in range(0, len(encoding.ids), 208):
            end = min(start + 240, len(encoding.ids))
            left, right = encoding.offsets[start][0], encoding.offsets[end - 1][1]
            chunk = text[left:right]
            # A window may start inside a word. Check its re-tokenized size too.
            if len(self.tokenizer.encode(chunk).ids) > 256:
                raise ValueError("Chunk exceeds embedding token limit")
            chunks.append(chunk)
            if end == len(encoding.ids):
                break
        return chunks

    def index(self, recipes: list[Recipe]) -> None:
        records = []
        for recipe in recipes:
            payload = json.dumps(recipe.to_dict(), ensure_ascii=False)
            for index, chunk in enumerate(self.chunks(recipe.search_text())):
                records.append((f"{recipe.id}:{index}", chunk,
                                {"recipe_id": recipe.id, "recipe": payload}))
        # Upsert makes interrupted imports safe to repeat without duplicate IDs.
        for start in range(0, len(records), 64):
            batch = records[start:start + 64]
            self.collection.upsert(ids=[x[0] for x in batch], documents=[x[1] for x in batch],
                                   metadatas=[x[2] for x in batch])
            print(f"Indexed {min(start + 64, len(records))}/{len(records)} chunks", flush=True)

    def count(self) -> int:
        metadata = self.collection.get(include=["metadatas"])["metadatas"] or []
        return len({item["recipe_id"] for item in metadata})

    def search(self, need: str, pantry: list[str], limit=3, max_distance=0.70, filters=None) -> list[dict]:
        filters = validate_filters(filters)
        pantry = main_pantry(pantry)
        wanted, excluded = query_categories(need)
        if not need.strip():
            raise ValueError("Describe the meal you want")
        if len(self.tokenizer.encode(need).ids) > 256:
            raise ValueError("Please shorten your meal request to about one sentence")
        count = self.collection.count()
        if not count:
            return []
        # This local corpus is small. Consider every chunk so practical recipes
        # are not lost behind an arbitrary top-20 semantic candidate cutoff.
        raw = self.collection.query(query_texts=[need], n_results=count,
                                    include=["metadatas", "distances", "documents"])
        candidates, seen = [], set()
        for metadata, distance, excerpt in zip(raw["metadatas"][0], raw["distances"][0], raw["documents"][0]):
            recipe = Recipe(**json.loads(metadata["recipe"]))
            if recipe.id in seen or distance > max_distance:
                continue
            seen.add(recipe.id)
            if not matches_category(recipe, wanted, excluded) or not matches_filters(recipe, filters):
                continue
            have, missing = pantry_match(recipe, pantry)
            candidates.append(dict(recipe=recipe, have=have, missing=missing,
                                   unverified=unmapped_ingredients(recipe),
                                   distance=distance, excerpt=excerpt))
        return rank_matches(candidates, bool(pantry))[:limit]
