"""Recipe parsing and conservative ingredient matching; no database dependency."""
from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import asdict, dataclass


def text_list(value) -> list[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            try:
                value = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                raise ValueError("Expected a JSON list of strings") from None
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        raise ValueError("Expected a list of strings")
    return [re.sub(r"\s+", " ", x).strip() for x in value if x.strip()]


@dataclass
class Recipe:
    id: str
    title: str
    ingredients: list[str]
    ingredient_names: list[str]
    directions: list[str]
    description: str = ""
    link: str = ""
    source: str = "user"

    @classmethod
    def from_row(cls, row: dict) -> Recipe:
        title = str(row.get("title") or "").strip()
        ingredients = text_list(row.get("ingredients", []))
        directions = text_list(row.get("directions", []))
        names = text_list(row.get("ingredient_names", row.get("NER", row.get("ner", []))))
        if not title or not ingredients or not directions or not names:
            raise ValueError("A recipe needs a title, ingredients, ingredient names, and directions")
        # Content-derived IDs make importing the same recipe idempotent.
        fingerprint = json.dumps([title.casefold(), ingredients, directions], ensure_ascii=False)
        identity = str(row.get("id") or "recipenlg-" + hashlib.sha256(fingerprint.encode()).hexdigest()[:24])
        return cls(identity, title, ingredients, names, directions,
                   str(row.get("description") or ""), str(row.get("link") or ""),
                   str(row.get("source") or "RecipeNLG"))

    def to_dict(self) -> dict:
        return asdict(self)

    def search_text(self) -> str:
        return (f"{self.title}. {self.description}\n"
                f"Ingredients: {', '.join(self.ingredient_names)}.\n"
                f"Method: {' '.join(self.directions)}")


# Deliberately small: no fuzzy substring matches or automatic substitutions.
ALIASES = {
    "brocoli": "broccoli",
    "eggs": "egg", "onions": "onion", "tomatoes": "tomato",
    "potatoes": "potato", "carrots": "carrot", "mushrooms": "mushroom",
    "lemons": "lemon", "limes": "lime", "apples": "apple",
    "bananas": "banana", "chicken breasts": "chicken breast",
    "scallion": "green onion", "scallions": "green onion",
    "spring onion": "green onion", "spring onions": "green onion",
    "green onions": "green onion", "chickpeas": "chickpea",
    "garbanzo beans": "chickpea", "aubergine": "eggplant",
    "courgette": "zucchini", "bell peppers": "bell pepper",
}

# Explicit names, not substring rules: bell peppers, peanut butter, milk,
# flour, fresh onions/garlic, meat and vegetables remain main ingredients.
SEASONINGS = {
    "water", "salt", "table salt", "sea salt", "kosher salt", "seasoned salt",
    "pepper", "black pepper", "ground black pepper", "white pepper", "salt and pepper",
    "sugar", "white sugar", "granulated sugar", "brown sugar", "powdered sugar",
    "confectioners sugar", "confectioners' sugar",
    "oil", "cooking oil", "vegetable oil", "olive oil", "extra virgin olive oil",
    "canola oil", "sunflower oil", "corn oil", "peanut oil", "sesame oil",
    "coconut oil", "salad oil", "cooking spray", "nonstick cooking spray",
    "garlic powder", "onion powder", "garlic salt", "onion salt", "celery salt",
    "paprika", "smoked paprika", "cayenne", "cayenne pepper", "chili powder",
    "chilli powder", "red pepper flakes", "crushed red pepper", "cumin", "ground cumin",
    "cinnamon", "ground cinnamon", "nutmeg", "ground nutmeg", "allspice",
    "ground cloves", "cloves", "ground ginger", "dried oregano", "oregano",
    "dried basil", "dried thyme", "dried rosemary", "bay leaf", "bay leaves",
    "italian seasoning", "italian seasonings", "poultry seasoning", "curry powder",
    "vanilla", "vanilla extract", "almond extract", "lemon extract",
    "vinegar", "white vinegar", "apple cider vinegar", "rice vinegar", "balsamic vinegar",
    "red wine vinegar", "white wine vinegar", "soy sauce", "light soy sauce",
    "dark soy sauce", "worcestershire sauce", "hot sauce", "tabasco sauce",
    "mustard", "dijon mustard", "dry mustard", "ketchup",
}


def is_seasoning(value: str) -> bool:
    """Recognize known seasonings, including simple quantity-bearing raw lines."""
    name = re.sub(r"\s+", " ", value.casefold()).strip()
    name = re.sub(r"\([^)]*\)", "", name)
    name = re.sub(r"^[\d\s./¼½¾⅓⅔⅛-]+", "", name)
    name = re.sub(r"^(?:c|cups?|tsp|teaspoons?|tbsp|tablespoons?|oz|ounces?|lb|pounds?|g|grams?|ml|pinch|dash)\.?\s+", "", name)
    name = re.sub(r"(?:,\s*)?\s*(?:to taste|as needed|optional)$", "", name)
    name = re.sub(r"\s+", " ", name).strip(' ,.')
    return name in SEASONINGS


def main_pantry(pantry: list[str]) -> list[str]:
    return [x for x in pantry if x.strip() and not is_seasoning(x)]


def assumed_seasonings(recipe: Recipe) -> list[str]:
    return list(dict.fromkeys(x for x in recipe.ingredient_names if is_seasoning(x)))


def normalize_ingredient(value: str) -> str:
    value = re.sub(r"\s+", " ", value.casefold().strip())
    return ALIASES.get(value, value)


def pantry_match(recipe: Recipe, pantry: list[str]) -> tuple[list[str], list[str]]:
    available = {normalize_ingredient(x) for x in main_pantry(pantry)}
    have, missing, seen = [], [], set()
    for name in recipe.ingredient_names:
        if is_seasoning(name):
            continue
        key = normalize_ingredient(name)
        if key not in seen:
            (have if key in available else missing).append(name)
            seen.add(key)
    return have, missing


def unmapped_ingredients(recipe: Recipe) -> list[str]:
    """Flag raw lines not covered by an extracted name; never silently omit them."""
    def words(value):
        return " " + " ".join(re.findall(r"[a-z]+", value.casefold())) + " "
    names = [words(name) for name in recipe.ingredient_names]
    return [line for line in recipe.ingredients
            if not is_seasoning(line) and not any(name in words(line) for name in names)]
