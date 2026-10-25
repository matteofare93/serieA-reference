from ninja import Router
from django.shortcuts import get_object_or_404
from django.db.models import Q
from typing import Optional, List

from .models import Game, GameDetail
from .schemas import GameSchema, GameDetailSchema, PlayerGameDetailSchema

router = Router()


@router.get("/games", response=List[GameSchema], tags=["games"])
def list_games(
    request,
    season: Optional[str] = None,
    team: Optional[str] = None,
    team_two: Optional[str] = None,
    only_home: bool = False,
    only_away: bool = False,
):
    qs = Game.objects.all()

    if season:
        qs = qs.filter(season=season)

    if team and team_two:
        if only_home:
            qs = qs.filter(home_team__icontains=team, away_team__icontains=team_two)
        elif only_away:
            qs = qs.filter(home_team__icontains=team_two, away_team__icontains=team)
        else:
            qs = qs.filter(
                Q(home_team__icontains=team, away_team__icontains=team_two) |
                Q(home_team__icontains=team_two, away_team__icontains=team)
            )
    elif team:
        if only_home:
            qs = qs.filter(home_team__icontains=team)
        elif only_away:
            qs = qs.filter(away_team__icontains=team)
        else:
            qs = qs.filter(Q(home_team__icontains=team) | Q(away_team__icontains=team))
    elif team_two:
        if only_home:
            qs = qs.filter(home_team__icontains=team_two)
        elif only_away:
            qs = qs.filter(away_team__icontains=team_two)
        else:
            qs = qs.filter(Q(home_team__icontains=team_two) | Q(away_team__icontains=team_two))

    return qs


@router.get("/games/{game_id}", response=GameSchema, tags=["games"])
def get_game(request, game_id: int):
    """Dettaglio di una singola partita."""
    return get_object_or_404(Game, id=game_id)


@router.get("/games/{game_id}/details", response=List[GameDetailSchema], tags=["games"])
def get_game_details(request, game_id: int):
    """Statistiche di tutti i giocatori di una partita."""
    get_object_or_404(Game, id=game_id)
    return GameDetail.objects.filter(game_id=game_id)


@router.get("/seasons", response=List[str], tags=["meta"])
def list_seasons(request):
    """Lista di tutte le stagioni disponibili."""
    return (
        Game.objects
        .exclude(season__isnull=True)
        .values_list("season", flat=True)
        .distinct()
        .order_by("-season")
    )


@router.get("/players/{player_name}/details", response=List[PlayerGameDetailSchema], tags=["players"])
def get_player_details(
    request,
    player_name: str,
    season: Optional[str] = None,
):
    """Tutte le statistiche di un giocatore, con filtro stagione opzionale."""
    qs = GameDetail.objects.filter(player__icontains=player_name).select_related("game")

    if season:
        qs = qs.filter(game__season=season)

    return qs
