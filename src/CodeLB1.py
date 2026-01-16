from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager 
import time
from bs4 import BeautifulSoup
import pandas as pd
import mysql.connector

# Suchmaschine auswählen
USE_GOOGLE = False
USE_BING = False
USE_DUCKDUCKGO = True

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
def get_search_url(query, page=0):
    start = page * 10  # Position für Pagination
    if USE_GOOGLE:
        return SEARCH_ENGINES["google"].format(query=query.replace(" ", "+"), start=start)
    elif USE_BING:
        return SEARCH_ENGINES["bing"].format(query=query.replace(" ", "+"), start=start+1)
    elif USE_DUCKDUCKGO:
        return SEARCH_ENGINES["duckduckgo"].format(query=query.replace(" ", "+"), start=start)
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
    
    
# Open Google Search URL
try: 
    with open("./data/InputM122.txt", "r", encoding="utf-8") as f:
        search_terms = [line.strip() for line in f if line.strip()]  # leere Zeilen ignorieren
except FileNotFoundError:
    print("Die Datei InputM122.txt wurde nicht gefunden.")
    driver.quit()
    exit(1)
    
all_results = []

#Iterate through each search term in InputM122.txt
pages_to_scrape = 1  # Number of pages to scrape per search

for term in search_terms:
    try: 
        print(f"Suche: {term}")
        search_url = get_search_url(term, page=0) #page= 0 for first page
        #search_url = f"https://www.google.com/search?q={term.replace(' ', '+')}"
        driver.get(search_url)
        
        time.sleep(2) # Wait for the page to load

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

        #allData = soup.find("div", {"class":"dURPMd"}).find_all("div", {"class":"Ww4FFb"})
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

            obj["search_term"] = term # Add search term to the object
            obj["search_engine"] = current_engine

            l.append(obj)
            
        all_results.extend(l) # Collect results from all search terms
    except Exception as e:
        print(f"Fehler beim Scraping von '{term}': {e}")
        continue # Try Continue with the next search term
    
# Save all results to a single CSV file
try: 
    df = pd.DataFrame(all_results)
    df.to_csv('./data/search_results.csv', index=False, encoding='utf-8')
except Exception as e:
    print(f"Fehler beim Speichern der CSV-Datei: {e}")

##################################################################3
# Load data into MySQL database MariaDB

# Connect to the database/ server
try: 
    conn = mysql.connector.connect(
        host="localhost",
        user="lin",
        password="z3a",
    )
    cursor = conn.cursor()

    # Create database and table if not exists
    cursor.execute("CREATE DATABASE IF NOT EXISTS M122_results")
    conn.commit()
    # Switch to the database
    conn.database = "M122_results"
    # Create table
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