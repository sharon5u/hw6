## Web APP for HW 6 - Pantry Pal
Pantry Pal is a recipe discovery app that helps users find recipes through meaning-based search, available ingredients, and customizable filters new. User can enter their description of the meal they want and put down the ingredients they have to search for a dish.

## Data Source and Info
Data is originally from RecipeNLG: a novel dataset of cooking recipes.

## How to add/use?
User can add an entry to the dataset by adding their own recipe (name, ingredients, steps). 

## Two queries
1. "A refreshing beverage for a summer gathering” --> Easy Party Punch
2. “A cozy dinner on a cold winter night” --> Swiss Vegetable Medley
## How to obtain data

### Run the prepared copy

For the cookbook-style browser app, run:

```bash
.venv/bin/python web_app.py
```

Then open **http://127.0.0.1:8000** in your browser. Keep the terminal running;
press Ctrl+C to stop. On this Mac, `Start-Web.command` runs the same server.
If port 8000 is occupied, use `python web_app.py --port 8002` and open that port.

The browser interface lets you browse the whole collection, search by meal intent
and pantry ingredients, open full recipes, check off ingredient lists, and save
your own recipes. New recipes are embedded immediately and persist in the same
Chroma collection used by the CLI. The layout adapts to narrow and wide screens.
Checkmarks are temporary reading aids; they are not saved pantry inventory.

This is a local app for the assignment, not a publicly hosted website. The server
binds only to 127.0.0.1 and has no multi-user accounts. Its backend uses Python's
standard library, so there are no additional packages to install.

### Recipe photos

RecipeNLG has no image field. The UI uses a bundled Wikimedia photo library,
matched to dish types such as lemonade, punch, cake, soup, and casseroles. Photos
are explicitly labeled **illustrative**, not photos of the exact recipe. Recipes
in the same dish family can share a photo; unfamiliar titles use a broader fallback.
Newly added recipes receive a representative photo automatically.

The original photographer, source, and license appear in the recipe detail view.
`web/photos/manifest.json` records all attribution and download URLs. The displayed
images are cropped to fit their cards. Keep these credits and assets with the app;
they are included in Git, unlike the raw recipe dataset. Photos load locally and
work offline. `python fetch_photos.py` can restore missing photos; it observes
rate-limit backoff and skips existing files.

For the original CLI:

Open `Start.command` on this Mac, or run these commands from this folder:

```bash
.venv/bin/python app.py
```

The prepared copy already contains 500 real RecipeNLG recipes and their Chroma
index. It does not use generated sample recipes or require a paid API key.

### Install a fresh copy

Use Python 3.11 or 3.12 (tested with Python 3.12.14). From the project folder:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python fetch_recipes.py
python app.py import data/recipes_500.json
python app.py
```

`fetch_recipes.py` fetches small pages through the Hugging Face Dataset Viewer API,
not the multi-gigabyte CSV. It selects 500 complete, unique `Gathered` recipes from
six fixed 100-row windows and shuffles with seed 42. This is a reproducible convenience
sample, not a uniform sample of all RecipeNLG. The saved manifest includes request
URLs, retrieval time, selected IDs, and a SHA-256 checksum. Upstream changes could
change a newly downloaded subset; preserve your manifest when reporting results.

The first import downloads Chroma's approximately 79 MB ONNX model archive. The
model runs locally; after setup, search and additions work without an API key or
network connection. Dependencies are a larger initial download.

If you already have the official RecipeNLG CSV:

```bash
python app.py import /absolute/path/full_dataset.csv --limit 500
```

This CSV importer reads the first 500 usable unique records; the remote subset
script uses the window-and-shuffle method described above.

### Try it

Menu: find a dish, add a recipe, show recipe count, import recipes, or quit.
Enter main ingredient names without quantities, separated by commas. A blank pantry is allowed. Common oils, salt, pepper, sugars, dried spices, extracts, and basic condiments are assumed available; they do not count as on-hand or missing main ingredients. All ingredients remain visible in the cooking instructions.
When adding a recipe, enter one ingredient per line as `name | amount`, then one
instruction per line. Blank lines finish those lists.

```bash
python app.py count
python app.py search --pantry "pineapple juice, ginger ale, sugar, water" --need "A refreshing beverage for a summer gathering"
python app.py search --need "A cozy dinner on a cold winter night"
python app.py search --need "Help me repair my bicycle brakes"
python -m unittest -v
```


### Data sources and attribution

- Original: [RecipeNLG project](https://recipenlg.cs.put.poznan.pl/) and
  [Bień et al., 2020 paper](https://aclanthology.org/2020.inlg-1.4/).
- Download mirror: [SandhyaKilari/RecipeNLG_dataset](https://huggingface.co/datasets/SandhyaKilari/RecipeNLG_dataset).
- [Original dataset card and use terms](https://huggingface.co/datasets/mbien/recipe_nlg).
  Follow the original non-commercial research/educational terms; the mirror's
  broader license label should not be treated as overriding those terms.
- [Chroma embedding documentation](https://docs.trychroma.com/docs/embeddings/embedding-functions)
  and [collection configuration](https://docs.trychroma.com/docs/collections/configure).

`data/`, `chroma_store/`, `.cache/`, and `.venv/` are ignored by Git. Publish the
code and reproducible download instructions, not these local directories.

### AI use and remaining homework

Codex researched access to the dataset, wrote this first implementation and tests,
ran it locally, and drafted these labeled notes. This is not evidence of 4.5 hours
of student work. The student still needs to understand and refine the code, write
the first four README sections, maintain the prompt log, record the demo, add a
portfolio entry, push to GitHub, and submit the required form.


