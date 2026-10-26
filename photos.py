"""Attach a locally stored illustrative photo without changing stored recipes."""
import json
from functools import lru_cache
from pathlib import Path

from categories import recipe_categories, contains
from recipes import Recipe

PHOTO_DIR = Path(__file__).resolve().parent / 'web/photos'


@lru_cache(maxsize=1)
def photo_manifest():
    return json.loads((PHOTO_DIR / 'manifest.json').read_text())


def photo_key(recipe):
    title = recipe.title.casefold()
    categories = recipe_categories(recipe)
    if 'beverage' in categories:
        for pattern, key in [('lemonade','lemonade'),('punch','punch'),('tea','tea'),
                             ('coffee','coffee'),('smoothie','smoothie'),('milkshake','milkshake')]:
            if contains(title, pattern):
                return key
        return 'juice'
    # More specific dish names before broad ingredient names.
    rules = [
        ('peanut butter cookies?','peanut-cookies'),('oatmeal.*cookies?|raisin.*cookies?','oatmeal-cookies'),
        ('lemon.*bars?','lemon-bars'),('green beans?','green-beans'),
        ('coleslaw|slaw','coleslaw'),('meat ?balls?','meatballs'),('hamburger|hamburgers','burger'),
        ('wings','wings'),('quiche','quiche'),('pickles','pickles'),('salsa|pico de gallo','salsa'),
        ('slush','slush'),('jello|gelatin|apricot salad|molded.*delight','gelatin'),
        ('chocolate.*bars?|chocolate.*squares','brownies'),('bars?|squares|torte|crisp','cake'),
        ('mousse|dirt|ladyfinger','pudding'),('mints|marshmallow treats|peanut butter balls','fudge'),
        ('snickerdoodles','cookies'),('sticky buns','bread'),

        ('fruit salad|ambrosia|pineapple.*salad','fruit-salad'),('potato salad','potato-salad'),
        ('macaroni salad|pasta salad|spaghetti salad','pasta-salad'),
        ('brownies|brownie','brownies'),('cheesecake|cheese cake','cheesecake'),
        ('chocolate.*cake|devil.s food','chocolate-cake'),('cookies|cookie','cookies'),
        ('ice cream|sherbet|sorbet','ice-cream'),('fudge|candy|candies|bark','fudge'),
        ('pudding','pudding'),('cake','cake'),
        ('pot pie|shepherd.s pie|chicken pie','casserole'),('pie|cobbler|tart','pie'),
        ('corn bread|cornbread','cornbread'),('biscuits?|scones?','biscuits'),
        ('muffins?','muffins'),('pancakes?','pancakes'),('waffles?','waffles'),
        ('french toast','toast'),('burritos?','burrito'),('sandwich|toast','sandwich'),
        ('bread|rolls?','bread'),('salad','salad'),('chili','chili'),('stew|goulash','stew'),
        ('soup|chowder|bisque','soup'),('lasagna','lasagna'),('spaghetti','spaghetti'),
        ('pasta|fettuccine|macaroni|noodle|linguine','pasta'),('pizza','pizza'),
        ('dip|spread','dip'),('sauce|dressing|marinade','sauce'),
        ('casserole|medley','casserole'),('meat ?loaf','meatloaf'),
        ('rice','rice'),('potato|potatoes','potatoes'),('beans','beans'),
        ('chicken|turkey','chicken'),('beef|steak|roast','beef'),
        ('fish|salmon|tuna|shrimp|seafood','fish'),
        ('broccoli|vegetables?|veggie|zucchini|carrots?|squash|corn|mushrooms?|onions?|okra|cabbage|tomatoes','vegetables'),
    ]
    for pattern, key in rules:
        if contains(title, pattern):
            return key
    for category, key in [('dessert','cake'),('soup','soup'),('salad','salad'),('bread','bread'),
                          ('pasta','pasta'),('breakfast','pancakes'),('snack','dip')]:
        if category in categories:
            return key
    names = ' '.join(recipe.ingredient_names).lower()
    if contains(names, r'sugar|chocolate|marshmallows|gelatin') and not contains(names, r'beef|chicken|pork|fish'):
        return 'cake'
    return 'casserole'


def with_photo(data):
    recipe = Recipe(**data)
    manifest = photo_manifest()
    key = photo_key(recipe)
    # Some Wikimedia pages have no reusable lead image. Only fall back within
    # reasonable food groups rather than showing a drink as a solid dish.
    fallbacks = {'peanut-cookies':'cookies','oatmeal-cookies':'cookies','lemon-bars':'cake',
                 'green-beans':'vegetables','coleslaw':'salad','meatballs':'beef','burger':'beef',
                 'wings':'chicken','quiche':'casserole','pickles':'vegetables','salsa':'sauce',
                 'slush':'juice','gelatin':'fruit-salad','vegetables':'casserole','rice':'casserole','fish':'casserole',
                 'biscuits':'bread','muffins':'bread','toast':'bread','burrito':'sandwich',
                 'pudding':'cake','pie':'cake','fudge':'brownies','cheesecake':'cake',
                 'smoothie':'juice','milkshake':'juice','coffee':'tea','juice':'lemonade',
                 'potato-salad':'salad','fruit-salad':'salad','pasta-salad':'salad',
                 'stew':'soup','chili':'soup','beans':'vegetables'}
    while key not in manifest and key in fallbacks:
        key = fallbacks[key]
    photo = manifest.get(key, manifest['casserole'])
    return {**data, 'photo': {**photo, 'url': '/photos/' + photo['file'],
                            'alt': f"Illustrative {photo['topic'].lower()} photo; not the exact recipe"}}
