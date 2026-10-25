import datetime
import random

import pandas as pd
import requests
from django.core.management.base import BaseCommand

from games.models import Game

REGULAR_SEASON_ID = 4
PLAYOFF_ID = 2

USER_AGENTS = [
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


class Command(BaseCommand):
    help = 'Aggiorna le partite dal sito di Lega Basket'

    def _build_session(self):
        session = requests.Session()
        session.headers.update(BASE_HEADERS)
        return session

    def _fetch(self, session, url):
        session.headers["user-agent"] = random.choice(USER_AGENTS)
        resp = session.get(url)
        resp.raise_for_status()
        return resp.json()

    def _fetch_games(self, session):
        year = datetime.datetime.now().year
        url = f"https://www.legabasket.it/api/championships/get-championships?s={year}&cs_id=1"
        championships = self._fetch(session, url)

        if not championships['competitions']:
            year -= 1
            url = f"https://www.legabasket.it/api/championships/get-championships?s={year}&cs_id=1"
            championships = self._fetch(session, url)

        season = f"{year}/{year+1}"
        all_dfs = []

        for comp in championships['competitions']:
            comp_id = comp['id']
            comp_name = comp['full_name']
            championship_type = comp['championship_type_id']
            self.stdout.write(f"Processing {comp_name}...")

            list_games_url = f"https://www.legabasket.it/api/championships/get-championships-calendar-by-id?id={comp_id}"
            resp = self._fetch(session, list_games_url)

            if championship_type == REGULAR_SEASON_ID:
                all_days = [x['code'] for x in resp['filters']['days']]
            elif championship_type == PLAYOFF_ID:
                all_days = [x['id'] for x in resp['filters']['phases']]
            else:
                continue

            for d in all_days:
                if championship_type == REGULAR_SEASON_ID:
                    day_url = list_games_url + f'&d={d}'
                elif championship_type == PLAYOFF_ID:
                    day_url = list_games_url + f'&ph_id={d}'

                resp = self._fetch(session, day_url)
                matches = resp['matches']
                if not matches:
                    continue

                temp_df = pd.DataFrame(matches)
                temp_df = temp_df[['day_name', 'h_team_name', 'home_final_score',
                                   'visitor_final_score', 'id', 'v_team_name',
                                   'match_datetime', 'h_team_id']]

                temp_df['score'] = (temp_df['home_final_score'].astype(str)
                                    + '-' + temp_df['visitor_final_score'].astype(str))
                temp_df['match_datetime'] = temp_df['match_datetime'].apply(lambda x: x.split('.')[0])
                temp_df['game_date'] = pd.to_datetime(temp_df['match_datetime'], format='%Y-%m-%dT%H:%M:%S')
                temp_df['boxscore_link'] = None
                temp_df['season'] = season
                temp_df.drop(columns=['match_datetime', 'home_final_score', 'visitor_final_score'], inplace=True)
                temp_df.rename(columns={
                    'day_name': 'matchday',
                    'h_team_name': 'home_team',
                    'v_team_name': 'away_team',
                    'id': 'legabasket_game_id',
                    'h_team_id': 'team_id',
                }, inplace=True)

                all_dfs.append(temp_df)

        games = pd.concat(all_dfs, ignore_index=True)
        games.drop_duplicates(subset=['legabasket_game_id'], inplace=True, keep='last')
        games.sort_values('game_date', inplace=True)
        return games, season

    def _update_db(self, games, season):
        existing = {
            g.legabasket_game_id: (g.pk, g.score)
            for g in Game.objects.filter(season=season).only('id', 'legabasket_game_id', 'score')
        }

        to_upsert = []
        ids_to_delete = []

        for _, row in games.iterrows():
            gid = row['legabasket_game_id']
            if gid not in existing:
                to_upsert.append(row)
            elif existing[gid][1] != row['score']:
                to_upsert.append(row)
                ids_to_delete.append(existing[gid][0])

        self.stdout.write(f"Found {len(to_upsert)} new or updated games")
        if not to_upsert:
            return 0

        if ids_to_delete:
            Game.objects.filter(pk__in=ids_to_delete).delete()

        Game.objects.bulk_create([
            Game(
                team_id=row['team_id'],
                season=row['season'],
                matchday=row['matchday'],
                game_date=row['game_date'].to_pydatetime(),
                home_team=row['home_team'],
                score=row['score'],
                away_team=row['away_team'],
                boxscore_link=row['boxscore_link'],
                legabasket_game_id=row['legabasket_game_id'],
            )
            for row in to_upsert
        ])

        return len(to_upsert)

    def handle(self, *args, **options):
        session = self._build_session()
        games, season = self._fetch_games(session)
        self.stdout.write(f"Found {len(games)} total games for season {season}")
        count = self._update_db(games, season)
        self.stdout.write(self.style.SUCCESS(f"Done. Inserted/updated {count} games."))
