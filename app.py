"""Pantry Pal: run with no arguments for the interactive menu."""
from __future__ import annotations

import argparse
import csv
import json
import sys
import uuid
from pathlib import Path

from recipes import Recipe, unmapped_ingredients, assumed_seasonings
from store import ROOT, RecipeStore


def load_recipes(path: Path, limit: int) -> list[Recipe]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = csv.DictReader(handle) if path.suffix.lower() == ".csv" else json.load(handle)
        result, seen, skipped = [], set(), 0
        for row in rows:
            try:
                recipe = Recipe.from_row(row)
            except (ValueError, TypeError, AttributeError):
                skipped += 1
                continue
            if recipe.id not in seen:
                result.append(recipe)
                seen.add(recipe.id)
            if len(result) >= limit:
                break
    print(f"Loaded {len(result)} unique recipes; skipped {skipped} incomplete records.")
    if not result:
        raise ValueError("No usable recipes in this file")
    return result


def split_pantry(value: str) -> list[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


def print_results(results: list[dict]) -> None:
    if not results:
        print("No close matches. Try a more specific food-related request or add a recipe.")
        return
    for number, item in enumerate(results, 1):
        recipe = item["recipe"]
        print(f"\n{number}. {recipe.title}\n" + "─" * 50)
        print(f"You have ({len(item['have'])}): {', '.join(item['have']) or 'none matched'}")
        print(f"Missing named ingredients ({len(item['missing'])}): {', '.join(item['missing']) or 'none from the extracted names'}")
        print("Assumed seasonings: " + (", ".join(assumed_seasonings(recipe)) or "none listed"))
        unverified = unmapped_ingredients(recipe)
        if unverified:
            print("Also check these ingredients manually (not covered by extracted names):")
            for line in unverified:
                print(f"  ? {line}")
        print(f"Semantic distance: {item['distance']:.3f} (lower is closer)")
        if item["distance"] > 0.65:
            print("Loose semantic match — check whether this fits your request.")
        print("\nIngredients and quantities:")
        for line in recipe.ingredients:
            print(f"  • {line}")
        print("\nMethod:")
        for step, line in enumerate(recipe.directions, 1):
            print(f"  {step}. {line}")
        if recipe.link:
            print(f"Source: {recipe.link}")
    print("\nCheck the full ingredient list and quantities before cooking. Common oils, salt, pepper, sugar, spices and flavorings are assumed available.")


def required(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Please enter a value.")


def add_interactive(store: RecipeStore):
    title = required("Recipe name: ")
    description = input("Short description (optional): ").strip()
    print("Enter each ingredient as NAME | AMOUNT, e.g. rice | 1 cup. Blank line finishes.")
    names, ingredients = [], []
    while True:
        line = input("Ingredient: ").strip()
        if not line:
            if names:
                break
            print("Add at least one ingredient.")
            continue
        name, _, amount = line.partition("|")
        if not name.strip():
            print("Enter the ingredient name before |.")
            continue
        names.append(name.strip())
        ingredients.append(f"{amount.strip()} {name.strip()}".strip())
    print("Enter one cooking step at a time. Blank line finishes.")
    steps = []
    while True:
        line = input(f"Step {len(steps) + 1}: ").strip()
        if not line:
            if steps:
                break
            print("Add at least one step.")
            continue
        steps.append(line)
    recipe = Recipe("user-" + str(uuid.uuid4()), title, ingredients, names, steps, description)
    store.index([recipe])
    print(f'Saved "{title}". You can search for it now.')


def menu(store: RecipeStore):
    print("\nPANTRY PAL · What can you cook tonight?")
    print("Use English ingredient names and meal requests.")
    while True:
        print("\n1. Find a dish\n2. Add a recipe\n3. Show recipe count\n4. Import recipes\n5. Quit")
        choice = input("Choose 1–5: ").strip()
        try:
            if choice == "1":
                if not store.count():
                    print("Your collection is empty. Choose 4 to import recipes first.")
                    continue
                pantry = split_pantry(input("What ingredients do you have? (comma-separated): "))
                need = required("What kind of meal do you want? ")
                print_results(store.search(need, pantry))
            elif choice == "2":
                add_interactive(store)
            elif choice == "3":
                print(f"{store.count()} recipes stored persistently.")
            elif choice == "4":
                value = input("JSON/CSV path [data/recipes_500.json]: ").strip()
                path = Path(value).expanduser() if value else ROOT / "data/recipes_500.json"
                store.index(load_recipes(path, 500))
            elif choice == "5":
                print("See you next meal. Your recipes are saved.")
                return
            else:
                print("Please choose a number from 1 to 5.")
        except (ValueError, OSError) as error:
            print(f"Could not complete that action: {error}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=ROOT / "chroma_store")
    commands = parser.add_subparsers(dest="command")
    importer = commands.add_parser("import", help="Import RecipeNLG CSV or normalized JSON")
    importer.add_argument("path", type=Path)
    importer.add_argument("--limit", type=int, default=500)
    search = commands.add_parser("search", help="Search without the menu")
    search.add_argument("--need", required=True)
    search.add_argument("--pantry", default="")
    search.add_argument("--limit", type=int, default=3)
    search.add_argument("--max-distance", type=float, default=0.70)
    commands.add_parser("count")
    args = parser.parse_args()
    if getattr(args, "limit", 1) < 1:
        parser.error("--limit must be positive")
    if not 0 <= getattr(args, "max_distance", 0.70) <= 2:
        parser.error("--max-distance must be between 0 and 2")
    store = RecipeStore(args.store)
    if args.command == "import":
        store.index(load_recipes(args.path.expanduser(), args.limit))
        print(f"Ready: {store.count()} recipes.")
    elif args.command == "search":
        if not store.count():
            print("No recipes yet. Import your dataset first.")
        else:
            print_results(store.search(args.need, split_pantry(args.pantry), args.limit, args.max_distance))
    elif args.command == "count":
        print(f"{store.count()} recipes")
    else:
        menu(store)


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye. Previously saved recipes are kept.")
    except Exception as error:
        print(f"Error: {error}\nFirst use needs internet access for the embedding model. Check your file path and setup.", file=sys.stderr)
        sys.exit(1)
