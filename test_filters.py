import unittest
from filters import validate_filters, matches_filters
from recipes import Recipe
from store import RecipeStore


def recipe(title, ingredients):
    return Recipe(title, title, ingredients, ingredients, ['Cook.'])


class FilterTests(unittest.TestCase):
    def test_type_alternatives_and_ingredient_intersection(self):
        filters = validate_filters({'types':['soup','salad'], 'ingredients':['chicken','rice']})
        self.assertTrue(matches_filters(recipe('Chicken Soup',['chicken breast','white rice']), filters))
        self.assertTrue(matches_filters(recipe('Chicken Salad',['chicken','rice']), filters))
        self.assertFalse(matches_filters(recipe('Chicken Soup',['chicken']), filters))
        self.assertFalse(matches_filters(recipe('Chicken Casserole',['chicken','rice']), filters))

    def test_word_boundaries_and_plurals(self):
        filters = validate_filters({'ingredients':['egg','potato']})
        self.assertTrue(matches_filters(recipe('Breakfast',['2 eggs','3 potatoes']),filters))
        self.assertFalse(matches_filters(recipe('Vegetables',['eggplant','potatoes']),filters))

    def test_validation_and_empty_selection(self):
        self.assertTrue(matches_filters(recipe('Anything',[]), validate_filters()))
        for value in [{'types':['invalid']}, {'ingredients':'rice'}, [], {'other':[]}]:
            with self.assertRaises(ValueError):
                validate_filters(value)

    def test_real_search_keeps_query_constraints(self):
        store=RecipeStore()
        if not store.count():
            self.skipTest('Import corpus first')
        self.assertEqual(store.search('A refreshing beverage for a summer gathering', [], filters={'types':['breakfast']}), [])
        rows=store.search('A cozy dinner on a cold winter night', [], limit=9, filters={'ingredients':['chicken']})
        self.assertTrue(rows)
        for row in rows:
            self.assertTrue(matches_filters(row['recipe'], validate_filters({'ingredients':['chicken']})))
