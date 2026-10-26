"""Fetch a small reproducible RecipeNLG subset through the HF rows API."""
import argparse
import hashlib
import json
import random
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from recipes import Recipe

ROOT = Path(__file__).resolve().parent
DATASET = "SandhyaKilari/RecipeNLG_dataset"
# Sample windows across the corpus rather than downloading the 2+ GB CSV.
OFFSETS = [0, 10000, 50000, 100000, 200000, 400000, 600000, 800000, 1000000, 1200000]


def fetch_page(offset: int) -> tuple[list, str]:
    url = "https://datasets-server.huggingface.co/rows?" + urllib.parse.urlencode({
        "dataset": DATASET, "config": "default", "split": "train", "offset": offset, "length": 100,
    })
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "PantryPal-Educational/1.0"})
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = json.load(response)
            return payload["rows"], url
        except (OSError, ValueError, KeyError):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--output", type=Path, default=ROOT / "data/recipes_500.json")
    args = parser.parse_args()
    if not 1 <= args.limit <= 800:
        parser.error("Choose a limit from 1 to 800")
    if args.output.exists():
        print(f"Already exists: {args.output}. Keeping your existing subset.")
        return
    recipes, seen, urls, skipped = [], set(), [], 0
    for offset in OFFSETS:
        rows, url = fetch_page(offset)
        urls.append(url)
        for entry in rows:
            if entry.get("truncated_cells") or entry["row"].get("source") != "Gathered":
                skipped += 1
                continue
            try:
                recipe = Recipe.from_row(entry["row"])
            except (ValueError, TypeError):
                skipped += 1
                continue
            if recipe.id not in seen:
                recipes.append(recipe)
                seen.add(recipe.id)
        print(f"Fetched window at row {offset:,}: {len(recipes)} usable unique recipes", flush=True)
        # One extra window gives a small pool to shuffle before selection.
        if len(recipes) >= args.limit + 80:
            break
    if len(recipes) < args.limit:
        raise RuntimeError(f"Only {len(recipes)} usable recipes; no output was written")
    random.Random(42).shuffle(recipes)
    selected = recipes[:args.limit]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps([r.to_dict() for r in selected], ensure_ascii=False, indent=2) + "\n"
    temporary = args.output.with_suffix(".tmp")
    temporary.write_text(encoded, encoding="utf-8")
    temporary.replace(args.output)
    manifest = {
        "original_project": "https://recipenlg.cs.put.poznan.pl/",
        "mirror": f"https://huggingface.co/datasets/{DATASET}",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "Fixed 100-row windows; Gathered only; reject truncated/incomplete rows; content deduplication; shuffle seed 42. Not a uniform sample of the full corpus.",
        "requests": urls, "pool_size": len(recipes), "skipped": skipped,
        "count": len(selected), "bytes": len(encoded.encode()),
        "sha256": hashlib.sha256(encoded.encode()).hexdigest(),
        "terms": "Follow original RecipeNLG non-commercial research/educational terms, not the mirror's broader license label.",
        "recipe_ids": [r.id for r in selected],
    }
    args.output.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Saved {len(selected)} recipes ({len(encoded.encode()) / 1024:.0f} KB) to {args.output}")


if __name__ == "__main__":
    main()
