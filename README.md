graph_explorer_project/               # Root direktorijum celog projekta
├── api/                              # Python biblioteka za zajedničke apstrakcije i interfejse (API)
│   ├── __init__.py                   # Obeležava da je 'api' direktorijum Python paket
│   ├── interfaces.py                 # Definiše zajedničke interfejse/abstraktne klase za plug-inove (npr. BaseDataSource, BaseVisualizer)
│   ├── models.py                     # (Opcionalno) Definicije struktura podataka, npr. klase za Graf, Čvor, Granu
│   └── utils.py                      # Zajedničke pomoćne funkcije i klase koje koriste platforma i plug-inovi
├── platform/                         # Biblioteka koja koristi `api` i upravlja komunikacijom sa plug-inovima
│   ├── __init__.py                   # Inicijalizuje 'platform' paket
│   ├── main.py                       # (Opcionalno) Ulazna skripta za pokretanje platforme van Django okruženja (npr. CLI test)
│   ├── plugin_manager.py             # Logika za dinamičko učitavanje i registraciju plug-inova (korišćenjem API interfejsa)
│   ├── graph_builder.py              # Koristi data_source plug-inove za kreiranje grafa i prosleđuje ga vizualizacionom plug-inu
│   └── settings.py                   # Podešavanja platforme (npr. putanje do plug-in direktorijuma, konfiguracije plug-inova)
├── data_source_json/                 # Plugin za parsiranje JSON fajlova i kreiranje strukture grafa
│   ├── __init__.py                   # Inicijalizuje JSON data-source plug-in paket
│   ├── parser.py                     # Funkcije za čitanje i parsiranje JSON fajla u čvorove i veze grafa
│   └── plugin.py                     # Implementira `BaseDataSource` interfejs iz API-ja za JSON (npr. klasa JSONDataSource)
├── data_source_xml/                  # Plugin za parsiranje XML fajlova i kreiranje strukture grafa
│   ├── __init__.py                   # Inicijalizuje XML data-source plug-in paket
│   ├── parser.py                     # Funkcije za čitanje i parsiranje XML fajla u strukturu grafa
│   └── plugin.py                     # Implementira `BaseDataSource` interfejs za XML (npr. klasa XMLDataSource)
├── simple_visualizer/                # Plugin koji vizualizuje čvorove grafa kao jednostavne krugove
│   ├── __init__.py                   # Inicijalizuje simple_visualizer plug-in paket
│   ├── visualizer.py                 # Implementira `BaseVisualizer` interfejs (npr. klasa SimpleVisualizer za prikaz čvorova kao krugova)
│   └── assets/                       # (Opcionalno) Resursi za vizuelizaciju, npr. ikone ili template za krugove
├── block_visualizer/                 # Plugin koji prikazuje čvorove kao pravougaonike sa atributima
│   ├── __init__.py                   # Inicijalizuje block_visualizer plug-in paket
│   ├── visualizer.py                 # Implementira `BaseVisualizer` interfejs (npr. klasa BlockVisualizer za prikaz čvorova kao blokova sa tekstom)
│   └── templates/                    # (Opcionalno) Template fajlovi ili resursi specifični za blok vizualizaciju
│       └── node_block.html           # (Primer) HTML/SVG template za prikaz čvora kao pravougaonika sa detaljima
├── graph_explorer/                   # Django projektni direktorijum za web aplikaciju (korisnička interakcija)
│   ├── manage.py                     # Django skripta za upravljanje projektom (pokretanje servera, migracija, itd.)
│   ├── graph_explorer/               # Python paket sa Django podešavanjima za projekat
│   │   ├── __init__.py
│   │   ├── settings.py               # Django podešavanja (uključuje INSTALLED_APPS za 'explorer' app i podešava plug-in biblioteke)
│   │   ├── urls.py                   # Glavne URL putanje projekta (uključuje URL-ove iz 'explorer' aplikacije)
│   │   ├── wsgi.py                   # WSGI konfiguracija za deployment
│   │   └── asgi.py                   # ASGI konfiguracija (ako je potreban async support)
│   └── explorer/                     # Django aplikacija unutar projekta (glavni web interfejs za Graph Explorer)
│       ├── __init__.py
│       ├── admin.py                  # Registracija modela u Django admin (ukoliko postoje models.py)
│       ├── apps.py                   # Konfiguracija Django aplikacije (npr. ime aplikacije, default auto field)
│       ├── models.py                 # Django modeli za čuvanje podataka (npr. snimljeni grafovi ili korisničke postavke) – opcionalno
│       ├── forms.py                  # Django forme za unos korisničkih podataka (npr. upload fajla, izbor vizualizatora)
│       ├── views.py                  # Django views (logika kontrolera) za rukovanje zahtevima i korišćenje platforme + plug-inova
│       ├── urls.py                   # URL konfiguracija specifična za ovu aplikaciju (ruta za upload, prikaz grafa itd.)
│       ├── templates/                # HTML template-ovi za prikaz stranica u okviru aplikacije
│       │   └── explorer/             # Direktorijum sa template-ovima ove aplikacije (imenovan po aplikaciji)
│       │       ├── base.html         # Osnovni template (npr. zajednički layout sa uključenim statičkim fajlovima)
│       │       ├── index.html        # Početna stranica sa formom za upload grafa i izbor vizualizacije
│       │       └── graph_view.html   # Stranica koja prikazuje vizualizovani graf korisniku
│       ├── static/                   # Statički fajlovi (CSS, JS, slike) za ovu aplikaciju
│       │   └── explorer/             # Folder za statičke resurse aplikacije (imenovan po aplikaciji radi izolacije)
│       │       ├── css/
│       │       │   └── style.css     # Stilovi za stranice (npr. izgled grafa, layout stranice)
│       │       ├── js/
│       │       │   └── app.js        # JavaScript logika za interakciju na klijentskoj strani (npr. manipulacija prikaza grafa)
│       │       └── images/
│       │           └── logo.png      # (Primer) Slika ili ikonice korišćene u interfejsu
│       └── tests.py                  # Testovi za Django aplikaciju (provere view funkcija, formi, URL-ova)
├── tests/                            # (Alternativno) Direktorijum za sve testove ako ih odvajamo od koda
│   ├── test_api.py                   # Jedinični testovi za 'api' modul
│   ├── test_platform.py              # Testovi za platform modul (učitavanje plug-inova, grafa...)
│   ├── test_data_source_json.py      # Testovi za JSON plug-in (parsiranje JSON, ispravna struktura grafa)
│   ├── test_data_source_xml.py       # Testovi za XML plug-in
│   ├── test_simple_visualizer.py     # Testovi za simple_visualizer (ispravan prikaz/metapodaci)
│   └── test_block_visualizer.py      # Testovi za block_visualizer
├── requirements.txt                  # Spisak zavisnosti projekta (npr. Django, lxml za XML parsiranje, itd.)
├── setup.py                          # Setup skripta za instalaciju paketa (omogućava da se projekat/komponente instaliraju preko pip-a)
├── install.sh                        # (Opcionalno) Skripta za inicijalnu instalaciju okruženja (npr. kreiranje virtualenv-a, instalacija zavisnosti)
└── README.md                         # Osnovna dokumentacija projekta sa uputstvima za razvoj i korišćenje
