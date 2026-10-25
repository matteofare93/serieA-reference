from django.db import models


class Game(models.Model):
    team_id = models.IntegerField(null=True, blank=True)
    season = models.CharField(max_length=9, null=True, blank=True)
    matchday = models.CharField(max_length=100, null=True, blank=True)
    game_date = models.DateTimeField(null=True, blank=True)
    home_team = models.CharField(max_length=100)
    score = models.CharField(max_length=100, null=True, blank=True)
    away_team = models.CharField(max_length=100)
    boxscore_link = models.TextField(unique=True)

    class Meta:
        db_table = 'games'

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} ({self.season})"


class GameDetail(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='details')
    team = models.CharField(max_length=100, null=True, blank=True)
    starter = models.BooleanField(null=True, blank=True)
    number = models.IntegerField(null=True, blank=True)
    player = models.CharField(max_length=100, null=True, blank=True)
    points = models.DecimalField(max_digits=14, decimal_places=6, null=True, blank=True)
    minutes = models.DecimalField(max_digits=14, decimal_places=6, null=True, blank=True)
    fouls_committed = models.IntegerField(null=True, blank=True)
    fouls_received = models.IntegerField(null=True, blank=True)
    two_pts_made = models.IntegerField(null=True, blank=True)
    two_pts_attempted = models.IntegerField(null=True, blank=True)
    two_pts_perc = models.DecimalField(max_digits=14, decimal_places=6, null=True, blank=True)
    dunks = models.IntegerField(null=True, blank=True)
    three_pts_made = models.IntegerField(null=True, blank=True)
    three_pts_attempted = models.IntegerField(null=True, blank=True)
    three_pts_perc = models.DecimalField(max_digits=14, decimal_places=6, null=True, blank=True)
    ft_made = models.IntegerField(null=True, blank=True)
    ft_attempted = models.IntegerField(null=True, blank=True)
    ft_perc = models.DecimalField(max_digits=14, decimal_places=6, null=True, blank=True)
    def_rebounds = models.IntegerField(null=True, blank=True)
    off_rebounds = models.IntegerField(null=True, blank=True)
    tot_rebounds = models.IntegerField(null=True, blank=True)
    blocks_given = models.IntegerField(null=True, blank=True)
    blocks_received = models.IntegerField(null=True, blank=True)
    turnovers = models.IntegerField(null=True, blank=True)
    steals = models.IntegerField(null=True, blank=True)
    assists = models.IntegerField(null=True, blank=True)
    league_rating = models.IntegerField(null=True, blank=True)
    oer_rating = models.DecimalField(max_digits=14, decimal_places=6, null=True, blank=True)
    plus_minus = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'games_details'

    def __str__(self):
        return f"{self.player} — {self.game}"

