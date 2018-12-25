import time
import re
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

def main():
    print('Starting data pull.')
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(options=chrome_options)
#     driver = webdriver.Chrome() #If you want to see it run browser
    # driver.implicitly_wait(10)
    
    # Get parent HTML
    print("Getting https://hsreplay.net/meta/#tab=tierlist...")
    driver.get('https://hsreplay.net/meta/#tab=tierlist')
    time.sleep(10)
    
    # Grab all meta deck links
    print("Getting nested HTML from https://hsreplay.net/meta/#tab=tierlist...")
    innerHTML = driver.execute_script("return document.body.innerHTML")
    soup = BeautifulSoup(innerHTML, 'html.parser')
    all_decks = soup.find_all("li", class_="archetype-list-item")
    links = list(map(lambda tag: tag.find("a").get('href'), all_decks))
    print(f"deck links found {links}")
    
    # Setup name extract and base url for scrape
    deck_name_extract = re.compile('[^\/]+$')
    base_url = 'https://hsreplay.net'
    winrates = {}
    df_wr = pd.DataFrame()

    # Check each deck/archetype for matchup data
    for link in links:
        deck = deck_name_extract.search(link).group()
        url = base_url + link + '#tab=matchups'
        print(f'{deck}={url}')
        driver.get(url)
        time.sleep(5)
        innerHTML = driver.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(innerHTML, 'html.parser')
        matchups = soup.find_all("a",class_="table-cell", attrs={"aria-describedby": re.compile("column0")})
        winrates[deck] = list(map(lambda matchup: (float(matchup.contents[0].rstrip('%')), deck_name_extract.search(matchup.get('href')).group()), matchups))

        zlst = list(zip(*winrates[deck]))
        s_wr = pd.Series(zlst[0], index=zlst[1])

        df_wr[deck] = s_wr

    driver.quit()

    # Order df/csv columns and save
    df_wr = df_wr.T
    df_wr = df_wr[list(df_wr.index.values)]
    fname = f"hsreplay_winrates_{datetime.today().strftime('%Y%m%d')}.csv"
 
    print(f'Saving {fname}')
    df_wr.to_csv(fname)
    print('Done.')
    

if __name__ == "__main__":
    main()