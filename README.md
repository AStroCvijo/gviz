# gviz — Raspodjela zadataka

## Pregled tima

| Student | Uloga |
|---------|-------|
| **Student 1** | API biblioteka + Platform core + JSON Data Source Plugin + UI dizajn |
| **Student 2** | Simple Visualizer Plugin + Main View (D3.js) |
| **Student 3** | XML Data Source Plugin + Tree View + Bird View |
| **Student 4** | Block Visualizer Plugin + Django web app + Search/Filter/CLI backend |

---

## Student 1 — API biblioteka + Platform core + JSON Data Source Plugin + UI dizajn

### Cilj

Postaviti temelje cijelog projekta: definisati apstraktni API koji svi plugini
moraju implementirati, izgraditi platformu koja upravlja pluginima, radnim
prostorima i filtriranjem grafova, kreirati prvi data source plugin (JSON format)
sa podrškom za ciklične strukture, te dizajnirati kompletan UI layout Django
aplikacije koji ostali studenti popunjavaju funkcionalnostima.

---

### Student 1 Issues

| Issue | Grana | Opis |
|-------|-------|------|
| `#S1-01` | `feature-api-library` | Kompletna API biblioteka: apstraktne klase Node/Edge/Graph, DataSourcePlugin/VisualizerPlugin, hijerarhija grešaka |
| `#S1-02` | `feature-platform-graph-model` | ConcreteNode, ConcreteEdge, ConcreteGraph — podrška za usmerene/neusmerene i ciklične/aciklične grafove |
| `#S1-03` | `feature-platform-services` | PluginManager (entry point discovery), WorkspaceManager, FilterEngine (search + filter → podgraf) |
| `#S1-04` | `feature-json-data-source` | JSONDataSourcePlugin: dvoprolazni parser sa @id semantikom za cikluse, test podaci (210 + 216 čvorova) |
| `#S1-05` | `feature-django-setup-and-ui` | Django AppConfig integracija platforme, URL routing, kompletan UI layout (Main/Tree/Bird View, toolbar, terminal) |

---

## Student 2 — Simple Visualizer Plugin + Main View

### Cilj

Napraviti plugin koji prima `Graph` objekat i vraća HTML string koji D3.js
može renderovati kao interaktivni graf u browseru. Zatim taj HTML integrisati
u Main View dio UI-ja koji je Student 1 dizajnirao.

---

### Student 2 Issues

| Issue | Grana | Opis |
|-------|-------|------|
| `#S2-01` | `feature-simple-visualizer-plugin` | Kreirati SimpleVisualizerPlugin, render() metoda |
| `#S2-02` | `feature-main-view-d3` | D3.js force layout, pan, zoom |
| `#S2-03` | `feature-main-view-drag` | Drag & drop čvorova |
| `#S2-04` | `feature-main-view-mouseover` | Mouseover → Node Details panel |
| `#S2-05` | `feature-node-selection-coordination` | Koordinacija selekcije sa Tree/Bird View |

---

## Student 3 — XML Data Source Plugin + Tree View + Bird View

### Cilj

Napraviti drugi data source plugin (XML format), implementirati Tree View sa
dinamičkim expand/collapse i Bird View sa minimap-om koji prati Main View.

---

### Student 3 Issues

| Issue | Grana | Opis |
|-------|-------|------|
| `#S3-01` | `feature-xml-parser` | XMLParser — mapiranje elemenata na čvorove/grane, podrška za aciklične i ciklične strukture (XPath reference), generisanje test podataka (200+ čvorova) |
| `#S3-02` | `feature-xml-plugin` | XMLDataSourcePlugin wrapper + registracija entry point-a |
| `#S3-03` | `feature-tree-view` | Tree View — izgradnja stabla, expand/collapse, detekcija i prikaz ciklusa |
| `#S3-04` | `feature-tree-view-selection` | Koordinacija selekcije čvora između Tree View i Main View |
| `#S3-05` | `feature-bird-view` | Bird View — minimap sa skaliranjem + sinhronizacija viewport-a sa Main View-om |

---

## Student 4 — Block Visualizer Plugin + Django web app + Search/Filter/CLI

### Cilj

Napraviti Block Visualizer plugin, implementirati sve Django API endpoint-e
koji zamjenjuju JavaScript mock stub-ove u `ui.js`, te implementirati CLI
backend za manipulaciju grafom putem komandi.

### Student 4 Issues

| Issue | Grana | Opis |
|-------|-------|------|
| `#S4-01` | `feature-block-visualizer-plugin` | BlockVisualizerPlugin — render() metoda koja vraća HTML za blokovski prikaz grafa |
| `#S4-02` | `feature-django-graph-api` | Django API: `load_graph`, `reset_workspace`, `list_workspaces`, `activate_workspace`, `delete_workspace` views + URL routing |
| `#S4-03` | `feature-django-search-filter` | Django API: `search_graph` i `filter_graph` views sa prikazom grešaka (server-side FilterEngine pozivi) |
| `#S4-04` | `feature-cli-backend` | `CLIHandler` klasa (Command pattern) + create/edit/delete operacije za čvorove i grane |
| `#S4-05` | `feature-js-api-calls` | Zamjena svih mock stub-ova u `ui.js` pravim `fetch()` pozivima prema Django API endpointima |

---

### 4.7 Design patterns koje Student 4 treba primijeniti

| Pattern | Gdje |
|---------|------|
| **Command pattern** | `CLIHandler` — svaka komanda je zaseban objekt sa `execute()` |
| **Chain of Responsibility** | Sukcesivno primjenjivanje filter → search → filter operacija |
| **Facade** | Django `views.py` — jednostavan interfejs prema kompleksnoj platformi |

---

## Zajednički zadaci

### Dijagram klasa

Potrebno je odraditi dijagram klasu

---
