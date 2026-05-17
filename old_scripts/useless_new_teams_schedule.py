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

def split_data(dateora):
    return dateora.split(' ')[0]

def invert_data(data):
    day, month, year = data.split('/')
    return year + '/' + month + '/' + day

def extract_game_id(link):
    g_id = link.split('/')[2]
    return g_id

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

base_url = 'http://web.legabasket.it/team'

games_df = pd.read_csv('stats_reference/static/all_games.csv')

# save backups
timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
games_df.to_csv('stats_reference/static/backup/all_games_'+timestamp+'.csv',index=False)

cols = ['Team ID','Anno','Giornata','Data','Squadra Casa','Punteggio','Squadra Trasferta','Link Boxscore']
new_games = pd.DataFrame(columns=cols)
pos = 0

user_agent = random.choice(user_agent_list)
headers = {'User-Agent': user_agent}

req = requests.get(base_url, headers=headers)
soup = BS(req.text, 'html.parser')

all_a = soup.findAll('a')
all_href = [x['href'] for x in all_a if 'team' in x['href'] and '?' not in x['href'] and 'php' not in x['href']]
all_href = list(set(all_href))

team_ids = [int(x.split('/')[2]) for x in all_href]

base_url = 'http://web.legabasket.it/team/counter/prandoni_bergamo/schedule'
for t_id in team_ids:
    this_url = base_url.replace('counter',str(t_id))
    print(this_url)
    time.sleep(2)

    user_agent = random.choice(user_agent_list)
    headers = {'User-Agent': user_agent}

    req = requests.get(this_url, headers=headers)
    soup = BS(req.text, 'lxml')

    year = soup.find('div', {'class':'title'}).get_text().strip().split(' ')[-1]
    try:
        table = soup.findAll('table')[0]
    except:
        print('Not found')
        continue

    for i,tr in enumerate(table.findAll('tr')):
        row = [t_id, year]
        for i,td in enumerate(tr.findAll('td')):
            try:
                a = td.findAll('a')
                texts = [x.text for x in a]
            except IndexError:
                continue
            row.extend(texts)
            if i == 2:
                link = a[0]['href']
        if len(row) > 2:
            row.append(link)
            new_games.loc[pos] = row
            pos += 1

# clean and modify data
new_games.sort_values('Team ID', inplace=True)
new_games = new_games.drop_duplicates(subset=['Link Boxscore'], keep='first')
new_games['Data'] = new_games['Data'].apply(convert_date)
#new_games['Data'] = pd.to_datetime(new_games['Data'], format='%d/%m/%Y %H:%M', errors='ignore')
new_games.rename(columns={'Data':'DataOra'}, inplace=True)
import ipdb; ipdb.set_trace()
new_games['Data'] = new_games['DataOra'].apply(split_data)
new_games['Data'] = new_games['Data'].apply(invert_data)
new_games['Squadra Casa'] = new_games['Squadra Casa'].str.strip()
new_games['Squadra Trasferta'] = new_games['Squadra Trasferta'].str.strip()
new_games['Anno'] = new_games['Anno'].str.strip()
new_games = new_games[['Team ID',
 'Anno',
 'Giornata',
 'Data',
 'DataOra',
 'Squadra Casa',
 'Punteggio',
 'Squadra Trasferta',
 'Link Boxscore']]
new_games.sort_values(['Anno','Data'], inplace=True)

final_df = pd.concat([games_df, new_games])
final_df['Game ID'] = final_df['Link Boxscore'].apply(extract_game_id)
final_df.drop_duplicates(subset=['Game ID'], inplace=True, keep='last')
final_df.drop(columns=['Game ID'], inplace=True)
import ipdb; ipdb.set_trace()