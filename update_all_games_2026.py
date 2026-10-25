import requests
import pandas as pd
import random
import datetime
import os
import psycopg as pg
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("POSTGRES_HOST")
dbname = os.getenv("POSTGRES_DB")
user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")

conn = pg.connect(host=host, dbname=dbname, user=user, password=password)
conn.autocommit = True
cursor = conn.cursor()

REGULAR_SEASON_ID = 4
PLAYOFF_ID = 2

user_agent_list = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
]

BASE_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "origin": "https://www.legabasket.it",
    "priority": "u=1, i",
    "referer": "https://www.legabasket.it/",
    "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
}

def build_session(authorize=False):
    session = requests.Session()
    session.headers.update(BASE_HEADERS)
    if authorize:
        token = os.environ.get("LEGABASKET_TOKEN", "")
        session.headers["authorization"] = f"Bearer {token}"
    return session

def send_get_request(session, url):
    session.headers["user-agent"] = random.choice(user_agent_list)
    resp = session.get(url)
    resp.raise_for_status()
    return resp.json()


################################################# GAMES #################################################

columns_df = ['team_id', 'season', 'matchday', 'game_date', 'home_team', 'score', 'away_team', 'boxscore_link', 'legabasket_game_id']
new_games = pd.DataFrame(columns=columns_df)
all_dfs = []

session = build_session()
year = datetime.datetime.now().year
year = 2024

# cs_id=1 filtra su campionato e playoff, escludendo coppe e supercoppe
# cerco prima questa stagione, se siamo prima di settembre la risposta è vuota, cerco quella precedente
list_championships_url = f"https://www.legabasket.it/api/championships/get-championships?s={year}&cs_id=1"

championships = send_get_request(session, list_championships_url)
if championships['competitions'] == []:

    year = year - 1
    list_championships_url = f"https://www.legabasket.it/api/championships/get-championships?s={year}&cs_id=1"
    championships = send_get_request(session, list_championships_url)

season = f"{year}/{year+1}"
# cycle on this year competitions
for comp in championships['competitions']:

    comp_id = comp['id']
    comp_name = comp['full_name']
    championship_type = comp['championship_type_id']
    print(f"Processing {comp_name}...")

    list_games_url = f"https://www.legabasket.it/api/championships/get-championships-calendar-by-id?id={comp_id}"
    
    # find all matchdays for this competition
    resp = send_get_request(session, list_games_url)

    if championship_type == REGULAR_SEASON_ID:
        all_days = [x['code'] for x in resp['filters']['days']] # all values for d parameter
    elif championship_type == PLAYOFF_ID:
        all_days = [x['id'] for x in resp['filters']['phases']]
    
    for d in all_days:
    
        if championship_type == REGULAR_SEASON_ID:
            this_d_url = list_games_url + f'&d={d}'
        elif championship_type == PLAYOFF_ID:
            this_d_url = list_games_url + f'&ph_id={d}'

        resp = send_get_request(session, this_d_url)
        matches = resp['matches']
        if matches == []:
            continue
        
        temp_df = pd.DataFrame(matches)
        
        temp_df = temp_df[['day_name','h_team_name','home_final_score',
                'visitor_final_score','id','v_team_name','match_datetime','h_team_id']]

        temp_df['score'] = temp_df['home_final_score'].astype(str) + '-' + temp_df['visitor_final_score'].astype(str)
        temp_df['match_datetime'] = temp_df['match_datetime'].apply(lambda x: x.split('.')[0]) # remove timezone info
        temp_df['game_date'] = pd.to_datetime(temp_df['match_datetime'], format='%Y-%m-%dT%H:%M:%S')
        temp_df['boxscore_link'] = None
        temp_df['season'] = season
        temp_df.drop(columns=['match_datetime', 'home_final_score', 'visitor_final_score'], inplace=True)

        temp_df.rename(columns={
            'day_name':'matchday',
            'h_team_name':'home_team',
            'v_team_name':'away_team',
            'id':'legabasket_game_id',
            'h_team_id':'team_id'
        }, inplace=True)
        
        all_dfs.append(temp_df)
        
new_games = pd.concat(all_dfs, ignore_index=True)

new_games.drop_duplicates(subset=['legabasket_game_id'], inplace=True, keep='last')
new_games.reset_index(drop=True, inplace=True)
print(f"Found {len(new_games)} games")
new_games.sort_values('game_date', inplace=True)

################################################# GAMES DETAILS #################################################



################################################# UPDATE DB #################################################

query = f"""SELECT 
    id as db_id, 
    legabasket_game_id as db_legabasket_game_id, 
    score as db_score
FROM public.games 
WHERE season = '{season}'"""
df_games_db = pd.read_sql_query(query, conn)

df_to_update = new_games.merge(df_games_db, left_on='legabasket_game_id', right_on='db_legabasket_game_id', how='left')
df_to_update = df_to_update[
                    df_to_update['db_legabasket_game_id'].isna()
                    | (df_to_update['score'] != df_to_update['db_score'])
                ]
print(f"Found {len(df_to_update)} new or updated games")
df_to_update.drop(columns=['db_id', 'db_legabasket_game_id', 'db_score'], inplace=True)

# delete games that are already in the db
if len(df_to_update) > 0:
    legabasket_game_ids_to_delete = df_to_update['legabasket_game_id'].dropna().tolist()
    delete_query = f"DELETE FROM public.games WHERE legabasket_game_id IN ({','.join(map(str, legabasket_game_ids_to_delete))})"
    cursor.execute(delete_query)

# insert new games
INSERT_GAME = """
    INSERT INTO games (team_id, season, matchday, game_date, home_team, score, away_team, boxscore_link, legabasket_game_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id
"""

params = [
    (
        row['team_id'],
        row['season'],
        row['matchday'],
        row['game_date'].to_pydatetime(),
        row['home_team'],
        row['score'],
        row['away_team'],
        row['boxscore_link'],
        row['legabasket_game_id']
    )
    for _, row in df_to_update.iterrows()
]

try:
    cursor.executemany(INSERT_GAME, params, returning=True)
    print(f"Inserite {len(df_to_update)} righe in games.")
except Exception as e:
    conn.rollback()
    raise e