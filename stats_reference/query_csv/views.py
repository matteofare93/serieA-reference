from django.shortcuts import render
from .forms import QueryForm
from django.http import HttpResponse
import pandas as pd
import datetime
from pathlib import Path
import os
import json

def home_view(request):
	form = QueryForm()

	if request.method == "POST":
		form = QueryForm(request.POST)

		if form.is_valid():
			context = {
				'data': form.cleaned_data
			}
			return display_games_view(request, context)

	context = {
		'form': form
	}

	return render(request, 'home_form.html', context)

def display_games_view(request, context):

	params = context['data']
	print(params)
	season = params['season']
	team_1 = params['team']
	team_2 = params['team_two']
	only_home_games = params['only_home_games']
	only_road_games = params['only_road_games']

	n_words_1 = team_1.split(' ')
	n_words_2 = team_2.split(' ')

	if len(n_words_1) == 1:
		team_1 = team_1.capitalize()
	else:
		team_1 = " ".join([x.capitalize() for x in n_words_1])

	if len(n_words_2) == 1:
		team_2 = team_2.capitalize()
	else:
		team_2 = " ".join([x.capitalize() for x in n_words_2])

	df_games = pd.read_csv('./static/all_games.csv')

	if season != 'All':
		df_games = df_games[df_games['Anno'] == season]
	else:
		season = 'All Seasons'

	if team_1 != '':
		if team_2 != '':
			if only_home_games:
				df_games = df_games[(df_games['Squadra Casa'].str.contains(team_1)) & (df_games['Squadra Trasferta'].str.contains(team_2))]
			elif only_road_games:
				df_games = df_games[(df_games['Squadra Casa'].str.contains(team_2)) & (df_games['Squadra Trasferta'].str.contains(team_1))]
			else:
				df_games = df_games[((df_games['Squadra Casa'].str.contains(team_1)) | (df_games['Squadra Trasferta'].str.contains(team_1))) & 
									((df_games['Squadra Casa'].str.contains(team_2)) | (df_games['Squadra Trasferta'].str.contains(team_2)))]
		else:
			if only_home_games:
				df_games = df_games[(df_games['Squadra Casa'].str.contains(team_1))]
			elif only_road_games:
				df_games = df_games[(df_games['Squadra Trasferta'].str.contains(team_1))]
			else:
				df_games = df_games[(df_games['Squadra Casa'].str.contains(team_1)) | (df_games['Squadra Trasferta'].str.contains(team_1))]
	
	elif team_2 != '':
		if only_home_games:
			df_games = df_games[(df_games['Squadra Casa'].str.contains(team_2))]
		elif only_road_games:
			df_games = df_games[(df_games['Squadra Trasferta'].str.contains(team_2))]
		else:
			df_games = df_games[(df_games['Squadra Casa'].str.contains(team_2)) | (df_games['Squadra Trasferta'].str.contains(team_2))]
	
	else:
		team_1 = 'All Teams'

	all_links = ['links']
	all_links.extend(df_games['Link Boxscore'].tolist())

	df_games = df_games[['Anno','Giornata','DataOra','Squadra Casa','Punteggio','Squadra Trasferta']]
	df_list = [df_games.columns.tolist()]
	df_list.extend(df_games.values.tolist())

	
	df_list = zip(all_links, df_list)

	context = {
		'season': season,
		'team_1': team_1,
		'team_2': team_2,
		'df': df_list
	}

	return render(request, 'all_games.html', context)

def game_details(request):

	game = request.GET.get('game')
	df_games = pd.read_csv('./static/all_games.csv')
	result = df_games.loc[df_games['Link Boxscore'] == game,'Punteggio'].item()
	home_team = df_games.loc[df_games['Link Boxscore'] == game,'Squadra Casa'].item()
	road_team = df_games.loc[df_games['Link Boxscore'] == game,'Squadra Trasferta'].item()

	df_details = pd.read_pickle('./static/games_details.pkl')
	df_details = df_details[df_details['Partita'] == game]
	df_details.drop(columns=['Partita'], inplace=True)

	short_columns = ['Squadra','Tit','#','Giocatore','Pts','Min','FC','FS','2P','2PA','2P%','SCH','3P','3PA','3P%',
					'TL','TLA','TL%','OREB','DREB','TREB','BLKD','BLKS','PP','PR','AST','Val Lega','OER','+/-']
	df_details.columns = short_columns

	df_list = [df_details.columns.tolist()]
	df_list.extend(df_details.values.tolist())

	"""
	game = game.split('/')[-1]
	game = game.replace('_',' ').replace('0-0', result).replace('-',' - ')
	game_list = game.split(' ')
	game_list = [x.capitalize() for x in game_list]
	game = " ".join(game_list)
	"""
	game = f'{home_team} {result} {road_team}'
	#game = game.replace('0 - 0', result)
	

	context = {
		'game' : game,
		'df': df_list
	}
	return render(request, 'game_details.html', context)

def player_details(request):

	player = request.GET.get('player')

	df_details = pd.read_pickle('./static/games_details.pkl')
	df_details = df_details[df_details['Giocatore'] == player]
	df_games = pd.read_csv('./static/all_games.csv')

	df_join = df_games.merge(df_details, left_on='Link Boxscore', right_on='Partita')
	df_join.sort_values('Data', inplace=True)

	#df_details.drop(columns=['Partita'], inplace=True)

	#short_columns = ['Squadra','Tit','#','Giocatore','Pts','Min','FC','FS','2P','2PA','2P%','SCH','3P','3PA','3P%',
	#				'TL','TLA','TL%','DRB','ORB','TRB','BLKD','BLKS','PP','PR','AST','Val','OER','+/-']
	#df_details.columns = short_columns

	all_links = ['links']
	all_links.extend(df_join['Link Boxscore'].tolist())

	df_join['Risultato'] = df_join['Squadra Casa'] + ' ' + df_join['Squadra Trasferta'] + ' ' + df_join['Punteggio']
	df_join.drop(columns=['Team ID','Anno','Giornata','DataOra','Squadra Casa','Squadra Trasferta','Link Boxscore','Partita','Punteggio',
							'Squadra'], inplace=True)
	all_columns_no_res = list(df_join.columns)
	ordered_columns = ['Data','Risultato']
	ordered_columns.extend([x for x in all_columns_no_res if x not in ordered_columns])
	df_join = df_join[ordered_columns]

	short_columns = ['Data','Partita','Tit','#','Giocatore','Pts','Min','FC','FS','2P','2PA','2P%','SCH','3P','3PA','3P%',
					'TL','TLA','TL%','DRB','ORB','TRB','BLKD','BLKS','PP','PR','AST','Val','OER','+/-']
	df_join.columns = short_columns
	
	df_list = [df_join.columns.tolist()]
	df_list.extend(df_join.values.tolist())

	df_list = zip(all_links, df_list)

	context = {
		'game' : player,
		'df': df_list
	}
	return render(request, 'player_details.html', context)
