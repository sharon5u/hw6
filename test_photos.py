import json
import unittest
from pathlib import Path
from photos import PHOTO_DIR, with_photo, photo_key, photo_manifest
from recipes import Recipe


def make(title):
    return Recipe('test', title, ['rice'], ['rice'], ['Cook.'])


class PhotoTests(unittest.TestCase):
    def test_drinks_and_desserts_have_distinct_photos(self):
        for title, expected in [('Lemonade','lemonade'),('Easy Party Punch','punch'),('Russian Tea','tea'),
                                 ('Coffee Cake','cake'),('Chocolate Cake','chocolate-cake')]:
            self.assertEqual(photo_key(make(title)),expected)

    def test_all_actual_recipes_have_local_photos_with_attribution(self):
        path = Path(__file__).parent / 'data/recipes_500.json'
        if not path.exists():
            self.skipTest('Fetch the corpus first')
        for recipe in json.loads(path.read_text()):
            result = with_photo(recipe)
            self.assertTrue((PHOTO_DIR / result['photo']['file']).is_file())
            self.assertTrue(result['photo']['source'].startswith('https://'))
            self.assertTrue(result['photo']['license'])
            self.assertIn('not the exact recipe',result['photo']['alt'])

    def test_new_recipes_get_photo_without_changing_stored_schema(self):
        original=make('My special casserole').to_dict()
        self.assertNotIn('photo', original)
        enriched=with_photo(original)
        self.assertTrue(enriched['photo']['url'].startswith('/photos/'))
        self.assertNotIn('photo', original)

    def test_photo_assets_are_images(self):
        for photo in photo_manifest().values():
            data=(PHOTO_DIR / photo['file']).read_bytes()
            self.assertTrue(data.startswith(b'\xff\xd8') or data.startswith(b'\x89PNG'))
