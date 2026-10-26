"""Behavior tests. Integration tests use the actual local embedding model."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from app import load_recipes
from recipes import Recipe, pantry_match, text_list, unmapped_ingredients, is_seasoning, main_pantry
from store import ROOT, RecipeStore, rank_matches


class RankingTests(unittest.TestCase):
    def candidate(self, identity, have, missing, distance, unverified=None):
        return dict(recipe=Recipe(identity, identity, [], [], []), have=have,
                    missing=missing, distance=distance, unverified=unverified or [])

    def test_one_pantry_item_prefers_less_shopping_over_closer_meaning(self):
        elaborate = self.candidate('elaborate', ['egg'], ['milk', 'flour', 'butter', 'sugar'], .2)
        simple = self.candidate('simple', ['egg'], ['bread'], .6)
        self.assertEqual(rank_matches([elaborate, simple], True)[0]['recipe'].id, 'simple')

    def test_uses_pantry_before_nonmatching_recipe(self):
        unrelated = self.candidate('unrelated', [], ['rice'], .2)
        match = self.candidate('match', ['egg'], ['bread', 'butter'], .5)
        self.assertEqual(rank_matches([unrelated, match], True)[0]['recipe'].id, 'match')

    def test_unverified_lines_do_not_look_ready_to_cook(self):
        incomplete = self.candidate('incomplete', ['egg'], [], .2, ['flour', 'butter'])
        complete = self.candidate('complete', ['egg'], ['bread'], .6)
        self.assertEqual(rank_matches([incomplete, complete], True)[0]['recipe'].id, 'complete')

    def test_without_pantry_uses_semantic_order(self):
        close = self.candidate('close', [], ['milk', 'flour'], .2)
        distant = self.candidate('distant', [], [], .6)
        self.assertEqual(rank_matches([distant, close], False)[0]['recipe'].id, 'close')


class ParsingTests(unittest.TestCase):
    def test_both_list_encodings(self):
        self.assertEqual(text_list('["egg", "rice"]'), ["egg", "rice"])
        self.assertEqual(text_list("['egg', 'rice']"), ["egg", "rice"])
        with self.assertRaises(ValueError):
            text_list('__import__("os").system("false")')

    def test_no_substring_substitutions_and_salt_is_assumed(self):
        recipe = Recipe("test", "Dish", ["milk", "egg", "salt"],
                        ["milk", "egg", "salt"], ["Mix."])
        have, missing = pantry_match(recipe, ["coconut milk", "Eggs"])
        self.assertEqual(have, ["egg"])
        self.assertEqual(missing, ["milk"])

    def test_seasonings_never_inflate_main_ingredient_counts(self):
        recipe = Recipe('beef', 'Beef and broccoli', [],
                        ['beef', 'broccoli', 'salt', 'pepper', 'vegetable oil', 'sugar', 'soy sauce'], ['Cook.'])
        self.assertEqual(pantry_match(recipe, ['beef', 'salt', 'oil']), (['beef'], ['broccoli']))
        self.assertEqual(main_pantry(['salt', 'pepper', 'sugar', 'oil']), [])

    def test_quantity_lines_and_similarly_named_main_ingredients(self):
        for value in ['1/2 tsp. salt', '2 Tbsp. olive oil', 'black pepper, to taste', '1 c. sugar']:
            self.assertTrue(is_seasoning(value), value)
        for value in ['bell pepper', 'green peppers', 'peanut butter', 'milk', 'flour', 'onion', 'garlic', 'beef in soy sauce']:
            self.assertFalse(is_seasoning(value), value)

    def test_unmapped_seasonings_are_not_shopping_penalties(self):
        recipe = Recipe('r', 'Rice', ['rice', '1 tsp. salt', '2 tbsp. olive oil', '1 carrot'],
                        ['rice'], ['Cook.'])
        self.assertEqual(unmapped_ingredients(recipe), ['1 carrot'])

    def test_import_rejects_incomplete_and_deduplicates(self):
        row = dict(title="Rice", ingredients=["1 cup rice"], NER=["rice"], directions=["Boil."])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "recipes.json"
            path.write_text(json.dumps([row, row, {"title": "Incomplete"}]))
            self.assertEqual(len(load_recipes(path, 500)), 1)

    def test_missing_extracted_ingredient_is_flagged(self):
        recipe = Recipe("punch", "Punch", ["2 pkg. Kool-Aid", "2 c. sugar"],
                        ["sugar"], ["Mix."])
        self.assertEqual(unmapped_ingredients(recipe), ["2 pkg. Kool-Aid"])


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.path = Path(cls.temporary.name) / "database"
        cls.store = RecipeStore(cls.path)
        cls.recipes = [
            Recipe("soup", "Lentil stew", ["1 cup lentils", "1 carrot", "water"],
                   ["lentils", "carrot", "water"], ["Simmer lentils and diced carrot until tender."],
                   "A hearty bowl of vegetables and legumes."),
            Recipe("dessert", "Chocolate ice cream", ["cream", "cocoa", "sugar"],
                   ["cream", "cocoa", "sugar"], ["Churn and freeze."], "A frozen dessert."),
        ]
        cls.store.index(cls.recipes)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_reimport_does_not_duplicate(self):
        before = self.store.collection.count()
        self.store.index(self.recipes)
        self.assertEqual(self.store.collection.count(), before)

    def test_meaning_based_retrieval(self):
        result = self.store.search("A hearty vegetable dinner", ["carrots"], 1)
        self.assertEqual(result[0]["recipe"].id, "soup")
        self.assertEqual(result[0]["have"], ["carrot"])

    def test_long_text_is_not_silently_truncated(self):
        text = "Chop the vegetables and simmer gently. " * 100 + "Finish with saffron."
        chunks = self.store.chunks(text)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(self.store.tokenizer.encode(c).ids) <= 256 for c in chunks))
        self.assertIn("saffron", chunks[-1])

    def test_add_search_and_restart_via_cli(self):
        path = self.path.parent / "interactive"
        entries = "\n".join([
            "2", "Saffron risotto", "Creamy Italian rice", "rice | 1 cup", "saffron | a pinch", "",
            "Stir rice in hot stock until tender and add saffron.", "", "1", "rice, saffron",
            "saffron risotto", "5", "",
        ])
        result = subprocess.run([sys.executable, str(ROOT / "app.py"), "--store", str(path)],
                                input=entries, text=True, capture_output=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Saved "Saffron risotto"', result.stdout)
        self.assertIn("1. Saffron risotto", result.stdout)
        self.assertIn("You have (2)", result.stdout)
        restarted = subprocess.run([sys.executable, str(ROOT / "app.py"), "--store", str(path),
                                    "search", "--need", "saffron risotto"],
                                   text=True, capture_output=True, timeout=90)
        self.assertEqual(restarted.returncode, 0, restarted.stderr)
        self.assertIn("1. Saffron risotto", restarted.stdout)


if __name__ == "__main__":
    unittest.main()
