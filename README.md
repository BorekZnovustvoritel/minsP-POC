# minsP projekt

Jedná se o jednoduchý eshop s využitím FastAPI. 
Projekt slouží jen jako ukázka implementace a není
vhodný k ostrému nasazení.

## Jak spustit

Projekt byl vytvořen pro systém Linux s nainstalovanými
balíčky `python3` a `python3-devel`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install pdm
pdm install
python3 main.py
```

Poté se rozběhne server přístupný na `http://localhost:8080/`.

V databázi jsou nahrány některé produkty pro rychlejší vyzkoušení.
Další produkty lze přidat pomocí funkcí v souboru `admin.py`.
Při přidání dalších HTML souborů vyžadujících překlad je nutné
spustit script `python3 generate_translation.py` a poté vygenerovat
nové překlady pomocí:
```bash
for lang in translations/*; do msgfmt -o "${lang}/LC_MESSAGES/app.mo" "${lang}/LC_MESSAGES/app.po"; done
```
