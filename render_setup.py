"""Prepare the dataset/model/database as build artifacts, not Git files."""
import subprocess
import sys
from pathlib import Path
from app import load_recipes
from store import RecipeStore

ROOT = Path(__file__).resolve().parent
SEED = ROOT / 'render_seed'


def prepare():
    subprocess.run([sys.executable, str(ROOT / 'fetch_recipes.py')], check=True)
    recipes = load_recipes(ROOT / 'data/recipes_500.json', 500)
    if len(recipes) != 500:
        raise RuntimeError('Expected 500 seed recipes')
    store = RecipeStore(SEED)
    store.index(recipes)
    print(f'Render seed ready: {store.count()} recipes', flush=True)


if __name__ == '__main__':
    prepare()
