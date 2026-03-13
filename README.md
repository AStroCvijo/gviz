# gviz — Graph Visualizer

Web aplikacija za vizualizaciju, istraživanje i manipulaciju grafova (usmerenih/neusmerenih, cikličnih/acikličnih). Izgrađena sa Django backend-om i D3.js vizualizacijom, sa plugin arhitekturom koja omogućava lako dodavanje novih izvora podataka i stilova vizualizacije.

## Funkcionalnosti

- Interaktivna vizualizacija grafova (pan, zoom, drag, selekcija čvorova)
- Više prikaza: Main View, Tree View, Bird View (minimapa)
- Upravljanje workspace-ima za rad sa više grafova istovremeno
- CLI terminal za manipulaciju grafovima (search, filter, create, edit, delete)
- Plugin sistem za izvore podataka (JSON, XML) i vizualizere (Simple, Block)
- Podrška za ciklične strukture

## Pokretanje

### Preduslovi

- Python 3.9+
- pip

### Brzo pokretanje

```bash
chmod +x setup.sh
./setup.sh
```

Skripta automatski kreira virtualno okruženje, instalira sve zavisnosti i komponente, pokreće migracije i startuje server na `http://127.0.0.1:8000`.

### Ručno pokretanje

```bash
# 1. Kreiranje i aktivacija virtualnog okruženja
python3 -m venv .venv
source .venv/bin/activate

# 2. Instalacija zavisnosti
pip install -r requirements.txt

# 3. Instalacija komponenti (redosled je bitan)
pip install -e api/
pip install -e platform/
pip install -e json_data_source/
pip install -e xml_data_source/
pip install -e simple_visualizer/
pip install -e block_visualizer/

# 4. Migracije i pokretanje
cd gviz/
python manage.py migrate --run-syncdb
python manage.py runserver
```

Aplikacija je dostupna na `http://127.0.0.1:8000`.

## Korišćenje

1. Otvorite aplikaciju u browseru
2. Izaberite izvor podataka (JSON ili XML) i učitajte fajl
3. Graf se prikazuje u Main View sa D3.js force layout-om
4. Koristite toolbar za prebacivanje prikaza (Tree View, Bird View)
5. Koristite CLI terminal za komande:
   - `search <tekst>` — pretraga čvorova po atributima
   - `filter <izraz>` — filtriranje (npr. `age > 25`)
   - `create node <atributi>` — kreiranje novog čvora
   - `edit node <id> <atributi>` — izmena čvora
   - `delete node <id>` — brisanje čvora

## Dodavanje novog plugina

gviz koristi Python entry point mehanizam za automatsko otkrivanje pluginova. Postoje dva tipa: **Data Source** (izvor podataka) i **Visualizer** (vizualizer).

### Struktura plugina

```
moj_plugin/
├── setup.py
└── moj_plugin/
    ├── __init__.py
    └── plugin.py
```

### Data Source plugin

Implementirajte `DataSourcePlugin` iz `api.plugins`:

```python
from typing import Any, List
from api.models import Graph
from api.plugins import DataSourcePlugin, PluginParameter


class MojDataSourcePlugin(DataSourcePlugin):

    def get_name(self) -> str:
        return "moj-data-source"

    def get_description(self) -> str:
        return "Opis mog izvora podataka"

    def get_parameters(self) -> List[PluginParameter]:
        return [
            PluginParameter(
                name="file_path",
                label="Putanja do fajla",
                description="Putanja do fajla za učitavanje",
                required=True,
                param_type=str,
            ),
        ]

    def load(self, **kwargs: Any) -> Graph:
        file_path = kwargs.get("file_path", "")
        # Parsirati fajl i konstruisati graf
        # Koristiti ConcreteGraph, ConcreteNode, ConcreteEdge iz gviz_platform.graph
        ...
        return graph
```

### Visualizer plugin

Implementirajte `VisualizerPlugin` iz `api.plugins`:

```python
from api.models import Graph
from api.plugins import VisualizerPlugin


class MojVisualizerPlugin(VisualizerPlugin):

    def get_name(self) -> str:
        return "moj-visualizer"

    def get_description(self) -> str:
        return "Opis mog vizualizera"

    def render(self, graph: Graph) -> str:
        # Vratiti HTML string sa ugrađenim JavaScript-om
        # koji renderuje graf
        html = "<div id='graph'>...</div><script>...</script>"
        return html
```

### Registracija plugina

U `setup.py` registrujte plugin kroz entry point:

```python
from setuptools import setup, find_packages

setup(
    name="gviz-moj-plugin",
    version="1.0.0",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "gviz-api",
    ],
    entry_points={
        # Za data source plugin:
        "gviz.data_source": [
            "moj-data-source = moj_plugin.plugin:MojDataSourcePlugin",
        ],
        # Za visualizer plugin:
        # "gviz.visualizer": [
        #     "moj-visualizer = moj_plugin.plugin:MojVisualizerPlugin",
        # ],
    },
)
```

### Instalacija i aktivacija

```bash
pip install -e moj_plugin/
```

Plugin se automatski otkriva pri sledećem pokretanju aplikacije nije potrebna dodatna konfiguracija.

## Tehnologije

- **Backend:** Python, Django 4.2
- **Frontend:** JavaScript, D3.js, HTML5, CSS
- **Baza:** SQLite (Django ORM)
- **Arhitektura:** Plugin sistem sa Python entry points
