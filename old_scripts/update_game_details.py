import requests
import time
from bs4 import BeautifulSoup as BS
import pandas as pd
import random
import os
import copy
import datetime

user_agent_list = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
]

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", 
    "Accept-Encoding": "gzip, deflate", 
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8", 
    "Dnt": "1", 
    "Host": "httpbin.org", 
    "Upgrade-Insecure-Requests": "1", 
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36", 
  }

base_url = 'http://web.legabasket.it'

games_df = pd.read_csv('stats_reference/static/all_games.csv')
game_details_df = pd.read_pickle('stats_reference/static/games_details.pkl')

games_df = games_df[games_df['Team ID'] >= 537]
new_games = games_df[~games_df['Link Boxscore'].isin(game_details_df['Partita'].tolist())]
new_games = new_games[~new_games['Link Boxscore'].str.contains('0-0')]

columns = ['Partita','Squadra','Titolare','Numero','Giocatore','Punti',
           'Minuti','Falli Commessi','Falli Subiti',
           'Tiri da 2 Realizzati','Tiri da 2 Tentati',
           '% da 2','Schiacciate','Tiri da 3 Realizzati',
           'Tiri da 3 Tentati','% da 3','Tiri Liberi Realizzati',
           'Tiri da Liberi Tentati','% Liberi','Rimbalzi Dif',
           'Rimbalzi Off','Rimbalzi Tot','Stoppate Date',
           'Stoppate Subite','Palle Perse','Palle Recuperate',
           'Assist','Valutazione Lega','Valutazione OER','+/-']

new_game_details = pd.DataFrame(columns=columns)
pos = 0

#import ipdb; ipdb.set_trace()
for link in new_games['Link Boxscore'].unique():

    this_url = base_url + link
    print(this_url)
    time.sleep(2)

    user_agent = random.choice(user_agent_list)
    headers = {'User-Agent': user_agent}

    req = requests.get(this_url, headers=headers)
    soup = BS(req.text, 'lxml')

    tables = soup.findAll('table')[1:3]
    for table in tables:
        for i, tr in enumerate(table.findAll('tr')):
            this_row = [link]
            if i == 0:
                team = tr.findAll('th')[0].text
                continue
            if i == 1:
                continue
            this_row.append(team)
            for td in tr.findAll('td'):
                this_row.append(td.get_text().strip())

            new_game_details.loc[pos] = this_row
            pos += 1

# save backup
timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
game_details_df.to_pickle('stats_reference/static/backup/games_details_'+timestamp+'.pkl')

final_details = pd.concat([game_details_df, new_game_details])
final_details.to_pickle("stats_reference/static/games_details.pkl")

