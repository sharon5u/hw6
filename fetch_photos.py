"""Download a small attributed Wikimedia photo library for illustrative recipe images."""
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEST = ROOT / 'web/photos'
TOPICS = {
 'peanut-cookies':'Peanut butter cookie','oatmeal-cookies':'Oatmeal raisin cookie',
 'lemon-bars':'Lemon bar','green-beans':'Green bean casserole','coleslaw':'Coleslaw',
 'meatballs':'Meatball','burger':'Hamburger','wings':'Buffalo wing',
 'quiche':'Quiche','pickles':'Pickled cucumber','salsa':'Salsa (food)',
 'slush':'Slushy','gelatin':'Jello salad',
 'lemonade':'Lemonade','punch':'Punch (drink)','tea':'Iced tea','coffee':'Coffee',
 'smoothie':'Smoothie','milkshake':'Milkshake','juice':'Orange juice',
 'soup':'Vegetable soup','stew':'Beef stew','chili':'Chili con carne',
 'salad':'Greek salad','potato-salad':'Potato salad','fruit-salad':'Fruit salad','pasta-salad':'Pasta salad',
 'bread':'Bread','cornbread':'Cornbread','biscuits':'Biscuit (bread)','muffins':'Muffin',
 'pancakes':'Pancake','waffles':'Waffle','toast':'French toast','burrito':'Breakfast burrito',
 'cookies':'Chocolate chip cookie','brownies':'Chocolate brownie','cake':'Cake',
 'chocolate-cake':'Chocolate cake','cheesecake':'Cheesecake','pie':'Apple pie',
 'pudding':'Pudding','ice-cream':'Ice cream','fudge':'Fudge',
 'pasta':'Pasta primavera','lasagna':'Lasagna','spaghetti':'Spaghetti aglio e olio',
 'casserole':'Casserole','chicken':'Roast chicken','beef':'Roast beef',
 'meatloaf':'Meatloaf','fish':'Fish and chips','rice':'Cooked rice',
 'potatoes':'Mashed potato','vegetables':'Ratatouille','beans':'Baked beans',
 'dip':'Hummus','sauce':'Tomato sauce','sandwich':'Sandwich','pizza':'Pizza',
}


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent':'PantryPalHomework/1.0 (educational cookbook; Wikimedia image attribution retained)'})
    for attempt in range(4):
        time.sleep(1.5)
        try:
            with urllib.request.urlopen(req, timeout=40) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 3:
                raise
            delay = min(60, int(error.headers.get('Retry-After', 15 * (attempt + 1))))
            print(f'Rate limited; pausing {delay}s.', flush=True)
            time.sleep(delay)


def api(host, **params):
    return json.loads(get(f'https://{host}/w/api.php?' + urllib.parse.urlencode(dict(action='query',format='json',**params))))


def clean(value):
    return html.unescape(re.sub('<[^>]+>', '', value)).strip()


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    manifest_path = DEST / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    missing = {key: topic for key, topic in TOPICS.items()
               if key not in manifest or not (DEST / manifest[key]['file']).exists()}
    if not missing:
        print(f'{len(manifest)} photos ready.')
        return
    payload = api('en.wikipedia.org', titles='|'.join(missing.values()), redirects=1,
                  prop='pageimages', piprop='thumbnail|name', pithumbsize=640)['query']
    redirects = {x['from']: x['to'] for x in payload.get('redirects', [])}
    pages = {x['title']: x for x in payload['pages'].values()}
    filenames = ['File:' + x['pageimage'] for x in pages.values() if 'pageimage' in x]
    info_pages = api('commons.wikimedia.org', titles='|'.join(filenames), prop='imageinfo',
                     iiprop='extmetadata|url')['query']['pages']
    info = {x['title'].removeprefix('File:').replace('_', ' '): x for x in info_pages.values()}
    for key, topic in missing.items():
        try:
            page = pages[redirects.get(topic, topic)]
            filename = page['pageimage']
            details = info[filename.replace('_', ' ')]['imageinfo'][0]
            meta = details['extmetadata']
            license_name = clean(meta.get('LicenseShortName',{}).get('value',''))
            if not any(x in license_name.lower() for x in ['cc by', 'cc0', 'public domain']):
                raise ValueError('Unverified reuse license: '+license_name)
            photo_url = page['thumbnail']['source']
            content = get(photo_url)
            if content.startswith(b'\xff\xd8'):
                extension = '.jpg'
            elif content.startswith(b'\x89PNG'):
                extension = '.png'
            else:
                raise ValueError('Not a JPEG or PNG photograph')
            local_name = key + extension
            (DEST / local_name).write_bytes(content)
            manifest[key] = dict(file=local_name, topic=topic,
                author=clean(meta.get('Artist',{}).get('value','Unknown author')),
                license=license_name, license_url=meta.get('LicenseUrl',{}).get('value',''),
                source=details['descriptionurl'], image_url=photo_url,
                note='Illustrative dish-type photo, not the exact RecipeNLG recipe. Display crops to fit.')
            manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
            print(key, license_name, len(content), flush=True)
        except Exception as error:
            print('SKIP',key,str(error),flush=True)
    print(f'{len(manifest)} photos ready.')

if __name__ == '__main__':
    main()
