# FR03: Release Plan - CI/CD Workflows

## Problem

Aktuell gibt es keine automatisierte Validierung oder Release-Prozesse:

- Keine Prüfung bei Push/PR ob die Integration valide ist
- Keine automatische Erstellung von Release-Artifacts
- Manueller, fehleranfälliger Release-Prozess

## Ziel

Automatisierte CI/CD Pipeline mit:

1. **Validierung** bei jedem Push und Pull Request
2. **Release Artifact** (ZIP) bei GitHub Release automatisch erstellen

## Lösung

### Ordnerstruktur

```
.github/
└── workflows/
    ├── validate.yaml    # Validierung bei Push/PR
    └── release.yml      # Release-Automation
```

### Workflow 1: validate.yaml

Validiert die Integration bei jedem Push und Pull Request.

```yaml
name: Validate

on:
  push:
  pull_request:
  schedule:
    - cron: "0 0 * * *"
  workflow_dispatch:

jobs:
  hassfest:
    name: Hassfest
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: home-assistant/actions/hassfest@master

  hacs:
    name: HACS
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: HACS validation
        uses: hacs/action@main
        with:
          category: integration
```

**Was wird geprüft:**

| Job | Prüft |
|-----|-------|
| **hassfest** | manifest.json, translations, config_flow, dependencies |
| **hacs** | HACS-Kompatibilität (hacs.json, Struktur, README) |

**Wann wird ausgeführt:**
- Bei jedem Push
- Bei jedem Pull Request
- Täglich um Mitternacht (erkennt Breaking Changes durch HA-Updates)
- Manuell auslösbar

### Workflow 2: release.yml

Erstellt automatisch ein ZIP-Archiv bei GitHub Release.

```yaml
name: Release

on:
  release:
    types:
      - published

permissions:
  contents: write

jobs:
  release:
    name: Release WhenHub
    runs-on: ubuntu-latest
    steps:
      - name: Checkout the repository
        uses: actions/checkout@v4

      - name: Create zip package
        run: |
          cd "${{ github.workspace }}/custom_components/whenhub"
          zip whenhub.zip -r ./

      - name: Upload zip to release
        uses: softprops/action-gh-release@v2
        with:
          files: ${{ github.workspace }}/custom_components/whenhub/whenhub.zip
```

**Was passiert:**
1. Bei "Publish Release" auf GitHub wird der Workflow gestartet
2. Der komplette `custom_components/whenhub/` Ordner wird als ZIP gepackt
3. Das ZIP wird automatisch an die Release-Assets angehängt

## Release-Workflow (manuell)

Nach Implementierung dieser Workflows:

1. **Version in manifest.json erhöhen** (siehe FR01)
2. **Commit & Push**
   ```bash
   git add .
   git commit -m "Bump version to X.Y.Z"
   git push
   ```
3. **GitHub Release erstellen**
   - Auf GitHub → Releases → "Create new release"
   - Tag: `vX.Y.Z` (z.B. `v2.2.0`)
   - Title: `vX.Y.Z`
   - Release Notes schreiben
   - "Publish release" klicken
4. **Warten** - Workflow erstellt automatisch `whenhub.zip`
5. **Fertig** - ZIP ist im Release verfügbar

## Voraussetzungen

### hacs.json

Für HACS-Validierung muss eine `hacs.json` im Root existieren:

```json
{
  "name": "WhenHub",
  "render_readme": true
}
```

**Status:** Prüfen ob vorhanden, ggf. erstellen.

## Betroffene Dateien

| Datei | Aktion |
|-------|--------|
| `.github/workflows/validate.yaml` | NEU erstellen |
| `.github/workflows/release.yml` | NEU erstellen |
| `hacs.json` | Prüfen/erstellen |

## Vorteile

- **Frühzeitige Fehlererkennung** durch hassfest bei jedem Push
- **Konsistente Releases** durch automatisierte ZIP-Erstellung
- **HACS-Readiness** durch regelmäßige Validierung
- **Tägliche Checks** erkennen Breaking Changes durch HA-Updates

## Referenz: solstice_season

Diese Workflows sind 1:1 aus solstice_season übernommen und dort erfolgreich im Einsatz:
- [validate.yaml](https://github.com/moerk-o/ha-solstice_season/blob/main/.github/workflows/validate.yaml)
- [release.yml](https://github.com/moerk-o/ha-solstice_season/blob/main/.github/workflows/release.yml)

## Status

- [x] `.github/workflows/` Ordner erstellen
- [x] `validate.yaml` erstellen
- [x] `release.yml` erstellen
- [x] `hacs.json` prüfen/erstellen
- [x] Push und Workflow-Ausführung testen
- [ ] Test-Release erstellen

**Erledigt:** 2026-01-28 (Commit a322ce9)

**Hinweis:** Test-Release steht noch aus - wird beim nächsten echten Release getestet.
