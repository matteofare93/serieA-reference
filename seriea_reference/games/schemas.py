from ninja import Schema, FilterSchema
from typing import Optional
from datetime import datetime
from decimal import Decimal


class GameSchema(Schema):
    id: int
    team_id: Optional[int] = None
    season: Optional[str] = None
    matchday: Optional[str] = None
    game_date: Optional[datetime] = None
    home_team: str
    score: Optional[str] = None
    away_team: str
    boxscore_link: str


class GameDetailSchema(Schema):
    id: int
    game_id: int
    team: Optional[str] = None
    starter: Optional[bool] = None
    number: Optional[int] = None
    player: Optional[str] = None
    points: Optional[Decimal] = None
    minutes: Optional[Decimal] = None
    fouls_committed: Optional[int] = None
    fouls_received: Optional[int] = None
    two_pts_made: Optional[int] = None
    two_pts_attempted: Optional[int] = None
    two_pts_perc: Optional[Decimal] = None
    dunks: Optional[int] = None
    three_pts_made: Optional[int] = None
    three_pts_attempted: Optional[int] = None
    three_pts_perc: Optional[Decimal] = None
    ft_made: Optional[int] = None
    ft_attempted: Optional[int] = None
    ft_perc: Optional[Decimal] = None
    def_rebounds: Optional[int] = None
    off_rebounds: Optional[int] = None
    tot_rebounds: Optional[int] = None
    blocks_given: Optional[int] = None
    blocks_received: Optional[int] = None
    turnovers: Optional[int] = None
    steals: Optional[int] = None
    assists: Optional[int] = None
    league_rating: Optional[int] = None
    oer_rating: Optional[Decimal] = None
    plus_minus: Optional[int] = None


class GameFilterSchema(FilterSchema):
    season: Optional[str] = None
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    team: Optional[str] = None  # cerca in home o away
