# Pantry Pal — first version

This README is a scaffold, not your finished homework submission. Write the four
sections below yourself, after using the app. All implementation notes after the
AI-generated heading were written by Codex.

## 1. What my app does and why I chose it

TODO: Write 1–2 sentences in your own words.

## 2. My data and storage choices

TODO: Explain the source, recipe count, what one item means, chunking, and metadata.

## 3. Adding recipes and searching

TODO: Explain the user workflow in your own words after trying the menu.

## 4. Two semantic-search examples

TODO: Run the examples in TEST_REPORT.md yourself. Record the queries, returned
recipes, and why an important-keyword search would miss them. Explain the result
in your own words; do not claim that all paraphrases work.

## AI-generated implementation and setup notes

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

### How it works

1. `recipes.py` validates RecipeNLG fields and normalizes a small set of ingredient aliases.
2. `store.py` uses ChromaDB 1.5.9 `PersistentClient` with cosine distance and the
   local `all-MiniLM-L6-v2` ONNX embedding model.
3. Searchable text combines the title, optional description, extracted ingredient
   names, and directions. Long text is split into 240-token windows with up to 32
   tokens of overlap using the model's tokenizer; full recipes remain in metadata.
   The prepared 500-recipe subset produces 501 chunks.
4. Explicit food categories are hard constraints before pantry ranking. Requests
   for beverages, desserts, soups/stews, salads, bread, pasta, breakfast, or snacks
   only admit recipes classified into those categories. Lunch/dinner exclude
   beverages, desserts, and condiments. Classification uses conservative title
   rules in `categories.py`, not ingredient mentions; a casserole containing soup
   is still a casserole. Unknown titles are excluded for specific category requests.
   This can miss unusually named recipes; it is not a comprehensive food ontology
   or a general natural-language constraint parser. No wrong-category fallback
   is used when a category has no close matches.
   Search considers every chunk in this small local collection, rejects cosine
   distances above 0.70, and deduplicates recipes. With pantry ingredients, recipes
   that use at least one pantry item come first. Within those groups, fewer missing
   plus unverified ingredients ranks higher, then greater ingredient coverage, then
   closer semantic distance. Without a pantry, results rank by semantic distance.
   This keeps the meal request relevant while prioritizing dishes needing less shopping.
5. The CLI shows three results and the browser shows up to nine, with matching ingredients, a missing-ingredient shopping
   list, full ingredient quantities, original directions, and source links.
6. Imports use stable content IDs and upsert, so repeating an identical import
   does not duplicate it. User additions receive UUIDs and are immediately searchable.

The database lives at `chroma_store/` relative to the source files, so starting the
app from another working directory still opens the same collection. `--store`
can select a separate database for experiments.

### Limits to understand

- Input and source recipes are English. The corpus contains many US-style dishes.
- The 0.70 distance cutoff is a heuristic based on initial examples, not a calibrated
  confidence probability. Results over 0.65 are labeled loose matches. Some relevant
  queries are rejected and some irrelevant results can still pass.
- Negation, dietary exclusions, allergies, time limits, and quantities are not
  enforced. For example, a request for a meatless Italian meal may retrieve a beef
  casserole. Inspect the ingredient list; this version does not promise those filters.
- Pantry matching uses exact normalized names and a short alias list; it does not
  infer substitutions. `milk` differs from `coconut milk`, and `chicken` differs from
  `chicken breast`. Common seasonings are assumed available using the explicit list in recipes.py. Main ingredients such as meat, vegetables, milk, eggs, butter, and flour are still checked. Quantity sufficiency is not checked.
- RecipeNLG's extracted ingredient names can omit or mislabel ingredients. Raw
  ingredient lines without a matching extracted name are explicitly flagged for
  manual checking. The full original ingredient list is also shown. This simple
  check can over-flag spelling variations and cannot detect every extraction error.
- Source directions are preserved, not generated or independently corrected.
- No update/delete UI, hosted deployment, or generated explanations.

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

### Cartoon theme update

The active interface now uses original inline SVG food cartoons instead of the
photo library. Dish names select cookie, bread, beverage, salad, pasta and other
illustrations, with an ingredient-based fallback. These are playful impressions,
not exact recipe previews. SVGs render without external image requests, even when
an older server response has no photo metadata. The rounded Nunito font is bundled
locally under its SIL Open Font License in web/fonts/OFL.txt. Historical photo
assets and credits remain in the project but are no longer displayed.

Meal intent is applied before pantry ranking: ordinary lunch/dinner/supper queries
exclude breakfast dishes, snacks, standalone bread, desserts, drinks, condiments,
and unclassified recipes. An explicit exception such as “breakfast for dinner”
is respected. These conservative title-based rules may omit suitable unusually
named dishes; they do not guarantee every arbitrary natural-language constraint.

### Keyword filters

Use **Pick your favorites** to select dish types and ingredient keywords, then
click **Apply filters**. Dish types are alternatives (Soup OR Salad); ingredient
keywords must all appear in the recipe's ingredient text (Chicken AND Rice).
Matching is case-insensitive with word boundaries and common plurals. A keyword
also matches compound ingredient names, such as chicken broth. Filters work on
both the full collection and semantic search, before pagination/ranking limits.
They narrow rather than override the description; conflicting selections can
return no results. **Clear filters** restores the current unfiltered view.

Results appear on a horizontal recipe shelf. Swipe/scroll sideways or use the
left/right buttons. Keyboard users can focus the shelf and use Arrow keys,
Home/End, then Enter to open a recipe. Collection page navigation remains below
the shelf; changing a page or search resets the shelf to the first result.

The carousel now uses a centered circular layout: selected cards are largest,
and side cards shrink with distance. Horizontal scrolling/swiping changes selection;
click a side card to center it, then click the center card to open its recipe.
Left/right controls wrap around; Home/End select the first/last result.

### Home and Search pages

Home (`/`) is a discovery dashboard with one random featured recipe and eight
more random picks. Shuffle requests a new sample and excludes the previous batch
when the corpus is large enough. Click any recipe to open its instructions.
Search (`/search`) retains pantry input, semantic search, keyword filters and the
centered carousel. Home category shortcuts open Search with a preset dish filter.
Both pages include Add a recipe. Restart the Python server after this route update.
