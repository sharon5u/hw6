"""Local cookbook UI backed by the same persistent Chroma collection as the CLI."""
import argparse
import json
import random
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from filters import validate_filters, matches_filters
from recipes import Recipe, unmapped_ingredients, main_pantry, assumed_seasonings
from store import ROOT, RecipeStore
from photos import with_photo, photo_manifest, PHOTO_DIR


def create_server(port=8000, store_path=ROOT / 'chroma_store'):
    store = RecipeStore(store_path)
    lock = threading.Lock()

    def all_recipes():
        records = store.collection.get(include=['metadatas'])['metadatas'] or []
        unique = {x['recipe_id']: json.loads(x['recipe']) for x in records}
        return sorted(unique.values(), key=lambda r: r['title'].casefold())

    class Handler(BaseHTTPRequestHandler):
        def respond(self, data, status=200):
            raw = json.dumps(data).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == '/api/discover':
                query = parse_qs(parsed.query)
                excluded = set(query.get('exclude', [])[:12])
                with lock:
                    rows = all_recipes()
                pool = [r for r in rows if r['id'] not in excluded]
                if len(pool) < min(9, len(rows)):
                    pool = rows
                picks = random.sample(pool, min(9, len(pool)))
                return self.respond({'count': len(rows), 'recipes': [with_photo(r) for r in picks]})
            if parsed.path == '/api/recipes':
                try:
                    query = parse_qs(parsed.query)
                    page = max(1, int(query.get('page', ['1'])[0]))
                    with lock:
                        rows = all_recipes()
                    filters = validate_filters({'types': query.get('type', []), 'ingredients': query.get('ingredient', [])})
                    title = query.get('q', [''])[0].casefold().strip()
                    filtered = [r for r in rows if title in r['title'].casefold() and matches_filters(Recipe(**r), filters)]
                    start = (page - 1) * 12
                    return self.respond(dict(recipes=[with_photo(r) for r in filtered[start:start + 12]], total=len(filtered),
                                             count=len(rows), page=page))
                except ValueError as error:
                    return self.respond({'error': str(error)}, 400)
            files = {'/': ('index.html', 'text/html'), '/search': ('index.html', 'text/html'), '/style.css': ('style.css', 'text/css'),
                     '/app.js': ('app.js', 'text/javascript'),
                     '/fonts/nunito.ttf': ('fonts/nunito.ttf', 'font/ttf')}
            if parsed.path.startswith('/photos/'):
                name = parsed.path.removeprefix('/photos/')
                if name not in {p['file'] for p in photo_manifest().values()}:
                    return self.respond({'error': 'Not found'}, 404)
                raw = (PHOTO_DIR / name).read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'image/png' if name.endswith('.png') else 'image/jpeg')
                self.send_header('Content-Length', str(len(raw)))
                self.send_header('Cache-Control', 'public, max-age=86400')
                self.end_headers()
                self.wfile.write(raw)
                return
            if parsed.path not in files:
                return self.respond({'error': 'Not found'}, 404)
            name, mime = files[parsed.path]
            raw = (ROOT / 'web' / name).read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', mime + '; charset=utf-8')
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self):
            # Local mutations are same-origin only; do not expose this server publicly.
            origin = self.headers.get('Origin')
            if origin and origin != 'http://' + self.headers.get('Host', ''):
                return self.respond({'error': 'Cross-origin requests are not allowed.'}, 403)
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                return self.respond({'error': 'Expected JSON.'}, 415)
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 100_000:
                    return self.respond({'error': 'Request is empty or too large.'}, 413)
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise ValueError('Expected an object.')
                if self.path == '/api/search':
                    need = data.get('need', '')
                    pantry = data.get('pantry', [])
                    if not isinstance(need, str) or not need.strip() or len(need) > 1500:
                        raise ValueError('Enter a short description of the meal you want.')
                    if not isinstance(pantry, list) or len(pantry) > 100 or not all(isinstance(x, str) and len(x) <= 100 for x in pantry):
                        raise ValueError('Enter up to 100 ingredient names.')
                    filters = validate_filters(data.get('filters'))
                    with lock:
                        results = store.search(need, pantry, limit=9, filters=filters)
                    return self.respond({'main_pantry': main_pantry(pantry), 'results': [dict(recipe=with_photo(x['recipe'].to_dict()), have=x['have'],
                        missing=x['missing'], loose=x['distance'] > .65,
                        assumed=assumed_seasonings(x['recipe']),
                        unverified=unmapped_ingredients(x['recipe'])) for x in results]})
                if self.path == '/api/recipes':
                    title, description = data.get('title', ''), data.get('description', '')
                    lines, steps = data.get('ingredients', []), data.get('directions', [])
                    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 150:
                        raise ValueError('Add a recipe name (up to 150 characters).')
                    if not isinstance(description, str) or len(description) > 2000:
                        raise ValueError('Keep the description under 2,000 characters.')
                    for values in (lines, steps):
                        if not isinstance(values, list) or not 1 <= len(values) <= 100 or not all(isinstance(x, str) and x.strip() and len(x) <= 2000 for x in values):
                            raise ValueError('Add ingredients and steps, one per line (up to 100 lines).')
                    names, ingredients = [], []
                    for line in lines:
                        name, _, amount = line.partition('|')
                        if not name.strip():
                            raise ValueError('Each ingredient needs a name before the | separator.')
                        names.append(name.strip())
                        ingredients.append(f'{amount.strip()} {name.strip()}'.strip())
                    recipe = Recipe('user-' + str(uuid.uuid4()), title.strip(), ingredients, names,
                                    [x.strip() for x in steps], description.strip())
                    with lock:
                        store.index([recipe])
                        count = store.count()
                    return self.respond({'recipe': with_photo(recipe.to_dict()), 'count': count}, 201)
                return self.respond({'error': 'Not found'}, 404)
            except (ValueError, TypeError) as error:
                return self.respond({'error': str(error)}, 400)
            except Exception:
                import traceback
                traceback.print_exc()
                return self.respond({'error': 'Could not complete the request. Check the server terminal and try again.'}, 500)

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--store', type=Path, default=ROOT / 'chroma_store')
    args = parser.parse_args()
    server = create_server(args.port, args.store)
    print(f'Pantry Pal is ready at http://127.0.0.1:{server.server_port}', flush=True)
    print('Keep this terminal open. Press Ctrl+C to stop.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
