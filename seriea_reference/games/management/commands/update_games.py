import datetime
import random
import time

import pandas as pd
from curl_cffi import requests
from django.core.management.base import BaseCommand

from games.models import Game, GameDetail

REGULAR_SEASON_ID = 4
PLAYOFF_ID = 2

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


def _round2(val):
    return round(val, 2) if val is not None else None


def _parse_player_row(row, team_name):
    return dict(
        team=team_name,
        starter=row.get('sf') == '1',
        number=row.get('player_num'),
        player=f"{row.get('player_surname', '')} {row.get('player_name', '')}".strip(),
        points=row.get('pun'),
        minutes=row.get('min'),
        fouls_committed=row.get('falli_c'),
        fouls_received=row.get('falli_sf'),
        two_pts_made=row.get('t2_r'),
        two_pts_attempted=row.get('t2_t'),
        two_pts_perc=_round2(row.get('t2_perc')),
        dunks=row.get('sc'),
        three_pts_made=row.get('t3_r'),
        three_pts_attempted=row.get('t3_t'),
        three_pts_perc=_round2(row.get('t3_perc')),
        ft_made=row.get('tl_r'),
        ft_attempted=row.get('tl_t'),
        ft_perc=_round2(row.get('tl_perc')),
        def_rebounds=row.get('rimbalzi_d'),
        off_rebounds=row.get('rimbalzi_o'),
        tot_rebounds=row.get('rimbalzi_t'),
        blocks_given=row.get('stoppate_dat'),
        blocks_received=row.get('stoppate_sub'),
        turnovers=row.get('palle_p'),
        steals=row.get('palle_r'),
        assists=row.get('ass'),
        league_rating=row.get('val_lega'),
        oer_rating=_round2(row.get('val_oer')),
        plus_minus=row.get('plus_minus'),
    )


def _parse_aggregate_row(row, team_name, label):
    return dict(
        team=team_name,
        starter=None,
        number=None,
        player=label,
        points=row.get('pun'),
        minutes=row.get('min'),
        fouls_committed=row.get('falli_c'),
        fouls_received=row.get('falli_sf'),
        two_pts_made=row.get('t2_r'),
        two_pts_attempted=row.get('t2_t'),
        two_pts_perc=_round2(row.get('t2_perc')),
        dunks=row.get('sc'),
        three_pts_made=row.get('t3_r'),
        three_pts_attempted=row.get('t3_t'),
        three_pts_perc=_round2(row.get('t3_perc')),
        ft_made=row.get('tl_r'),
        ft_attempted=row.get('tl_t'),
        ft_perc=_round2(row.get('tl_perc')),
        def_rebounds=row.get('rimbalzi_d'),
        off_rebounds=row.get('rimbalzi_o'),
        tot_rebounds=row.get('rimbalzi_t'),
        blocks_given=row.get('stoppate_dat'),
        blocks_received=row.get('stoppate_sub'),
        turnovers=row.get('palle_p'),
        steals=row.get('palle_r'),
        assists=row.get('ass'),
        league_rating=row.get('val_lega'),
        oer_rating=_round2(row.get('val_oer')),
        plus_minus=row.get('plus_minus'),
    )


def _scores_to_rows(resp):
    match = resp['match']
    scores = resp['scores']
    rows = []
    for side, team_key in [('ht', 'h_team_name'), ('vt', 'v_team_name')]:
        team_name = match[team_key]
        for player_row in scores[side].get('rows', []):
            rows.append(_parse_player_row(player_row, team_name))
        rows.append(_parse_aggregate_row(scores[side]['team'],   team_name, 'Squadra'))
        rows.append(_parse_aggregate_row(scores[side]['totals'], team_name, 'Totali'))
    return rows


class Command(BaseCommand):
    help = 'Aggiorna le partite e i dettagli dal sito di Lega Basket'

    def _build_session(self):
        session = requests.Session(impersonate="chrome131")
        session.headers.update(BASE_HEADERS)
        return session

    def _fetch(self, session, url, max_retries=5):
        for attempt in range(max_retries):
            resp = session.get(url)
            if resp.status_code in (403, 429):
                wait = (2 ** attempt) + random.uniform(1, 3)
                self.stdout.write(f"  [{resp.status_code}] Rate limited. Attendo {wait:.1f}s (tentativo {attempt+1}/{max_retries})...")
                time.sleep(wait)
                continue
            if resp.status_code == 500:
                return None
            resp.raise_for_status()
            return resp.json()
        raise Exception(f"Troppi tentativi falliti per {url}")

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
            if resp is None:
                continue

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
                if resp is None:
                    continue
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
            return []

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

        return [row['legabasket_game_id'] for row in to_upsert]

    def _update_game_details(self, session, game_ids):
        base_url = "https://www.legabasket.it/api/championships/get-championships-matches-by-id?id="
        # Build a map legabasket_game_id -> Game pk
        game_map = {
            g.legabasket_game_id: g
            for g in Game.objects.filter(legabasket_game_id__in=game_ids).only('id', 'legabasket_game_id')
        }

        inserted = 0
        for legabasket_id in game_ids:
            resp = self._fetch(session, base_url + str(legabasket_id))
            if resp is None:
                self.stdout.write(f"  Skipping game {legabasket_id} (no data)")
                time.sleep(random.uniform(2.0, 4.0))
                continue

            game_obj = game_map.get(legabasket_id)
            if game_obj is None:
                time.sleep(random.uniform(2.0, 4.0))
                continue

            rows = _scores_to_rows(resp)

            GameDetail.objects.filter(game=game_obj).delete()
            GameDetail.objects.bulk_create([
                GameDetail(game=game_obj, **row)
                for row in rows
            ])
            inserted += len(rows)
            time.sleep(random.uniform(2.0, 4.0))

        return inserted

    def add_arguments(self, parser):
        parser.add_argument(
            '--full',
            action='store_true',
            help='Aggiorna i dettagli di tutte le partite, non solo quelle modificate',
        )

    def handle(self, *args, **options):
        session = self._build_session()
        games, season = self._fetch_games(session)
        self.stdout.write(f"Found {len(games)} total games for season {season}")

        upserted_ids = self._update_db(games, season)
        self.stdout.write(self.style.SUCCESS(f"Games: inserite/aggiornate {len(upserted_ids)}."))

        if options['full']:
            game_ids = games['legabasket_game_id'].dropna().tolist()
        else:
            game_ids = upserted_ids

        # exclude games not yet played (score 0-0)
        played_ids = set(
            games.loc[games['score'] != '0-0', 'legabasket_game_id'].dropna().tolist()
        )
        game_ids = [gid for gid in game_ids if gid in played_ids]

        self.stdout.write(f"Fetching details for {len(game_ids)} games...")
        detail_count = self._update_game_details(session, game_ids)
        self.stdout.write(self.style.SUCCESS(f"GameDetails: inserite {detail_count} righe."))