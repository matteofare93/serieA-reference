import requests
import time
from bs4 import BeautifulSoup as BS
import pandas as pd
import random
import datetime
from urllib.parse import urlencode
import re
import json

def send_get_request(url, authorize=False):
    
    user_agent = random.choice(user_agent_list)
    headers = {
	    "accept": "application/json, text/plain, */*",
	    "accept-language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
	    "if-none-match": 'W/"cd1bf2999c89407e9efe381d1c758a4c"',
	    "origin": "https://www.legabasket.it",
	    "priority": "u=1, i",
	    "referer": "https://www.legabasket.it/",
	    "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
	    "sec-ch-ua-mobile": "?0",
	    "sec-ch-ua-platform": '"macOS"',
	    "sec-fetch-dest": "empty",
	    "sec-fetch-mode": "cors",
	    "sec-fetch-site": "cross-site",
	    "user-agent": user_agent
	}
    
    if authorize:
        
        headers['authorization'] = 'Bearer MyBxdhceygFuwvlOMinlO7Wune-9qnsBcQNtI1ony1M'
    
    req = requests.get(url, headers=headers)
    soup = BS(req.text, 'html.parser')
    return soup

user_agent_list = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
]

columns_df = ['Anno', 'Giornata', 'Squadra Casa', 'Punteggio', 'Link Boxscore', 'Squadra Trasferta', 'DataOra', 'Team ID']
new_games = pd.DataFrame(columns=columns_df)

# first call for all competitions json
base_url = 'https://www.legabasket.it/calendario/1/serie-a?'
# other calls to calendar api
calendar_api_url = 'https://api-lba.procne.cloud/api/v1/championships/'

soup = send_get_request(base_url)

competitions = json.loads(soup.find('script', {'type':'application/json'}).text)
competitions = competitions['props']['pageProps']['allCompetitionsBySeriesId']['competitions']

seasons_to_update = ['2023/2024']

for s in seasons_to_update:
    
    # cycle on this year competitions
    year = s.split('/')[0]
    this_competitions = [x for x in competitions if x['year'] == int(year)]
    
    for comp in this_competitions:
    
        comp_id = comp['id']
        comp_name = comp['full_name']
        
        #import ipdb; ipdb.set_trace()
        # find all matchdays
        calendar_url = f"{calendar_api_url}{str(comp_id)}/calendar/"
        soup = send_get_request(calendar_url, authorize=True)

        j_soup = json.loads(soup.text)
        
        all_days = [x['code'] for x in j_soup['filters']['days']] # all values for d parameter
        
        for d in all_days:
        
            this_d_url = calendar_url + f'?d={d}'
            soup = send_get_request(this_d_url, authorize=True)
            matches = json.loads(soup.text)['matches']
            
            temp_df = pd.DataFrame(matches)
            
            temp_df = temp_df[['year','day_name','h_team_name','home_final_score',
                 'visitor_final_score','id','v_team_name','match_datetime','h_team_id']]

            temp_df['Punteggio'] = temp_df['home_final_score'].astype(str) + '-' + temp_df['visitor_final_score'].astype(str)
            temp_df['match_datetime'] = pd.to_datetime(temp_df['match_datetime'], format='%Y-%m-%dT%H:%M:%S')
            temp_df['Data'] = temp_df['match_datetime'].apply(lambda x: x.strftime('%Y-%m-%d'))
            temp_df['DataOra'] = temp_df['match_datetime'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M'))

            temp_df.drop(columns=['match_datetime','home_final_score','visitor_final_score','year'], inplace=True)

            temp_df.rename(columns={
                'day_name':'Giornata',
                'h_team_name':'Squadra Casa',
                'v_team_name':'Squadra Trasferta',
                'id':'Link Boxscore',
                'h_team_id':'Team ID'
            }, inplace=True)
            
            temp_df['Anno'] = s
            
            new_games = pd.concat([new_games,temp_df])


games_df = pd.read_csv('stats_reference/static/all_games.csv')
games_df = games_df[~games_df['Anno'].isin(new_games['Anno'].tolist())]
# save backups
timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
games_df.to_csv('stats_reference/static/backup/all_games_'+timestamp+'.csv',index=False)

final_df = pd.concat([games_df, new_games])
final_df['Game ID'] = final_df['Link Boxscore']
final_df.drop_duplicates(subset=['Game ID'], inplace=True, keep='last')
final_df.drop(columns=['Game ID'], inplace=True)
final_df.sort_values('Data', inplace=True)
final_df.to_csv('stats_reference/static/all_games.csv',index=False)