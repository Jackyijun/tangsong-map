# Between Tang and Song, 755–979

[![中文](https://img.shields.io/badge/lang-%E4%B8%AD%E6%96%87-red.svg)](README.md) [![English](https://img.shields.io/badge/lang-English-blue.svg)](README.en.md)

An interactive historical map from the An Lushan Rebellion to the early Song (755–979): the territories of fanzhen (military circuits) and states at 39 snapshots, historical and modern names for 382 prefectures and towns, a dedicated outline of the Sixteen Prefectures of Yan and Yun, the route of Huang Chao's campaigns, and 64 capitals, 63 battles, 26 passes, 34 events, 44 mountain ranges, more than a hundred rivers and lakes, and the peoples on the periphery. The interface is in Chinese and English, switched with "中 | EN" at the top right of the map.

---

## 1. Just look

Double-click **`docs/index.html`** and open it in any modern browser (Chrome, Edge, Safari, Firefox).

The file is about 1.5 MB with all data, styles and scripts embedded: no network, no server and no external libraries. You can copy it to a USB stick, send it to someone, or put it on your own website.

It opens in Chinese; click "EN" at the top right of the map to switch to English, or add `#en` to the end of the URL to open the English version directly.

---

## 2. Live site

https://jackyijun.github.io/tangsong-map/

---

## 3. Build locally

You only need to rebuild after changing the historical content (`content/`) or the parameters (`src/config.py`). You need **Python 3.9 or newer**.

**macOS / Linux**

```bash
cd tangsong-map
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py --open
```

**Windows (PowerShell)**

```powershell
cd tangsong-map
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py --open
```

A full build takes about a minute; when it finishes, the newly built `docs/index.html` opens in your browser.

> No Python? On macOS use `brew install python` or download it from python.org; on Windows, install from python.org and tick "Add python.exe to PATH".
> If PowerShell refuses to run scripts, first run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or skip the virtual environment and run `py -m pip install -r requirements.txt` and then `py run.py --open`.

| Command | What it does |
|---|---|
| `python run.py` | Download the base map if missing → compute the territories → assemble the HTML |
| `python run.py --html` | Only reassemble the HTML (when you changed only `src/template.html`; under a second) |
| `python run.py --draft` | Build even if English text is missing or out of date (missing text temporarily shows the Chinese); without it the build stops with an error, see section 7 |
| `python run.py --open` | Open the result in a browser when done |
| `python run.py --preview 805,820` | Also draw territory sketches of these snapshots to `build/preview.png`, to check that allegiances are filled in correctly |
| `python tools/preview.py 895,907 100,125,20,42` | Draw sketches only, optionally for a longitude–latitude box |
| `python tools/snapcheck.py 903` | Without a full build, list in a second which prefectures each unit holds in these snapshots |
| `python tools/snapcheck.py --diff saved.json` | Compare with a result saved earlier with `--dump`, to confirm that inserting snapshots has not shifted the existing ones |
| `python tools/i18n.py status` | How many English entries are missing or out of date |
| `python tools/screenshot.py` | (Optional, needs Playwright) take headless-browser screenshots and check for script errors |

The archive includes the base map data (`geodata/ne/`, about 31 MB), so you can build offline. If you delete it, `run.py` downloads a pinned version from GitHub.

In the same environment the same input always builds byte-for-byte the same output, so changes can be tracked safely with git.

To preview through a local server (optional, not required):

```bash
python -m http.server -d docs 8000
# then open http://localhost:8000/
```

After building, commit `docs/index.html` and push it to `main`; the live site updates automatically.

---

## 4. Directory layout

```
tangsong-map/
├── run.py                 one-step build entry point
├── requirements.txt
├── README.md              this guide in Chinese (shown by default on GitHub)
├── README.en.md           this guide in English
├── docs/
│   ├── index.html         ★ the result, a single file (GitHub Pages publishes straight from /docs)
│   └── .nojekyll          lets GitHub Pages publish the files as they are
├── content/               ★ historical content (hand-written; most edits happen here)
│   ├── seeds.txt          457 points (312 prefectures, 70 towns, 75 helper points): historical names, coordinates, modern locations, name changes
│   ├── snaps.txt          39 snapshots: which fanzhen and which state each prefecture belongs to in that year
│   ├── units.py           names and descriptions of 143 states, fanzhen and tribes
│   ├── items.py           capitals, battles, passes, events, peoples, mountains, rivers, canals, deserts, key regions (the Sixteen Prefectures), campaign routes
│   ├── colors.lock.json   colors of published units, locked (adding snapshots or units leaves existing colors unchanged)
│   └── en/                English translations (*.json), Chinese fingerprints zh.lock.json, naming conventions GLOSSARY.md
├── src/
│   ├── config.py          ★ all tunable parameters (grid, costs, smoothing, colors…)
│   ├── fetch_data.py      download the Natural Earth base map
│   ├── build.py           compute territories; writes build/geo.json and build/data.json
│   ├── snapdsl.py         parser for the snapshot language of snaps.txt (shared by build.py and tools/snapcheck.py)
│   ├── i18n.py            merge in the English, check for missing and out-of-date text
│   ├── assemble.py        inject the data and the English into the template; writes docs/index.html
│   └── template.html      front end: page structure, styles, interaction script
├── geodata/
│   ├── prov.json          modern provincial borders (simplified)
│   └── ne/                Natural Earth 1:10m GeoJSON
├── tools/
│   ├── preview.py         matplotlib territory sketches
│   ├── i18n.py            English maintenance: status / todo / lock / table
│   ├── snapcheck.py       inspect and compare the allegiances of each snapshot without building
│   └── screenshot.py      Playwright screenshot check
└── build/                 intermediate files (safe to delete)
```

---

## 5. How it works

```
content/*.txt, *.py ─┐
                     ├─► build.py ─► build/geo.json + data.json ─► assemble.py ─► docs/index.html
geodata/ (base map) ─┘                                              ▲    ▲
                                              src/template.html ──┘    └── content/en/*.json
```

### 1. Why the territories are "computed"

There is no ready-made boundary data for the Tang fanzhen or the Five Dynasties and Ten Kingdoms. What the histories can establish is that "in a given year a given prefecture belonged to a given fanzhen", and Tang prefectural boundaries broadly "followed the lie of mountains and rivers". So the approach here is:

1. write by hand only the allegiance **prefecture → fanzhen → state** (`snaps.txt`);
2. let the computer infer the boundaries between prefectures from a "travel cost" map, so that they fall on ridges and great rivers wherever possible.

### 2. What `build.py` does

1. **Read the points**: the 457 points in `seeds.txt`. Type `z` is a prefecture, `c` a town or a place outside China, `r` a helper point that only claims territory and is not shown on the map (such as "Changtang" or "Siberia 1").
2. **Parse the snapshots**: `snaps.txt` is a small declarative language (syntax below). Each `@year` block inherits all the allegiances of the previous snapshot and only states what changed.
3. **Land–sea grid**: the 64° × 39.5° extent is cut into cells of 0.08° (about 8 km), 800 × 494 ≈ 400,000 cells in all. Large lakes count as water.
4. **Cost grid**: each cell has a base cost of 1.
   - The mountain ranges in `items.RANGES` "burn" a Gaussian band of high cost along their ridgelines, peaking at +9 for main ranges.
   - Natural Earth's mountain polygons add a little cost overall.
   - The Yangtze adds +7; the Yellow River (including its Tang–Song course) and the Huai (including its old lower course) add +3.5 each.
   - The sea has infinite cost.
5. **Multi-source shortest paths**: with all points as sources, one run of `scipy.sparse.csgraph.dijkstra(min_only=True)` on an 8-neighbor grid graph (about 310,000 land cells and 2.5 million directed edges) assigns each cell to the prefecture with the lowest cost distance.
   - This amounts to a **weighted Voronoi diagram** whose boundaries are drawn towards ridges and rivers.
   - Cells beyond a cost distance of `MAX_REACH` are unclaimed, for example deep in the Gobi or the heart of the Tibetan plateau.
6. **Polygons**: for each snapshot:
   - the cells are colored by "prefecture → unit", giving a fanzhen layer and a state layer;
   - they are extended 4 cells out to sea, and the front end clips the coastline with the land outline, so no gaps are left;
   - after Gaussian smoothing (σ = 1.15 cells), marching squares (`skimage.measure.find_contours`) traces the 0.5 contour;
   - finally the lines are simplified with Douglas–Peucker.
   - The label point is the "pole of inaccessibility" of the largest connected part (the maximum of the distance transform).
7. **Colors**:
   - three lightness levels × 24 hues are preset in the OKLCH color space, with chroma only 0.065–0.075, so all colors are muted;
   - Tang, Tibet, the Uyghurs, Nanzhao, Balhae, the Khitan, Silla and Song have fixed colors;
   - the remaining units are colored greedily from "the adjacencies that occur in any snapshot", the units with the most neighbors first, each taking the color most different from its already colored neighbors;
   - the colors of published units are recorded in `content/colors.lock.json` and take precedence at build time: adding snapshots or units only picks colors for the new units, and existing colors (including those shared with the 979 snapshot of the Song–Liao–Xia–Jin–Yuan map) stay the same;
   - the dark theme lightens them all.
8. **Base map and items**:
   - coasts, modern borders, lakes and deserts come from Natural Earth;
   - rivers are mapped to their Tang names through `items.NE_RIVERS`, e.g. Huang → 河 (the River), Hong → 富良江;
   - the Tang–Song course of the Yellow River, the ancient Ji River, the old lower Huai and the canals are hand-drawn polylines, and the modern lower Yellow River east of Zhengzhou is drawn dashed;
   - coordinates are multiplied by 100, rounded and delta-encoded. The base map plus 39 snapshots of territory come to about 1 MB (from 31 MB of source data).

### 3. The front end (`src/template.html`)

- **No dependencies**: plain JavaScript and SVG, no framework and no map library.
- **Projection**: Albers equal-area conic, standard parallels 25°N and 47°N, centered on 104°E, 35°N.
- **Layers (bottom to top)**: land → desert stipple → territory fill → hatching for autonomous fanzhen → heavy state borders → lakes → modern provinces → modern borders → mountains → rivers → canals → symbols and labels.
- **Label placement**: on every frame all labels are sorted by priority (selection > territory names > capitals > fanzhen seats > battles > great rivers > passes > …); each label tries several candidate positions in turn and is dropped if all of them overlap labels already placed. Each zoom level has display thresholds, so prefecture names and modern locations appear only when zoomed in.
- **Interaction**:
  - drag, scroll or pinch to zoom; hover for a tooltip, click to select;
  - the index on the right is linked to the map;
  - search matches historical names, modern names and name changes, in both Chinese and English, and English searches ignore diacritics (typing ngo quyen finds Ngô Quyền);
  - the timeline can be played (switch between 1× and 2× speed below the play button); the ← → keys step through snapshots and Esc clears the selection;
  - coloring switches between "Fanzhen / States", and each layer can be turned on and off;
  - there are also Timeline and Gazetteer views.
- **Markers that change over time**: each snapshot covers the years after the previous snapshot up to its own year (the 851 snapshot covers 845–851, for example).
  - Only battles, events and campaign routes in the current period are shown; the battles of the period are listed under the timeline and can be clicked to locate them.
  - Clicking a battle from another period in the index moves the timeline to that period.
  - Only current capitals and former capitals are shown; places that became capitals later do not appear early.
- **Campaign routes**: Huang Chao's campaigns (875–884) record the year of arrival at each point, and the map draws the route only up to the current snapshot: the stretch covered in this period as a solid line with arrows, earlier stretches as a dashed line. Clicking the route, or the "Campaign" button under the timeline, fits the whole route into view, and the index lists every stop. Add an entry to `items.ROUTES` in the same format to draw other routes.
- **The Sixteen Prefectures**: from the 938 snapshot onwards a red dashed line outlines the sixteen prefectures, a dotted line separates the seven prefectures south of the mountains from the nine north of them, and from 959 the return of Ying and Mo to Zhou is marked.
  - The outline is traced from the union of the grid cells of the sixteen prefectures (plus the area of the Waqiao and Yijin passes), by the same algorithm as the territories.
  - Clicking the outline, the "Region" button under the timeline or "Key regions" in the index selects it: the whole area is highlighted, all sixteen prefectures show their names and modern locations, and the panel on the right gives the history of the cession and the full list.
  - Adding an entry in the same format to `items.REGIONS` outlines another region (such as Hehuang or Guannan).
- **Chinese / English**: switched at the top right of the map and remembered by the browser; adding `#en` to the URL opens the English version directly. In English the map labels are in English only, while tooltips, the index, the timeline and the gazetteer add the original Chinese characters in small type after each English name; English labels are placed using their measured width, and long state names wrap onto two lines inside their territory.
- **Themes**: all colors are CSS variables and follow the system's light or dark theme. Each unit's color is `--u-<index>`, injected by `assemble.py`.

### 4. `assemble.py`

First it checks the English: if any text is missing or out of date (Chinese changed without the English following), it stops with an error unless `--draft` is given. Then it merges the English into the data (units `ne`, prefectures `ne`/`mode`, items `e{…}`, snapshots `erae`/`te`/`de`), and the front end picks the text in the current language.

The template has four placeholders: `__GEO__`, `__DATA__`, `__UCSS_LIGHT__` and `__UCSS_DARK__`. The script replaces them with the data and color variables, then wraps the result in the `<!doctype html>` document shell.

---

## 6. Common changes

**Change which fanzhen a prefecture belongs to in a given year**: add a line to that year's block in `snaps.txt`. For example, to give Suzhou (宿州) to Wuning in 805:

```
武宁{徐州}: 徐州 泗州 濠州 宿州
```

**Add a prefecture**:

1. add a line to `seeds.txt`: `宁州 107.92 35.50 甘肃宁县`
2. assign it to a unit in the `@755` block of `snaps.txt` (the first snapshot must give every point an allegiance, otherwise the build prints an `unassigned` warning)
3. run `python run.py --preview 755` and check that the territories look right

**Rename a prefecture**: add `N=0:old-name,year:new-name` to its line in `seeds.txt`, e.g. `N=0:汴州,907:开封府`.

**Add a snapshot** (790, say): insert between `@787` and `@794` in `snaps.txt`:

```
@790 | 贞元六年 | 北庭陷没 | description……
吐蕃: 庭州 轮台 弓月城 准噶尔
```

The front end adds a tick automatically. Because every snapshot inherits from the one before, an inserted snapshot changes the starting point of the next one: before inserting, save the current result with `python tools/snapcheck.py --dump build/snap-before.json`, and afterwards compare with `--diff build/snap-before.json`; if an existing snapshot changed where it should not have, write the allegiance, label (an empty `[]` deletes it) or seat back in the next snapshot.

**Add a battle, pass or event**: add a tuple in the same format to `BATTLES`, `PASSES` or `EVENTS` in `items.py`. Battles and events are assigned to snapshots by year automatically; for an event lasting several years, give its end year in `EVENT_END`.

**Add a campaign route**: add an entry to `ROUTES` in `items.py`: name, modern places, dates, description, and the points as `[longitude, latitude, year of arrival, place name]`. The route is assigned to periods by the years of arrival automatically.

**Add a state or fanzhen**: add `S(...)` (state), `Z(...)` (fanzhen) or `T(...)` (tribe) to `units.py`, then use its key in `snaps.txt`.

**Stop a border from crossing a mountain range**: add the range's ridgeline coordinates to `items.RANGES`, with `1` as the last field (main range, higher cost).

**Change colors**: change the unit's three OKLCH numbers in `content/colors.lock.json`, or delete its line to let it pick a new color; `PRESET_COLORS` and `PALETTE_LEVELS` in `src/config.py` only affect units not in the lock.

**Change only the page's look or interaction**: edit `src/template.html`, then run `python run.py --html`.

**After changing Chinese text**: change the matching English too (see section 7), or the build stops reporting it as out of date.

### `snaps.txt` syntax

```
@year | era | title | description               start a snapshot (inherits the previous one)
unit: prefecture prefecture                     assign these prefectures to the unit
unit[label]{seat}>state: prefecture …           also set this period's label, seat and overlord (all optional)
unit[new label]:                                only rename, without changing territory
unit[]:                                         delete a label set earlier and go back to the default name
unit: @other-unit                               take over every prefecture that belonged to other-unit at the start of this snapshot
unit: @other-unit@year                          take over the prefectures that belonged to other-unit at the end of that year's snapshot
·: prefecture prefecture                        make unclaimed
割据: unit unit …                               fanzhen defying the court in this period (hatched on the map), replacing the previous list
# comment
```

If the state is omitted, the default from `units.py` is used: fanzhen belong to Tang, states and tribes to themselves. A label, seat or overlord, once set, carries over to later snapshots until it is changed again.

---

## 7. The English version

Chinese is the source text. Every piece of Chinese that is displayed has a key, and the English is kept under the same keys in `content/en/`:

| File | Contents | Key |
|---|---|---|
| `units.json` | states, fanzhen, tribes: full name `n`, short map name `s` (optional), description `note` | unit key |
| `labels.json` | period labels from snapshots, such as "魏博（罗弘信）" | Chinese label |
| `seeds.json` | prefectures and towns: modern location `mod`, names in each period `n` | point ID |
| `items.json` | items: `old` `mod` `note` `yt` `sides` `cmd`, subdivisions of the Sixteen Prefectures `g`, campaign route place names `p` | `category:historical-name`, with `@year` added for items of the same name |
| `snaps.json` | snapshots: reign era `era`, title `t`, description `d` | year |
| `misc.json` | modern province names | Chinese name |

`zh.lock.json` records a fingerprint (the first 10 hex digits of the sha1) of the Chinese each English entry was written from. If the Chinese changes and the English does not, the build reports it as out of date.

After changing the English:

```bash
python run.py --html          # strict by default: stops and lists the counts if anything is missing or out of date
python tools/i18n.py todo     # lists the Chinese of every missing or out-of-date entry
# …edit content/en/*.json…
python tools/i18n.py lock     # record the new Chinese fingerprints
python run.py --html
```

To see the result first, use `python run.py --html --draft`; missing text temporarily shows the Chinese. `python tools/i18n.py table` exports every Chinese–English pair to `build/i18n-review.tsv` for review. The naming conventions (pinyin spelling, when 州, 府 and 军 are joined or separated, lunar months written as they are, and so on) are in `content/en/GLOSSARY.md`.

---

## 8. Tuning (`src/config.py`)

| Parameter | Default | Effect |
|---|---|---|
| `FIRST` | 820 | the snapshot shown when the page opens |
| `RES` | 0.08 | grid resolution (°). Smaller is finer; computing time grows roughly with the square |
| `COST_MAJOR_RANGE` | (9.0, 0.28) | peak cost and radius of influence of main mountain ranges |
| `COST_YANGTZE` etc. | — | how strongly the great rivers act as barriers |
| `MAX_REACH` | 7.5 | cells beyond this cost distance are unclaimed |
| `SMOOTH_SIGMA` | 1.15 | how smooth the borders are |
| `SIMPLIFY_TERR` | 0.025 | border simplification (larger is coarser and smaller) |
| `PRESET_COLORS` | — | states with fixed colors (OKLCH) |

---

## 9. Sources and reliability

- **Base map**: [Natural Earth](https://www.naturalearthdata.com/) 1:10m vector data (public domain), pinned at commit `ca96624`.
- **Modern provinces**: the simplified provincial borders of the earlier map of historical and modern place names in Hexi, Longyou and the Western Regions.
- **Historical sources**: allegiances and descriptions follow the Old and New Tang Histories, the *Zizhi tongjian* and the Old and New Histories of the Five Dynasties, and in outline vol. 5 of Tan Qixiang's *Historical Atlas of China*.
- **Limitations**:
  - Borders are indicative lines inferred from the allegiance of prefectures, not researched historical boundaries.
  - Points are sparse in the Western Regions, on the Tibetan plateau, north of the Gobi and in the northeast, so borders there are especially rough.
  - There are 39 snapshots; years with no change in territory get no snapshot (822–844, for example), and year-by-year changes between snapshots are not drawn.
  - Old river courses are drawn by hand following written sources and are approximate.
  - Disputed matters are marked "one account says" in the item notes: the allegiance of the cities of the Western Regions in the late 8th and early 9th centuries, the prefectures of Yiwu and Henghai in 784, the area actually controlled by the Liao army in the Central Plains in 947, and others.
  - The English is translated from the Chinese; the naming conventions are in `content/en/GLOSSARY.md`. Months are Chinese lunar months and are not converted to the Western calendar.
