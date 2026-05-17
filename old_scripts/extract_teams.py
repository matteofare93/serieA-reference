import requests
import time
from bs4 import BeautifulSoup as BS
import pandas as pd
import random

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

base_url = 'http://web.legabasket.it/team/counter/prandoni_bergamo/schedule'

col = ['Team ID','Anno','Giornata','Data','Squadra Casa','Punteggio','Squadra Trasferta','Link Boxscore']
games_df = pd.DataFrame(columns=col)

pos = 0
for team_id in range(1,1367):
	this_url = base_url.replace('counter',str(team_id))
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
	    row = [team_id, year]
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
	        games_df.loc[pos] = row
	        pos += 1

games_df.to_pickle("./all_games_with_team_id.pkl")
games_df['Data'] = games_df['Data'].apply(convert_date)
games_df.to_csv('all_games_with_team_id.csv',index=False)