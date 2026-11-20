# Konzertkalender

Ein alter Kindle Paperwhite 4 als E-Ink-Konzertkalender. Jeden Montag holt GitHub automatisch die
Programme von zehn Clubs in Bern und Fribourg. Es wählt die Konzerte, Partys und DJ-Sets von
Donnerstag- bis Samstagabend aus und erstellt daraus:

- `docs/kalender.png`: das Bild für den Schlafbildschirm des Kindle (1072 × 1448, Graustufen)
- `docs/index.html`: dasselbe Bild, auf eine Bildschirmhöhe skaliert und antippbar; jede Zeile öffnet
  die Event-Seite des Clubs, die Fusszeile und «+ N weitere» öffnen die vollständige Liste
- `docs/liste.html`: alle Events als schlichte Liste (nichts geht verloren, auch wenn das Bild Titel
  kürzen oder an sehr vollen Abenden Events weglassen muss)
- `docs/kalender.json`: dieselben Daten maschinenlesbar

Alles ist gratis: GitHub Actions und GitHub Pages, kein eigener Server, keine KI und kein Abo.

## Ablauf

```
Montag früh · GitHub Actions
  10 Club-Websites lesen → Do–Sa-Abende auswählen → Bild + Webseite erzeugen → docs/ committen
                                                                                │ GitHub Pages
Kindle (gejailbreakt)                                                           ▼
  schläft → zeigt kalender.png · wacht alle 12 h kurz auf → lädt neue Ausgabe
  Power-Taste → öffnet index.html im Browser → Eintrag antippen → Event-Seite des Clubs
```

## Clubs

| Schlüssel       | Club                          | Gelesen aus                                         |
|-----------------|-------------------------------|-----------------------------------------------------|
| `dachstock`     | Dachstock (Reitschule)        | strukturierte Event-Daten (schema.org / JSON-LD)    |
| `gaskessel`     | Gaskessel                     | Programmseite mit Genre-Zeile und Türöffnung        |
| `isc`           | ISC Club                      | Programm + Startzeit von der Detailseite            |
| `roessli`       | Rössli (Reitschule)           | Event-Karten, Tags gefiltert über die Genre-Liste   |
| `cafete`        | Cafete (Reitschule)           | Programmseite mit «Style:»-Zeile                    |
| `cafe_kairo`    | Café Kairo                    | Programm; Genres aus dem Beschreibungstext          |
| `progr`         | PROGR (inkl. bee-flat u. a.)  | Agenda; nur Musik-Kategorien                        |
| `bad_bonn`      | Bad Bonn (Düdingen)           | Programm; Genres aus der Detailbeschreibung         |
| `fri_son`       | Fri-Son (Fribourg)            | Programm mit Genre-Feldern                          |
| `nouveau_monde` | Le Nouveau Monde (Fribourg)   | Agenda mit Kategorie-Kürzeln (crt, fte …)           |

Die Genres stammen direkt von den Clubs. Fehlt dort ein Genre, sucht `config/genres.toml` (eine
Wortliste) passende Begriffe in der Beschreibung.

## Lokal ausprobieren

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest                                  # Tests (offline; Kindle-Skripte mit busybox)
.venv/bin/python -m konzertkalender --ausgabe preview --datum 2026-11-23
```

`--datum` legt fest, welches Wochenende erzeugt wird (Montag bis Samstag ergeben das Do–Sa derselben
Woche). Das Ergebnis liegt in `preview/` und wird nicht committet.

## Einrichtung

### GitHub (einmalig)

1. Ein öffentliches Repository `Konzertkalender` anlegen und diesen Code pushen.
2. Unter **Settings → Pages** als Source «Deploy from a branch» wählen, dann Branch `main` und Ordner `/docs`.
3. Unter **Actions → Wochen-Update → Run workflow** eine neue Ausgabe erzeugen (sonst montags automatisch).
4. Bild und Seite sind danach erreichbar unter `https://xkirmix.github.io/Konzertkalender/kalender.png`
   bzw. `https://xkirmix.github.io/Konzertkalender/`.

### Kindle (nach dem Jailbreak, z. B. mit WinterBreak2)

1. Den Ordner `kindle/konzertkalender/` nach `/mnt/us/konzertkalender/` kopieren und in
   `konzertkalender.conf` die beiden Adressen prüfen. Optional ein `startbild.png` dazulegen: Das
   zeigt der Kindle, bis der erste Download klappt.
2. Die Dateien aus `kindle/documents/` nach `/mnt/us/documents/` kopieren. Der Jailbreak zeigt
   `.sh`-Dateien dort als Einträge in der Bibliothek («Scriptlets»).
3. Am Kindle **«Konzertkalender starten»** antippen und danach die Power-Taste drücken. Im Schlaf
   zeigt er jetzt den Kalender.

Nach einem Neustart des Kindle (z. B. bei leerem Akku) einmal «Konzertkalender starten» antippen.
«Konzertkalender stoppen» macht ihn wieder zum normalen Kindle. «Konzertkalender Diagnose» schreibt
Infos zur Fehlersuche nach `konzertkalender/diagnose.txt`.

Der Dienst läuft aus einer Kopie im Arbeitsspeicher (`/tmp/konzertkalender`) und legt Bild,
Zeitstempel und Log unter `/var/local/konzertkalender` ab. So läuft er weiter, während der Kindle
als USB-Laufwerk am Computer hängt.

So holt der Kindle neue Ausgaben:

- **Auf Akku:** Vor dem Tiefschlaf stellt der Dienst den Wecker (RTC) auf die nächste fällige
  Aktualisierung (alle `REFRESH_HOURS`, nach einem Fehler nach `RETRY_MINUTES`).
- **Am Ladekabel** schläft der Kindle oft nie richtig ein; dann prüft ein Takt alle 30 Minuten, ob
  eine Ausgabe fällig ist.
- Das Bild wird nur neu gezeichnet, wenn der Kindle schläft – nie, während jemand liest.
- Liegen neue Skripte oder Einstellungen auf dem Kindle, startet sich der Dienst beim nächsten
  Einschlafen selbst neu; «Konzertkalender starten» ist dafür nicht nötig.
- `DEBUG_EVENTS=1` in `konzertkalender.conf` schreibt jedes Schlaf-/Aufwach-Signal ins Log.

## Anpassen

- **Clubs, Abendbeginn, Arten** (`konzert`, `party`, `andere`): `config/kalender.toml`. Pro Abend
  stehen die Events nach Club gruppiert, in der Reihenfolge der Club-Liste dort, innerhalb eines
  Clubs nach Uhrzeit.
- **Genres:** `config/genres.toml`
- **Neuer Club:** eine Klasse unter `src/konzertkalender/venues/<region>/` anlegen, die
  `VenueSource` erfüllt, in `venues/venue_registry.py` eintragen und einen Test mit Beispielseite
  in `tests/` ergänzen.

## Wenn etwas nicht stimmt

- **«keine Daten: X» in der Fusszeile:** Die Website von X hat sich vermutlich geändert. Die Tests
  und der Log unter **Actions** zeigen, welcher Parser angepasst werden muss.
- **Kindle zeigt nichts Neues:** Eine Kopie des Logs liegt in
  `/mnt/us/konzertkalender/konzertkalender.log`; «Konzertkalender Diagnose» sammelt den Rest.
- **Kein Update an einem Montag:** Der Workflow schlägt fehl, wenn kein einziger Club gelesen werden
  konnte. Die alte Ausgabe bleibt dann online, und GitHub schickt eine E-Mail.

Schrift: Inter (SIL Open Font License, siehe `src/konzertkalender/assets/fonts/LICENSE-Inter.txt`).
