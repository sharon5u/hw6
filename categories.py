"""Conservative food-type constraints, separate from semantic similarity.

The corpus has no reliable category field. Infer supported categories from the
recipe title (not ingredients: a casserole can contain soup without being soup).
Unknown titles are excluded when a specific category is explicitly requested.
"""
import re
from recipes import Recipe

PATTERNS = {
    'beverage': r'beverages?|drinks?|lemonades?|smoothies?|milkshakes?|cocktails?|mocktails?|punch|iced tea|coffee|tea|cocoa|juice|cider|eggnog',
    'dessert': r'desserts?|cakes?|cookies?|brownies|brownie|pies?|puddings?|ice cream|sherbet|sorbet|fudge|candy|candies|cobbler|cheesecakes?|tarts?|sweet treats?',
    'soup': r'soups?|stews?|chowders?|bisques?|chili|gumbos?',
    'salad': r'salads?',
    'bread': r'breads?|biscuits?|muffins?|rolls?|scones?',
    'pasta': r'pasta|spaghetti|lasagna|fettuccine|linguine|macaroni|ravioli|penne|noodles?',
    'breakfast': r'breakfast|brunch|pancakes?|waffles?|omelettes?|omelets?|french toast',
    'snack': r'snacks?|appetizers?|dips?|spreads?|nachos',
}


def contains(text, pattern):
    return bool(re.search(r'\b(?:' + pattern + r')\b', text, re.I))


def recipe_categories(recipe: Recipe) -> set[str]:
    title = recipe.title.lower()
    # Compound names take precedence over incidental words: coffee cake,
    # tea cookies, chicken soup casserole, salad dressing, etc.
    if contains(title, r'dressing|sauce|marinade|seasoning'):
        return {'condiment'}
    # An explicit meal label must win over a preparation (breakfast casserole).
    if contains(title, r'breakfast|brunch'):
        return {'breakfast'}
    if contains(title, r'casserole|meatloaf|meat loaf|pot pie|shepherd.s pie|chicken pie'):
        return {'main'}
    if contains(title, r'dip|spread'):
        return {'snack'}
    if contains(title, PATTERNS['salad']):
        return {'salad'}
    if contains(title, PATTERNS['dessert']):
        return {'dessert'}
    if contains(title, PATTERNS['bread']):
        return {'bread', 'breakfast'}
    if contains(title, PATTERNS['soup']):
        return {'soup', 'main'}
    if contains(title, PATTERNS['pasta']):
        return {'pasta', 'main'}
    if contains(title, PATTERNS['breakfast']):
        return {'breakfast'}
    if contains(title, PATTERNS['beverage']):
        return {'beverage'}
    if contains(title, PATTERNS['snack']):
        return {'snack'}
    return {'main'} if contains(title, r'chicken|beef|pork|fish|salmon|steak|rice|potatoes|vegetables?|broccoli|beans|burritos?|sandwiches?|burgers?|enchiladas?|tacos?|pizza|lentils?|tofu') else set()


def query_categories(query: str) -> tuple[set[str], set[str]]:
    """Return requested/excluded types. Multiple positive types are alternatives."""
    # Treat compound food names in the query as units too.
    text = re.sub(r'\b(?:coffee|tea|cocoa|lemonade)\s+(cake|cookies?|bread)\b', r'\1', query.lower())
    wanted, excluded = set(), set()
    for category, pattern in PATTERNS.items():
        for match in re.finditer(r'\b(?:' + pattern + r')\b', text):
            before = text[max(0, match.start() - 35):match.start()]
            negative = re.search(r'\b(?:no|not|without|excluding|except|avoid)\s+(?:(?:a|an|any|the)\s+)?$', before)
            (excluded if negative else wanted).add(category)
    # Meal intent is a constraint, not just a semantic hint. Explicit dish
    # requests still work ("bread for dinner", "dessert after dinner").
    dinner = contains(text, r'dinner|supper|lunch|main course|main dish')
    if dinner:
        excluded.update({'beverage', 'dessert', 'condiment', 'breakfast', 'snack', 'bread'} - wanted)
        # Bread is also marked breakfast in the corpus; allow explicitly asked bread.
        if 'bread' in wanted:
            excluded.discard('breakfast')
        if not wanted:
            wanted.update({'main', 'soup', 'salad', 'pasta'})
    return wanted, excluded


def matches_category(recipe: Recipe, wanted: set[str], excluded: set[str]) -> bool:
    categories = recipe_categories(recipe)
    return not (categories & excluded) and (not wanted or bool(categories & wanted))
