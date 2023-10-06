from django import forms
from django.core import validators
import datetime
import time
import pandas as pd
import os

df_games = pd.read_csv('./static/all_games.csv')
anni = df_games['Anno'].unique()
SEASONS = []
for a in anni:
    t = (a,a)
    SEASONS.append(t)
SEASONS.append(('All','All'))
SEASONS.append((('', 'Select a Season')))
SEASONS = SEASONS[::-1]

class QueryForm(forms.Form):

	season = forms.ChoiceField(label='Season', choices=SEASONS)
	team = forms.CharField(label='Team', max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'Enter a Team Name'}))
	only_home_games = forms.BooleanField(label='Only Home Games', required=False)
	only_road_games = forms.BooleanField(label='Only Road Games', required=False)
	#road_games = forms.BooleanField(label='Road Games', required=False)
	team_two = forms.CharField(label='Team', max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'Opposing Team'}))
	#road_games_2 = forms.BooleanField(label='Road Games', required=False)

	def clean(self):
		data = self.cleaned_data