import requests
import time
from bs4 import BeautifulSoup as BS
import pandas as pd
import random
import datetime

def convert_date(datetime):
    if len(datetime) == 11:
        return datetime[0:-1] + ' 00:00'
    else:
        return datetime[0:10] + ' ' + datetime[10:]

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
details_df = pd.read_pickle('stats_reference/static/games_details.pkl')

# save backups
timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
games_df.to_csv('stats_reference/static/backup/all_games_'+timestamp+'.csv',index=False)
details_df.to_pickle('stats_reference/static/backup/games_details_'+timestamp+'.pkl')

new_details = pd.DataFrame(columns=details_df.columns)
pos = 0
last_season = games_df['Anno'].max()
only_this_season = games_df[games_df['Anno'] == last_season]
only_new_games = only_this_season[only_this_season['Punteggio'] == '0-0']

for i, row in only_new_games.iterrows():
    link = row['Link Boxscore']

    this_url = base_url + link
    print(this_url)
    time.sleep(2)

    user_agent = random.choice(user_agent_list)
    headers = {'User-Agent': user_agent}

    req = requests.get(this_url, headers=headers)
    soup = BS(req.text, 'lxml')
    #import ipdb; ipdb.set_trace()

    result = soup.find("div", {"class": "game-total-result"}).get_text().strip().replace(' ','')
    games_df.loc[i,'Punteggio'] = result

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

            new_details.loc[pos] = this_row
            pos += 1

final_details = pd.concat([details_df, new_details])
final_details.to_pickle("stats_reference/static/games_details.pkl")
games_df.to_csv('stats_reference/static/all_games.csv',index=False)


    