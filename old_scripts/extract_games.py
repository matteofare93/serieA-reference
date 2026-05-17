import requests
import time
from bs4 import BeautifulSoup as BS
import pandas as pd
import random
import os
import copy

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

teams_df = pd.read_csv('./out_data/all_games_with_team_id.csv')
teams_df = teams_df[teams_df['Team ID'] >= 537]


all_pickles = os.listdir('./out_data/games_details/')
all_pickles = [x for x in os.listdir('./out_data/games_details/') if '.pkl' in x]
pickle_numbers = [int(x.split('.')[0].split('_')[-1]) for x in all_pickles]
max_pickle_number = max(pickle_numbers)
max_pickle = [x for x in all_pickles if str(max_pickle_number) in x][0]
done_games_df = pd.read_pickle('./out_data/games_details/' + max_pickle)

teams_df = teams_df[~teams_df['Link Boxscore'].isin(done_games_df['Partita'])]

columns = ['Partita','Squadra','Titolare','Numero','Giocatore','Punti',
           'Minuti','Falli Commessi','Falli Subiti',
           'Tiri da 2 Realizzati','Tiri da 2 Tentati',
           '% da 2','Schiacciate','Tiri da 3 Realizzati',
           'Tiri da 3 Tentati','% da 3','Tiri Liberi Realizzati',
           'Tiri da Liberi Tentati','% Liberi','Rimbalzi Dif',
           'Rimbalzi Off','Rimbalzi Tot','Stoppate Date',
           'Stoppate Subite','Palle Perse','Palle Recuperate',
           'Assist','Valutazione Lega','Valutazione OER','+/-']

#games_df = pd.DataFrame(columns=columns)
games_df = copy.deepcopy(done_games_df)
pos = games_df.shape[0]
#count = 0
count = int(max_pickle.split('.')[0].split('_')[-1])
print(count)
print(len(teams_df['Link Boxscore'].unique()))
for link in teams_df['Link Boxscore'].unique():

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

            games_df.loc[pos] = this_row
            pos += 1
    count += 1
    if count % 100 == 0:
        games_df.to_pickle("./out_data/games_details/games_details_raw_"+str(count)+".pkl")

games_df.to_pickle("./out_data/games_details_raw.pkl")
#games_df.to_csv('./out_data/games_details_raw.csv',index=False)