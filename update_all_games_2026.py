from curl_cffi import requests
import pandas as pd
import random
import datetime
import os
import psycopg as pg
from dotenv import load_dotenv
import time

load_dotenv()

host = os.getenv("POSTGRES_HOST")
dbname = os.getenv("POSTGRES_DB")
user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")

conn = pg.connect(host=host, dbname=dbname, user=user, password=password)
conn.autocommit = True
cursor = conn.cursor()

FULL_UPDATE = 1 # set to 1 to update all games, 0 to update only new or changed games
REGULAR_SEASON_ID = 4
PLAYOFF_ID = 2

user_agent_list = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
]

HOMEPAGE_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "accept-language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
}

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
    "sec-fetch-site": "same-site",
}

def build_session(authorize=False):
    session = requests.Session(impersonate="chrome131")
    session.headers.update(BASE_HEADERS)
    if authorize:
        token = os.environ.get("LEGABASKET_TOKEN", "")
        session.headers["authorization"] = f"Bearer {token}"
    return session

def send_get_request(session, url, max_retries=5):
    for attempt in range(max_retries):
        resp = session.get(url)
        if resp.status_code in (403, 429):
            wait = (2 ** attempt) + random.uniform(1, 3)
            print(f"  [{resp.status_code}] Rate limited. Attendo {wait:.1f}s prima di riprovare (tentativo {attempt+1}/{max_retries})...")
            time.sleep(wait)
            continue
        if resp.status_code == 500:
            return None
        resp.raise_for_status()
        return resp.json()
    raise Exception(f"Troppi tentativi falliti per {url}")

def _round2(val):
    return round(val, 2) if val is not None else None

def _clean(val):
    """Convert pandas NaN / numpy scalars to plain Python types for psycopg."""
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(val, 'item'):  # numpy scalar → Python native
        return val.item()
    return val

def parse_player_row(row, team_name):

    return {
        'team':                team_name,
        'starter':             row.get('sf') == '1',
        'number':              row.get('player_num'),
        'player':              f"{row.get('player_surname', '')} {row.get('player_name', '')}".strip(),
        'points':              row.get('pun'),
        'minutes':             row.get('min'),
        'fouls_committed':     row.get('falli_c'),
        'fouls_received':      row.get('falli_sf'),
        'two_pts_made':        row.get('t2_r'),
        'two_pts_attempted':   row.get('t2_t'),
        'two_pts_perc':        _round2(row.get('t2_perc')),
        'dunks':               row.get('sc'),
        'three_pts_made':      row.get('t3_r'),
        'three_pts_attempted': row.get('t3_t'),
        'three_pts_perc':      _round2(row.get('t3_perc')),
        'ft_made':             row.get('tl_r'),
        'ft_attempted':        row.get('tl_t'),
        'ft_perc':             _round2(row.get('tl_perc')),
        'def_rebounds':        row.get('rimbalzi_d'),
        'off_rebounds':        row.get('rimbalzi_o'),
        'tot_rebounds':        row.get('rimbalzi_t'),
        'blocks_given':        row.get('stoppate_dat'),
        'blocks_received':     row.get('stoppate_sub'),
        'turnovers':           row.get('palle_p'),
        'steals':              row.get('palle_r'),
        'assists':             row.get('ass'),
        'league_rating':       row.get('val_lega'),
        'oer_rating':          _round2(row.get('val_oer')),
        'plus_minus':          row.get('plus_minus'),
    }

def parse_aggregate_row(row, team_name, label):
    
    return {
        'team':                team_name,
        'starter':             None,
        'number':              None,
        'player':              label,
        'points':              row.get('pun'),
        'minutes':             row.get('min'),
        'fouls_committed':     row.get('falli_c'),
        'fouls_received':      row.get('falli_sf'),
        'two_pts_made':        row.get('t2_r'),
        'two_pts_attempted':   row.get('t2_t'),
        'two_pts_perc':        _round2(row.get('t2_perc')),
        'dunks':               row.get('sc'),
        'three_pts_made':      row.get('t3_r'),
        'three_pts_attempted': row.get('t3_t'),
        'three_pts_perc':      _round2(row.get('t3_perc')),
        'ft_made':             row.get('tl_r'),
        'ft_attempted':        row.get('tl_t'),
        'ft_perc':             _round2(row.get('tl_perc')),
        'def_rebounds':        row.get('rimbalzi_d'),
        'off_rebounds':        row.get('rimbalzi_o'),
        'tot_rebounds':        row.get('rimbalzi_t'),
        'blocks_given':        row.get('stoppate_dat'),
        'blocks_received':     row.get('stoppate_sub'),
        'turnovers':           row.get('palle_p'),
        'steals':              row.get('palle_r'),
        'assists':             row.get('ass'),
        'league_rating':       row.get('val_lega'),
        'oer_rating':          _round2(row.get('val_oer')),
        'plus_minus':          row.get('plus_minus'),
    }

def scores_to_rows(resp):
    match = resp['match']
    scores = resp['scores']
    rows = []
    for side, team_key in [('ht', 'h_team_name'), ('vt', 'v_team_name')]:
        team_name = match[team_key]
        for player_row in scores[side].get('rows', []):
            rows.append(parse_player_row(player_row, team_name))
        rows.append(parse_aggregate_row(scores[side]['team'],   team_name, 'Squadra'))
        rows.append(parse_aggregate_row(scores[side]['totals'], team_name, 'Totali'))
    return rows

################################################# GAMES #################################################

columns_df = ['team_id', 'season', 'matchday', 'game_date', 'home_team', 'score', 'away_team', 'boxscore_link', 'legabasket_game_id']
new_games = pd.DataFrame(columns=columns_df)
all_dfs = []

session = build_session()
year = datetime.datetime.now().year
year = 2023
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
        if resp is None:
            continue
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

################################################# GAMES DETAILS #################################################

if FULL_UPDATE == 1:
    all_game_ids = new_games['legabasket_game_id'].dropna().tolist()
else:
    all_game_ids = df_to_update['legabasket_game_id'].dropna().tolist()
print(f"Fetching details for {len(all_game_ids)} games...")

base_url = "https://www.legabasket.it/api/championships/get-championships-matches-by-id?id="

detail_dfs = []
for game_id in all_game_ids:
    url = base_url + str(game_id)
    resp = send_get_request(session, url)
    if resp is None:
        print(f"  Skipping game {game_id} (no data)")
        time.sleep(random.uniform(2.0, 4.0))
        continue

    player_rows = scores_to_rows(resp)
    df = pd.DataFrame(player_rows)
    df['legabasket_game_id'] = game_id
    detail_dfs.append(df)
    time.sleep(random.uniform(2.0, 4.0))  # sleep to avoid hitting rate limits

games_details_df = pd.concat(detail_dfs, ignore_index=True)
# recupero il game_id dal db
query = f"SELECT id as game_id, legabasket_game_id FROM public.games WHERE legabasket_game_id IN ({','.join(map(str, all_game_ids))})"
df_game_ids_db = pd.read_sql_query(query, conn)

games_details_df = games_details_df.merge(df_game_ids_db, left_on='legabasket_game_id', right_on='legabasket_game_id', how='inner')
games_details_df.drop(columns=['legabasket_game_id'], inplace=True)

################################################# UPDATE DB GAMES DETAILS #################################################

game_ids_to_delete = games_details_df['game_id'].dropna().unique().tolist()
if game_ids_to_delete:
    delete_query = f"DELETE FROM public.games_details WHERE game_id IN ({','.join(map(str, game_ids_to_delete))})"
    cursor.execute(delete_query)

INSERT_GAME_DETAIL = """
    INSERT INTO games_details (
        game_id, team, starter, number, player, points, minutes,
        fouls_committed, fouls_received,
        two_pts_made, two_pts_attempted, two_pts_perc,
        dunks,
        three_pts_made, three_pts_attempted, three_pts_perc,
        ft_made, ft_attempted, ft_perc,
        def_rebounds, off_rebounds, tot_rebounds,
        blocks_given, blocks_received,
        turnovers, steals, assists,
        league_rating, oer_rating, plus_minus
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s,
        %s, %s,
        %s, %s, %s,
        %s,
        %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s,
        %s, %s,
        %s, %s, %s,
        %s, %s, %s
    )
"""

detail_params = [
    (
        _clean(row['game_id']),
        _clean(row['team']),
        _clean(row['starter']),
        _clean(row['number']),
        _clean(row['player']),
        _clean(row['points']),
        _clean(row['minutes']),
        _clean(row['fouls_committed']),
        _clean(row['fouls_received']),
        _clean(row['two_pts_made']),
        _clean(row['two_pts_attempted']),
        _clean(row['two_pts_perc']),
        _clean(row['dunks']),
        _clean(row['three_pts_made']),
        _clean(row['three_pts_attempted']),
        _clean(row['three_pts_perc']),
        _clean(row['ft_made']),
        _clean(row['ft_attempted']),
        _clean(row['ft_perc']),
        _clean(row['def_rebounds']),
        _clean(row['off_rebounds']),
        _clean(row['tot_rebounds']),
        _clean(row['blocks_given']),
        _clean(row['blocks_received']),
        _clean(row['turnovers']),
        _clean(row['steals']),
        _clean(row['assists']),
        _clean(row['league_rating']),
        _clean(row['oer_rating']),
        _clean(row['plus_minus']),
    )
    for _, row in games_details_df.iterrows()
]

try:
    cursor.executemany(INSERT_GAME_DETAIL, detail_params)
    print(f"Inserite {len(games_details_df)} righe in games_details.")
except Exception as e:
    conn.rollback()
    raise e