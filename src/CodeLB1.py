from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager 
import time
from bs4 import BeautifulSoup
import pandas as pd
import mysql.connector

# Suchmaschine auswählen (Flag setzen)
USE_GOOGLE = True
USE_BING = False
USE_DUCKDUCKGO = False

# URL-Vorlagen für jede Suchmaschine
SEARCH_ENGINES = {
    "google": "https://www.google.com/search?q={query}&start={start}",
    "bing": "https://www.bing.com/search?q={query}&first={start}",
    "duckduckgo": "https://duckduckgo.com/?q={query}&s={start}"
}

# Aktive Suchmaschine ermitteln
if USE_GOOGLE:
    current_engine = "Google"
elif USE_BING:
    current_engine = "Bing"
elif USE_DUCKDUCKGO:
    current_engine = "DuckDuckGo"
else:
    current_engine = "Unknown"

# Funktion, um die aktive Suchmaschine zu ermitteln
def get_search_url(query):
    if USE_GOOGLE:
        return SEARCH_ENGINES["google"].format(query=query.replace(" ", "+"), start=0)
    elif USE_BING:
        return SEARCH_ENGINES["bing"].format(query=query.replace(" ", "+"), start=1)
    elif USE_DUCKDUCKGO:
        return SEARCH_ENGINES["duckduckgo"].format(query=query.replace(" ", "+"), start=0)
    else:
        raise ValueError("Keine Suchmaschine ausgewählt!")


# Initialize WebDriver mit webdriver-manager
try: 
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()

    options.add_argument("--window-size=1920,1080")  # Set window size
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(service=service, options=options)
except Exception as e:
    print(f"Fehler bei der Initialisierung des WebDrivers: {e}")
    exit(1)
    
    
# Öffnet InputM122.txt und liest Suchbegriffe ein
try: 
    with open("./data/InputM122.txt", "r", encoding="utf-8") as f:
        search_terms = [line.strip() for line in f if line.strip()]  # leere Zeilen ignorieren
except FileNotFoundError:
    print("Die Datei InputM122.txt wurde nicht gefunden.")
    driver.quit()
    exit(1)
    
all_results = []

pages_to_scrape = 1  # Anzahl Seiten die gelesen werden pro Suchbegriff

# Schleife durch Suchbegriffe
for term in search_terms:
    try: 
        print(f"Suche: {term}")
        search_url = get_search_url(term)
        driver.get(search_url)
        
        time.sleep(2) # Warten bis Seite lädt

        page_html = driver.page_source
        soup = BeautifulSoup(page_html, 'html.parser')
        
        # Je nach Suchmaschine unterschiedliche Parsing-Logik
        if current_engine.lower() == "google":
            container = soup.find("div", {"class":"dURPMd"})
            if container:
                allData = container.find_all("div", {"class":"Ww4FFb"})
            else:
                allData = []
        elif current_engine.lower() == "bing":
            allData = soup.find_all("li", {"class":"b_algo"})
        elif current_engine.lower() == "duckduckgo":
            allData = soup.find_all("article", {"data-testid": "result"})
        else:
            allData = []

        obj = {}
        l = []
        
        # Daten extrahieren
        print(len(allData))
        for entry in allData:
            obj = {}

            if current_engine.lower() == "google":
                try:
                    obj["title"] = entry.find("h3").text
                except:
                    obj["title"] = None
                try:
                    obj["link"] = entry.find("a").get('href')
                except:
                    obj["link"] = None
                try:
                    obj["description"] = entry.find("div", {"class":"VwiC3b"}).text
                except:
                    obj["description"] = None

            elif current_engine.lower() == "bing":
                try:
                    obj["title"] = entry.find("h2").text
                except:
                    obj["title"] = None
                try:
                    obj["link"] = entry.find("a").get('href')
                except:
                    obj["link"] = None
                try:
                    obj["description"] = entry.find("p").text if entry.find("p") else None
                except:
                    obj["description"] = None

            elif current_engine.lower() == "duckduckgo":
                try:
                    title_tag = entry.find("a", {"data-testid": "result-title-a"})
                    obj["title"] = title_tag.get_text() if title_tag else None
                except:
                    obj["title"] = None
                try:
                    obj["link"] = title_tag.get('href') if title_tag else None
                except:
                    obj["link"] = None
                try:
                    obj["description"] = desc_tag = entry.find("div", {"data-testid": "result-snippet"})
                    obj["description"] = desc_tag.get_text() if desc_tag else None
                except:
                    obj["description"] = None

            obj["search_term"] = term # Suchbegriff speichern im Ergebnis
            obj["search_engine"] = current_engine

            l.append(obj)
            
        all_results.extend(l) # Sammelt alle Resultate 
    except Exception as e:
        print(f"Fehler beim Scraping von '{term}': {e}")
        continue # Versuch mit nächstem Begriff
    
# Resultate in CSV speichern
try: 
    df = pd.DataFrame(all_results)
    df.to_csv('./data/search_results.csv', index=False, encoding='utf-8')
except Exception as e:
    print(f"Fehler beim Speichern der CSV-Datei: {e}")

##################################################################
# Daten in MySQL Datenbank speichern

# Verbindung zu Datenbank herstellen
try: 
    conn = mysql.connector.connect(
        host="localhost",
        user="lin",
        password="z3a",
    )
    cursor = conn.cursor()

    # Datenbank erstellen
    cursor.execute("CREATE DATABASE IF NOT EXISTS M122_results")
    conn.commit()
    # Datenbank auswählen
    conn.database = "M122_results"
    # Tabelle erstellen
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS search_results (
        id INT AUTO_INCREMENT PRIMARY KEY,
        search_term VARCHAR(255),
        title TEXT,
        link TEXT,
        description TEXT,
        search_engine VARCHAR(50)
    );
    """)
    conn.commit()
    # Tabellen mit Daten befüllen
    for _, row in df.iterrows():
        try: 
            cursor.execute("""
                INSERT INTO search_results (search_term, title, link, description, search_engine)
                VALUES (%s, %s, %s, %s, %s)
            """, (row['search_term'], row['title'], row['link'], row['description'], row['search_engine']))
        except Exception as e:
            print(f"Fehler beim Einfügen der Zeile '{row['search_term']}': {e}")

    conn.commit()
except mysql.connector.Error as err:
    print(f"Fehler bei der Datenbankoperation: {err}")
finally:
    try: 
        cursor.close()
        conn.close()
    except:
        pass

########################################

print(f"{len(all_results)} Ergebnisse gespeichert.")
driver.quit()