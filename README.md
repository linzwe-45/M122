# Multi-Engine Web Scraper (M122)

Dieses Python-Programm automatisiert die Suche über verschiedene Suchmaschinen (**Google**, **Bing**, **DuckDuckGo**). Es extrahiert Titel, Links sowie Beschreibungen der Suchergebnisse und speichert diese sowohl in einer **CSV-Datei** als auch in einer **MariaDB/MySQL-Datenbank**.

---

## Funktionen
* **Multi-Engine Support:** Flexibles Scraping von Google, Bing oder DuckDuckGo (einstellbar via Flags).
* **Batch-Verarbeitung:** Suchbegriffe werden automatisch aus einer lokalen Textdatei gelesen.
* **Dynamisches Scraping:** Nutzung von Selenium zur Erfassung von Inhalten, die per JavaScript geladen werden.
* **Duale Datenspeicherung:**
    * Export aller Ergebnisse in `google_multiple.csv`.
    * Automatischer Import in eine lokale SQL-Datenbank (`M122_results`).

---

## Voraussetzungen

### 1. System-Umgebung
* **Python 3.x**
* **Google Chrome** (installiert)
* **Laufender MySQL/MariaDB-Server** (z. B. via XAMPP oder Docker)

### 2. Python-Bibliotheken
Installiere die notwendigen Packages mit folgendem Befehl:

```bash
pip install selenium webdriver-manager beautifulsoup4 pandas mysql-connector-python
```

## Konfiguration
**Datenbank-Verbindung**
* Das Skript ist standardmäßig auf meine lokalen Zugangsdaten eingestellt:
```plaintext
Host: localhost

User: lin

Passwort: z3a
```

* **Wichtig**:  Passe die Parameter im mysql.connector.connect(...) Block direkt im Quellcode an damit sie zu deinen Datenbank-Konfigurationen passen.
---
**Inputfile - Suchbegriffe hinterlegen**
* Erstelle im Projektverzeichnis eine Datei namens InputM122.txt. Füge dort deine Suchbegriffe ein (einer pro Zeile):
```Plaintext
Python Web Scraping
MariaDB SQL Tutorial
Selenium Automation
Engine auswählen
```
**Suchmaschine wähle**
* Im Kopfbereich des Skripts die gewünschte Suchmaschine auswählen, indem du den Wert auf True setzt:

```Python
USE_GOOGLE = False
USE_BING = False
USE_DUCKDUCKGO = True  # Beispiel: DuckDuckGo ist aktiv
```
---
## Benutzung
* Server starten: Stelle sicher, dass dein MySQL/MariaDB-Dienst läuft.

* Input vorbereiten: Überprüfe, ob die InputM122.txt befüllt ist.

* Skript ausführen:

```Bash
python dein_skriptname.py
```
* Ergebnisse prüfen:
    - Die Konsole zeigt die Anzahl der gefundenen Ergebnisse an.
    - Die Datei search_results.csv wird im selben Ordner erstellt/aktualisiert.
    - Die Datenbank M122_results und die Tabelle search_results werden automatisch befüllt.
---
# Autor
**Lina Zweifel**


Beispiel Input & Output
