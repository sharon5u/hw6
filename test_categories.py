import unittest
from categories import query_categories, recipe_categories, matches_category
from recipes import Recipe
from store import RecipeStore


def recipe(title):
    return Recipe(title, title, ['cream of mushroom soup', 'coffee'], ['soup', 'coffee'], ['Mix.'])


class CategoryTests(unittest.TestCase):
    def test_beverages_exclude_food_even_with_drink_words(self):
        wanted, excluded = query_categories('A refreshing beverage for a summer gathering')
        for title in ['Lemonade', 'Easy Party Punch', 'Russian Tea', 'Banana Smoothie']:
            self.assertTrue(matches_category(recipe(title), wanted, excluded), title)
        for title in ['Cheese Dip', 'Summer Chicken', 'Coffee Cake', 'Tea Cookies', 'Lemonade Pie', 'Fruit Salad', 'Unknown creation']:
            self.assertFalse(matches_category(recipe(title), wanted, excluded), title)

    def test_specific_categories(self):
        for query, good, bad in [('a soup', 'Potato Soup', 'Chicken Casserole'),
                                 ('a dessert', 'Apple Pie', 'Chicken Pot Pie'),
                                 ('a salad', 'Green Salad', 'Salad Dressing'),
                                 ('a pasta dish', 'Lasagna', 'Lemonade'),
                                 ('breakfast', 'Waffles', 'Cheese Dip'),
                                 ('some bread', 'Corn Bread', 'Chocolate Cake')]:
            wanted, excluded = query_categories(query)
            self.assertTrue(matches_category(recipe(good), wanted, excluded), good)
            self.assertFalse(matches_category(recipe(bad), wanted, excluded), bad)

    def test_ingredients_do_not_define_category(self):
        self.assertEqual(recipe_categories(recipe('Chicken Casserole')), {'main'})

    def test_negative_and_compound_requests(self):
        self.assertEqual(query_categories('not a beverage')[0], set())
        self.assertIn('beverage', query_categories('not a beverage')[1])
        self.assertEqual(query_categories('coffee cake')[0], {'dessert'})
        wanted, excluded = query_categories('A cozy dinner on a cold winter night')
        self.assertFalse(matches_category(recipe('Lemonade'), wanted, excluded))
        self.assertFalse(matches_category(recipe('Chocolate Cake'), wanted, excluded))
        self.assertTrue(matches_category(recipe('Swiss Vegetable Medley'), wanted, excluded))

    def test_dinner_excludes_conflicting_meal_types(self):
        for query in ['cozy dinner', 'a hearty supper', 'lunch', 'a main course']:
            wanted, excluded = query_categories(query)
            for title in ['Breakfast Burritos', 'Breakfast Casserole', 'Brunch Pasta',
                          'Pancakes', 'Waffles', 'Corn Bread', 'Cheese Dip',
                          'Lemonade', 'Chocolate Cake', 'Unknown creation']:
                self.assertFalse(matches_category(recipe(title), wanted, excluded), (query, title))
            for title in ['Beef Burritos', 'Chicken Casserole', 'Vegetable Soup', 'Green Salad']:
                self.assertTrue(matches_category(recipe(title), wanted, excluded), (query, title))

    def test_explicit_exceptions_and_negatives(self):
        for query, good, bad in [
            ('breakfast for dinner', 'Breakfast Burritos', 'Chocolate Cake'),
            ('bread for dinner', 'Corn Bread', 'Lemonade'),
            ('a dessert after dinner', 'Chocolate Cake', 'Breakfast Burritos'),
            ('soup for dinner', 'Vegetable Soup', 'Breakfast Soup'),
            ('cozy dinner, not a salad', 'Chicken Casserole', 'Green Salad'),
        ]:
            wanted, excluded = query_categories(query)
            self.assertTrue(matches_category(recipe(good), wanted, excluded), query)
            self.assertFalse(matches_category(recipe(bad), wanted, excluded), query)


class ActualCorpusTests(unittest.TestCase):
    def test_reported_beverage_bug_with_unrelated_pantry(self):
        store = RecipeStore()
        if not store.count():
            self.skipTest('Import the real corpus first')
        results = store.search('A refreshing beverage for a summer gathering', ['egg', 'beef', 'garlic'], 9)
        self.assertTrue(results)
        for result in results:
            self.assertIn('beverage', recipe_categories(result['recipe']), result['recipe'].title)
        self.assertTrue(any(r['recipe'].title == 'Easy Party Punch' for r in results))

    def test_cozy_dinner_with_and_without_pantry(self):
        store = RecipeStore()
        if not store.count():
            self.skipTest('Import the real corpus first')
        for pantry in [[], ['egg', 'beef', 'garlic']]:
            results = store.search('A cozy dinner on a cold winter night', pantry, 9)
            self.assertTrue(results)
            for result in results:
                categories = recipe_categories(result['recipe'])
                self.assertFalse(categories & {'breakfast', 'dessert', 'beverage', 'snack', 'bread', 'condiment'}, result['recipe'].title)
                self.assertTrue(categories & {'main', 'soup', 'salad', 'pasta'}, result['recipe'].title)
