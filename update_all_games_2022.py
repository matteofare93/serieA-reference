import requests
import time
from bs4 import BeautifulSoup as BS
import pandas as pd
import random
import datetime
from urllib.parse import urlencode
import re

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

base_url = 'https://legabasket.it/lba/6/calendario/calendar?'

# s=2021&c=465&p=5&t=0

# prima chiamata per estrarre i parametri per ciclare su stagione, girone e giornata
user_agent = random.choice(user_agent_list)
headers = {'User-Agent': user_agent}

req = requests.get(base_url, headers=headers)
soup = BS(req.text, 'html.parser')

all_from_options = soup.find('select', {'id':'calendar_season'}).findAll('option')
all_from = {x.text:x['value'] for x in all_from_options}

columns_df = ['Anno', 'Giornata', 'Squadra Casa', 'Punteggio', 'Link Boxscore', 'Squadra Trasferta', 'DataOra', 'Team ID']
new_games = pd.DataFrame(columns=columns_df)
pos = 0

seasons_to_update = ['2023/2024']

# stagione
for s in seasons_to_update:
	print(s)
	season_param = all_from[s]
	params = {
		's': season_param
	}

	query_string = urlencode(params)
	full_url = base_url + query_string

	user_agent = random.choice(user_agent_list)
	headers = {'User-Agent': user_agent}

	req = requests.get(full_url, headers=headers)
	soup = BS(req.text, 'html.parser')

	all_comp_option = soup.find('select', {'id':'championship'}).findAll('option')
	all_comp = {x.text:x['value'] for x in all_comp_option}

	# competizione (regular season, playoff)
	for k_comp, v_comp in all_comp.items():
		print(k_comp)
		params.pop('p', None)
		params.pop('d', None)
		params['c'] = v_comp

		query_string = urlencode(params)
		full_url = base_url + query_string

		user_agent = random.choice(user_agent_list)
		headers = {'User-Agent': user_agent}

		req = requests.get(full_url, headers=headers)
		soup = BS(req.text, 'html.parser')

		all_phase_options = soup.find('select', {'id':'phase'}).findAll('option')
		all_phase = {x.text:x['value'] for x in all_phase_options}

		# girone (andata, ritorno, semifinali, ..)
		for k_phase, v_phase in all_phase.items():
			print(k_phase)
			params.pop('d', None)
			params['p'] = v_phase
			params['t'] = '0' # static param for all teams

			query_string = urlencode(params)
			full_url = base_url + query_string

			user_agent = random.choice(user_agent_list)
			headers = {'User-Agent': user_agent}

			req = requests.get(full_url, headers=headers)
			soup = BS(req.text, 'html.parser')

			# giornata
			all_round_options = soup.findAll('a', {'class':'page-link'})[1:]
			all_round = [x.get_text().strip() for x in all_round_options if x != '']
			print(all_round)
			for r in all_round:
				params['d'] = r

				query_string = urlencode(params)
				full_url = base_url + query_string

				user_agent = random.choice(user_agent_list)
				headers = {'User-Agent': user_agent}

				req = requests.get(full_url, headers=headers)
				soup = BS(req.text, 'html.parser')

				table = soup.find('table')

				rows = table.findAll('tr')[1:]

				for count_row, r in enumerate(rows):
					giornata = soup.findAll('span', {'class':'text-orange'})[-1].get_text() + ' ' + k_phase
					new_row = [s, giornata]
					cols = r.findAll('td')
					for count_col, c in enumerate(cols):
						if count_col == 1:
							punteggio = c.text.strip().replace(' ','')
							link_boxscore = c.find('a')['href']
							new_row.extend([punteggio, link_boxscore])
						elif count_col in [0,2,5]:
							val = c.text.strip().replace('\n','')
							val = re.sub(' +', ' ', val)
							new_row.append(val)
					team_id = cols[0].find('a')['href'].split('/')[4]
					new_row.append(team_id)

					new_games.loc[pos] = new_row
					pos += 1

# modify dataframe
new_games['Data'] = new_games['DataOra'].apply(split_data)
new_games['Data'] = new_games['Data'].apply(invert_data)
new_games = new_games[['Team ID','Anno','Giornata','Data','DataOra','Squadra Casa', 'Punteggio', 'Squadra Trasferta','Link Boxscore']]
new_games.sort_values('Data', inplace=True)

#new_games.to_csv('2021_2022.csv',index=False)

games_df = pd.read_csv('stats_reference/static/all_games.csv')
games_df = games_df[~games_df['Link Boxscore'].isin(new_games['Link Boxscore'].tolist())]
# save backups
timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
games_df.to_csv('stats_reference/static/backup/all_games_'+timestamp+'.csv',index=False)

final_df = pd.concat([games_df, new_games])
final_df['Game ID'] = final_df['Link Boxscore'].apply(extract_game_id)
final_df.drop_duplicates(subset=['Game ID'], inplace=True, keep='last')
final_df.drop(columns=['Game ID'], inplace=True)
final_df.sort_values('Data', inplace=True)
final_df.to_csv('stats_reference/static/all_games.csv',index=False)