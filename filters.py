"""Explicit UI filters shared by browsing and semantic retrieval."""
from categories import contains, matches_category, query_categories, recipe_categories

DISH_TYPES = {'dinner', 'breakfast', 'soup', 'salad', 'pasta', 'dessert', 'beverage', 'bread', 'snack'}
INGREDIENTS = {'chicken', 'beef', 'egg', 'rice', 'broccoli', 'potato', 'mushroom', 'cheese', 'lemon'}


def validate_filters(value=None):
    if value is None:
        value = {}
    if not isinstance(value, dict) or set(value) - {'types', 'ingredients'}:
        raise ValueError('Invalid filters.')
    result = {}
    for field, allowed in [('types', DISH_TYPES), ('ingredients', INGREDIENTS)]:
        values = value.get(field, [])
        if not isinstance(values, list) or len(values) > len(allowed) or not all(isinstance(x, str) and x in allowed for x in values):
            raise ValueError('Choose filters from the available keywords.')
        result[field] = list(dict.fromkeys(values))
    return result


def matches_filters(recipe, filters):
    types = filters['types']
    if types:
        categories = recipe_categories(recipe)
        dinner = 'dinner' in types and matches_category(recipe, *query_categories('dinner'))
        if not dinner and not categories.intersection(set(types) - {'dinner'}):
            return False
    # All selected ingredient keywords must occur in ingredient text. Word
    # boundaries avoid matching egg to eggplant or rice to licorice.
    names = '\n'.join(recipe.ingredient_names + recipe.ingredients)
    patterns = {'egg': r'eggs?', 'potato': r'potato(?:es)?', 'mushroom': r'mushrooms?'}
    return all(contains(names, patterns.get(word, word)) for word in filters['ingredients'])
