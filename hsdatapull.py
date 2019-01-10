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

# import signal
# import atexit

# gdriver = None

# def handle_exit():
#     try:
#         gdriver.quit()
#     except Exception as e:
#         print('No selenium driver.')
#     print('Clean exit')

# atexit.register(handle_exit)
# signal.signal(signal.SIGTERM, handle_exit)
# signal.signal(signal.SIGINT, handle_exit)

def clean_names(names):
    return list(map(lambda deck:deck.replace('-', ' ').title(), list(names)))

def main():
    print('Starting data pull.')
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(options=chrome_options)
    # gdriver = driver
    # driver = webdriver.Chrome() #If you want to see it run browser
    # driver.implicitly_wait(10)
    
    # Get parent HTML
    print("Getting https://hsreplay.net/meta/#tab=archetypes...")
    driver.get('https://hsreplay.net/meta/#tab=archetypes')
    time.sleep(10)
    
    # Grab all meta deck links
    print("Getting nested HTML from https://hsreplay.net/meta/#tab=tierlist...")
    innerHTML = driver.execute_script("return document.body.innerHTML")
    soup = BeautifulSoup(innerHTML, 'html.parser')
    all_decks = soup.find_all("a",class_="table-cell", attrs={"aria-describedby": re.compile("column0")})
    archetypes = list(map(lambda tag: (tag.get('href'), tag.contents[0].rstrip('%')), all_decks))
    archetypes_f = list(filter(lambda archetype: archetype[0] is not None, archetypes))
    links = [x[0] for x in archetypes_f]
    
    deck_name_extract = re.compile('[^\/]+$')
    
    all_archetypes = list(map(lambda link: deck_name_extract.search(link).group(), links))
    
    print(f"archetypes found {all_archetypes}")
    
    # Setup name extract and base url for scrape

    base_url = 'https://hsreplay.net'
    winrates = {}
    df_wr = pd.DataFrame(index=all_archetypes, columns=all_archetypes)

    # Check each deck/archetype for matchup data
    for link in links:
        deck = deck_name_extract.search(link).group()
        url = base_url + link + '#tab=matchups'
        print(f'{deck}={url}')
        driver.get(url)
        # gdriver = driver
        time.sleep(5)
        innerHTML = driver.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(innerHTML, 'html.parser')
        matchups = soup.find_all("a",class_="table-cell", attrs={"aria-describedby": re.compile("column0")})
        winrates[deck] = list(map(lambda matchup: (float(matchup.contents[0].rstrip('%')), deck_name_extract.search(matchup.get('href')).group()), matchups))

        zlst = list(zip(*winrates[deck]))
        try:
            s_wr = pd.Series(zlst[0], index=zlst[1])
        except IndexError as e:
            print(f"Unable to get winrates for: {deck}")
            continue

        df_wr[deck] = s_wr

    driver.quit()

    # Order df/csv columns and save        
    df_wr.columns = clean_names(df_wr.columns.values)
    df_wr.index = clean_names(df_wr.index.values)

    df_wr = df_wr.T
    # try:
    #     df_wr = df_wr[list(df_wr.index.values)]
    # except KeyError as e:
    #     print(f"Unable to sort decks due to: {e}")
    
    fname = f"hsreplay_winrates_{datetime.today().strftime('%Y%m%d')}.csv"
 
    print(f'Saving {fname}')
    df_wr.to_csv(fname)
    print('Done.')
    

if __name__ == "__main__":
    main()