from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager 
import time
from bs4 import BeautifulSoup
import pandas as pd
import mysql.connector


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
    with open("InputM122.txt", "r", encoding="utf-8") as f:
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
        search_url = f"https://www.google.com/search?q={term.replace(' ', '+')}"
        driver.get(search_url)
        
        time.sleep(2) # Wait for the page to load

        page_html = driver.page_source

        soup = BeautifulSoup(page_html, 'html.parser')
        obj = {}
        l = []

        allData = soup.find("div", {"class":"dURPMd"}).find_all("div", {"class":"Ww4FFb"})
        print(len(allData))

        for i in range(len(allData)):
            try:
                obj["title"] = allData[i].find("h3").text
            except:
                obj["title"] = None

            try:
                obj["link"] = allData[i].find("a").get('href')
            except:
                obj["link"] = None

            try:
                obj["description"] = allData[i].find("div", {"class":"VwiC3b"}).text
            except:
                obj["description"] = None

            obj["search_term"] = term # Add search term to the object
            l.append(obj)
            obj = {}
            
        all_results.extend(l) # Collect results from all search terms
    except Exception as e:
        print(f"Fehler beim Scraping von '{term}': {e}")
        continue # Try Continue with the next search term
    
# Save all results to a single CSV file
try: 
    df = pd.DataFrame(all_results)
    df.to_csv('google_multiple.csv', index=False, encoding='utf-8')
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
    CREATE TABLE IF NOT EXISTS google_results (
        id INT AUTO_INCREMENT PRIMARY KEY,
        search_term VARCHAR(255),
        title TEXT,
        link TEXT,
        description TEXT
    );
    """)
    conn.commit()

    for _, row in df.iterrows():
        try: 
            cursor.execute("""
                INSERT INTO google_results (search_term, title, link, description)
                VALUES (%s, %s, %s, %s)
            """, (row['search_term'], row['title'], row['link'], row['description']))
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