import requests
import time
from bs4 import BeautifulSoup as BS
import pandas as pd
import random
import datetime
from urllib.parse import urlencode

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

base_url = 'http://web.legabasket.it/stand/?'

# prima chiamata per estrarre i parametri per ciclare su stagione, girone e giornata
user_agent = random.choice(user_agent_list)
headers = {'User-Agent': user_agent}

req = requests.get(base_url, headers=headers)
soup = BS(req.text, 'html.parser')

all_from_options = soup.find('select', {'name':'from'}).findAll('option')
all_from = {x.text:x['value'] for x in all_from_options}

columns_df = ['Anno', 'Giornata', 'DataOra', 'Squadra Casa', 'Punteggio Casa', 'Team ID', 'Link Boxscore', 'Squadra Trasferta', 'Punteggio Trasferta']
new_games = pd.DataFrame(columns=columns_df)
pos = 0

seasons_to_update = ['2012/2013']
# campionato
for s in seasons_to_update:
	from_param = all_from[s]
	params = {
		'from':from_param
	}

	query_string = urlencode(params)
	full_url = base_url + query_string

	user_agent = random.choice(user_agent_list)
	headers = {'User-Agent': user_agent}

	req = requests.get(full_url, headers=headers)
	soup = BS(req.text, 'html.parser')

	all_lea_options = soup.find('select', {'name':'lea'}).findAll('option')
	all_lea = {x.text:x['value'] for x in all_lea_options}

	for k_lea, v_lea in all_lea.items():
		params['lea'] = v_lea

		query_string = urlencode(params)
		full_url = base_url + query_string

		user_agent = random.choice(user_agent_list)
		headers = {'User-Agent': user_agent}

		req = requests.get(full_url, headers=headers)
		soup = BS(req.text, 'html.parser')

		all_i_options = soup.find('select', {'name':'i'}).findAll('option')
		all_i = {x.text:x['value'] for x in all_i_options}

		for fase_k, fase_v in all_i.items():
			params['i'] = fase_v

			query_string = urlencode(params)
			full_url = base_url + query_string

			user_agent = random.choice(user_agent_list)
			headers = {'User-Agent': user_agent}

			req = requests.get(full_url, headers=headers)
			soup = BS(req.text, 'html.parser')

			all_round_options = soup.find('select', {'name':'round'}).findAll('option')
			all_round = {x.text.strip():x['value'] for x in all_round_options}
			for round_k, round_v in all_round.items():
				params['round'] = round_v
				query_string = urlencode(params)
				full_url = base_url + query_string

				print(full_url)
				user_agent = random.choice(user_agent_list)
				headers = {'User-Agent': user_agent}

				req = requests.get(full_url, headers=headers)
				soup = BS(req.text, 'html.parser')

				table = soup.find('table')

				rows = table.findAll('tr')[1:]

				for count_row, r in enumerate(rows):
					if count_row % 2 == 0:
						giornata = round_k + ' ' + fase_k
						first_row = [s, giornata]
						cols = r.findAll('td')[0:3]
					else:
						second_row = []
						cols = r.findAll('td')[0:2]
					for count_col, c in enumerate(cols):
						if count_row % 2 == 0:
							first_row.append(c.text.strip())
						else:
							second_row.append(c.text.strip())

						if (count_col == 1) & (count_row % 2 == 0):
							team_link = c.find('a')['href']
							team_id = team_link.split('/')[4]

						elif (count_col == 2) & (count_row % 2 == 0):
							game_link = c.find('a')['href'].split('.it')[-1].replace(':','-')

					if count_row % 2 == 0:
						first_row.extend([team_id, game_link])
					else:
						first_row.extend(second_row)
						new_games.loc[pos] = first_row
						pos += 1

# modify dataframe
new_games['Punteggio'] = new_games['Punteggio Casa'] + '-' + new_games['Punteggio Trasferta']
new_games['Data'] = new_games['DataOra'].apply(split_data)
new_games['Data'] = new_games['Data'].apply(invert_data)
#new_games.drop(columns=['Punteggio Casa', 'Punteggio Trasferta'], inplace=True)
new_games = new_games[['Team ID','Anno','Giornata','Data','DataOra','Squadra Casa', 'Punteggio', 'Squadra Trasferta','Link Boxscore']]
new_games.sort_values('Data', inplace=True)


games_df = pd.read_csv('stats_reference/static/all_games.csv')

# save backups
timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
games_df.to_csv('stats_reference/static/backup/all_games_'+timestamp+'.csv',index=False)

final_df = pd.concat([games_df, new_games])
final_df['Game ID'] = final_df['Link Boxscore'].apply(extract_game_id)
final_df.drop_duplicates(subset=['Game ID'], inplace=True, keep='last')
final_df.drop(columns=['Game ID'], inplace=True)
final_df.sort_values('Data', inplace=True)
final_df.to_csv('stats_reference/static/all_games.csv',index=False)

