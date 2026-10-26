"""HTTP integration tests run against a disposable collection, not your cookbook."""
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from web_app import create_server
from store import RecipeStore


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.path = Path(cls.temp.name) / 'db'
        cls.server = create_server(0, cls.path)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def request(self, path, data=None):
        req = urllib.request.Request(self.url + path,
            data=json.dumps(data).encode() if data is not None else None,
            headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            return response.status, json.load(response)

    def test_add_search_and_persistence(self):
        status, added = self.request('/api/recipes', dict(title='Lemon chickpea toast',
            description='A tangy lunch', ingredients=['bread | 2 slices', 'chickpeas | 1 cup', 'lemon | 1'],
            directions=['Toast the bread.', 'Mash chickpeas with lemon and spread on toast.']))
        self.assertEqual(status, 201)
        self.assertIn('photo', added['recipe'])
        with urllib.request.urlopen(self.url + added['recipe']['photo']['url']) as image:
            self.assertTrue(image.headers['Content-Type'].startswith('image/'))
            self.assertGreater(len(image.read()), 1000)
        _, search = self.request('/api/search', dict(need='lemon chickpea toast', pantry=['bread']))
        self.assertEqual(search['results'][0]['recipe']['id'], added['recipe']['id'])
        self.assertEqual(search['results'][0]['have'], ['bread'])
        self.assertEqual(RecipeStore(self.path).count(), added['count'])

    def test_static_and_empty_page(self):
        with urllib.request.urlopen(self.url) as response:
            self.assertIn(b'What\xe2\x80\x99s cooking?', response.read())
        _, body = self.request('/api/recipes?page=9999')
        self.assertEqual(body['recipes'], [])

    def test_rejects_invalid_recipe(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request('/api/recipes', {'title': 'Incomplete'})
        self.assertEqual(error.exception.code, 400)

    def test_rejects_cross_origin_mutation(self):
        req = urllib.request.Request(self.url + '/api/recipes', data=b'{}',
            headers={'Content-Type':'application/json', 'Origin':'http://unrelated.example'})
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(req)
        self.assertEqual(error.exception.code, 403)

    def test_filter_browsing_search_and_invalid_keywords(self):
        from recipes import Recipe
        store=RecipeStore(self.path)
        store.index([Recipe('filter-soup','Chicken Rice Soup',['chicken','rice'],['chicken','rice'],['Simmer.']),
                     Recipe('filter-salad','Chicken Salad',['chicken','lettuce'],['chicken','lettuce'],['Mix.'])])
        _, body=self.request('/api/recipes?type=soup&ingredient=chicken&ingredient=rice')
        self.assertEqual(body['total'],1)
        self.assertEqual(body['recipes'][0]['id'],'filter-soup')
        _, body=self.request('/api/recipes?type=soup&ingredient=chicken&ingredient=rice&page=2')
        self.assertEqual(body['recipes'],[])
        self.assertEqual(body['total'],1)
        _, body=self.request('/api/search',dict(need='Chicken Rice Soup',pantry=[],filters={'types':['soup'],'ingredients':['rice']}))
        self.assertEqual([r['recipe']['id'] for r in body['results']],['filter-soup'])
        for path,data in [('/api/recipes?type=bogus',None),('/api/search',dict(need='soup',filters={'types':['bogus']}))]:
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.request(path,data)
            self.assertEqual(error.exception.code,400)

    def test_home_discovery_routes_and_shuffle(self):
        from recipes import Recipe
        RecipeStore(self.path).index([Recipe(f'discover-{i}',f'Rice Bowl {i}',['rice'],['rice'],['Cook rice.']) for i in range(20)])
        _, first=self.request('/api/discover')
        ids=[r['id'] for r in first['recipes']]
        self.assertEqual(len(ids),9)
        self.assertEqual(len(set(ids)),9)
        from urllib.parse import urlencode
        _, second=self.request('/api/discover?'+urlencode({'exclude':ids},doseq=True))
        self.assertFalse(set(ids)&{r['id'] for r in second['recipes']})
        self.assertEqual(first['count'],second['count'])
        for route in ['/', '/search']:
            with urllib.request.urlopen(self.url+route) as response:
                html=response.read()
                self.assertIn(b'id="home-page"',html)
                self.assertIn(b'id="search-page"',html)
