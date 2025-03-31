from flask import Flask, render_template, request, jsonify, url_for
import json
import os
from pymongo import MongoClient
from datetime import datetime
from dateutil import parser

app = Flask(__name__)

# MongoDB Configuration
client = MongoClient("mongodb+srv://garde:LetstestStuff_25@cluster1.94yvjui.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1")
db = client["otteluohjelma"]
games_collection = db["otteluohjelma"]

# Load teams data from teams.json
teams_file_path = os.path.join(app.root_path, 'teams.json')
teams_data = {}
try:
    with open(teams_file_path, 'r', encoding='utf-8') as f:
        teams_data = json.load(f)
except FileNotFoundError:
    print(f"Error: teams.json not found at {teams_file_path}")
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {teams_file_path}")

@app.route('/', methods=['GET', 'POST'])
def index():
    selected_sports = request.form.getlist('sport') if request.method == 'POST' else []
    selected_teams_by_sport = {}
    next_home_games = {}

    datenow = datetime.now()
    datenow = datenow.strftime("%d.%m. %H:%M")    
    datenow = datetime.strptime(datenow, "%d.%m. %H:%M")

    if request.method == 'POST' and selected_sports:
        for sport in selected_sports:
            if sport in teams_data and isinstance(teams_data[sport], dict):
                selected_teams_by_sport[sport] = {}
                for category, teams in teams_data[sport].items():
                    team_key_prefix = f'team_{sport}_{category}'
                    selected_teams = request.form.getlist(team_key_prefix)
                    if selected_teams:
                        selected_teams_by_sport[sport][category] = selected_teams
                        for team in selected_teams:                        
                            query = {
                                'koti': team,
                                'pelipv': {'$exists': True},
                                'peliklo': {'$exists': True},
                                "laji": sport,  # Added sport to the query to distinguish teams with the same name.
                                "sarja": category
                            }
                            sort_criteria = [('pelipv', 1), ('peliklo', 1)]
                            games = games_collection.find(query, sort=sort_criteria) # changed find_one to find.

                            found_upcoming_game = False #Added this variable.
                            for next_game in games: # loop through all found games.
                                try:
                                    pelipv_str = next_game.get('pelipv', '')
                                    peliklo_str = next_game.get('peliklo', '')

                                    if pelipv_str and peliklo_str:
                                        try:

                                            game_date_naive = datetime.strptime(f"{pelipv_str} {peliklo_str}", "%d.%m. %H:%M")
                                            if game_date_naive >= datenow:
                                                game_date = game_date_naive 
                                                if sport not in next_home_games:
                                                    next_home_games[sport] = {}
                                                if category not in next_home_games[sport]:
                                                    next_home_games[sport][category] = {}

                                                game_date = game_date.strftime("%d.%m. %H:%M")   
                                                next_home_games[sport][category][team] = {
                                                    'opponent': next_game.get('vieras'),
                                                    'date': game_date
                                                }
                                                found_upcoming_game = True # set to true if upcoming game found.
                                                break #stop loop if upcoming game found.
                                            else:
                                                if sport not in next_home_games:
                                                    next_home_games[sport] = {}
                                                if category not in next_home_games[sport]:
                                                    next_home_games[sport][category] = {}
                                                next_home_games[sport][category][team] = {'opponent': 'Ei tulevia kotipelejä', 'date': 'N/A'}
                                        except ValueError:
                                            if sport not in next_home_games:
                                                next_home_games[sport] = {}
                                            if category not in next_home_games[sport]:
                                                next_home_games[sport][category] = {}
                                            next_home_games[sport][team] = {'opponent': 'Error parsing date', 'date': 'N/A'}
                                    else:
                                        if sport not in next_home_games:
                                            next_home_games[sport] = {}
                                        if category not in next_home_games[sport]:
                                            next_home_games[sport][category] = {}
                                        next_home_games[sport][category][team] = {'opponent': 'Ei tulevia kotipelejä', 'date': 'N/A'}
                                except Exception as e:
                                    print(f"Error processing game data for {team}: {e}")
                                    if sport not in next_home_games:
                                        next_home_games[sport] = {}
                                    if category not in next_home_games[sport]:
                                        next_home_games[sport][category] = {}
                                    next_home_games[sport][team] = {'opponent': 'Error fetching game', 'date': 'N/A'}

                            if found_upcoming_game == False: # if no upcoming game was found.
                                if sport not in next_home_games:
                                    next_home_games[sport] = {}
                                if category not in next_home_games[sport]:
                                    next_home_games[sport][category] = {}
                                next_home_games[sport][category][team] = {'opponent': 'Ei tulevia kotipelejä', 'date': 'N/A'}
            
            elif sport in teams_data and isinstance(teams_data[sport], list):
                team_key = f'team_{sport}'
                selected_teams = request.form.getlist(team_key)
                if selected_teams:
                    selected_teams_by_sport[sport] = selected_teams
                    for team in selected_teams:
                        query = {
                            'koti': team,
                            'pelipv': {'$exists': True},
                            'peliklo': {'$exists': True},
                            "laji": sport,  # Added sport to the query to distinguish teams with the same name.
                            "sarja": category
                        }
                        sort_criteria = [('pelipv', 1), ('peliklo', 1)]

                        games = games_collection.find(query, sort=sort_criteria) # changed find_one to find.
                        found_upcoming_game = False #Added this variable.
                        for next_game in games: # loop through all found games.
                            try:
                                pelipv_str = next_game.get('pelipv', '')
                                peliklo_str = next_game.get('peliklo', '')

                                if pelipv_str and peliklo_str:
                                    try:
                                        game_date_naive = datetime.strptime(f"{pelipv_str} {peliklo_str}", "%d.%m. %H:%M")
                                        game_date_naive = game_date_naive.strftime("%d.%m. %H:%M")                                    
                                        if game_date_naive >= datenow:
                                            game_date = game_date_naive   
                                            if sport not in next_home_games:
                                                next_home_games[sport] = {}

                                            game_date = game_date.strftime("%d.%m. %H:%M")  
                                            next_home_games[sport][team] = {
                                                'opponent': next_game.get('vieras'),
                                                'date': game_date
                                            }
                                            found_upcoming_game = True # set to true if upcoming game found.
                                            break #stop loop if upcoming game found.
                                        else:
                                            if sport not in next_home_games:
                                                next_home_games[sport] = {}
                                            next_home_games[sport][team] = {'opponent': 'Ei tulevia kotipelejä', 'date': 'N/A'}
                                    except ValueError:
                                        if sport not in next_home_games:
                                            next_home_games[sport] = {}
                                        next_home_games[sport][team] = {'opponent': 'Error parsing date', 'date': 'N/A'}
                                else:
                                    if sport not in next_home_games:
                                        next_home_games[sport] = {}
                                    next_home_games[sport][team] = {'opponent': 'Ei tulevia kotipelejä', 'date': 'N/A'}
                            except Exception as e:
                                print(f"Error processing game data for {team}: {e}")
                                if sport not in next_home_games:
                                    next_home_games[sport] = {}
                                next_home_games[sport][team] = {'opponent': 'Error fetching game', 'date': 'N/A'}

                        if found_upcoming_game == False: # if no upcoming game was found.
                            if sport not in next_home_games:
                                next_home_games[sport] = {}
                            next_home_games[sport][team] = {'opponent': 'Ei tulevia kotipelejä', 'date': 'N/A'}

    available_sports = list(teams_data.keys())
    num_selected_sports = len(selected_sports)
    return render_template('index.html',
                           available_sports=available_sports,
                           teams_data=teams_data,
                           selected_sports=selected_sports,
                           selected_teams_by_sport=selected_teams_by_sport,
                           num_selected_sports=num_selected_sports,
                           next_home_games=next_home_games)

@app.route('/home_games')
def home_games_page():
    selected_sports = request.args.getlist('sport')
    selected_teams_str = request.args.get('teams')
    selected_teams_by_sport = {}
    next_home_games_for_page = {}

    if selected_sports and selected_teams_str:
        selected_teams_list = json.loads(selected_teams_str)
        datenow = datetime.now()
        datenow = datenow.strftime("%d.%m. %H:%M")
        datenow = datetime.strptime(datenow, "%d.%m. %H:%M")


        for sport in selected_sports:
            if sport in selected_teams_list:
                selected_teams_by_sport[sport] = {}
                for category, teams in selected_teams_list[sport].items():
                    selected_teams_by_sport[sport][category] = teams
                    for team in teams:
                        query = {
                            'koti': team,
                            'pelipv': {'$exists': True},
                            'peliklo': {'$exists': True},
                            "laji": sport,  # Added sport to the query to distinguish teams with the same name.
                            "sarja": category
                        }
                        sort_criteria = [('pelipv', 1), ('peliklo', 1)]

                        games = games_collection.find(query, sort=sort_criteria) # changed find_one to find.
                        found_upcoming_game = False #Added this variable.
                        for next_game in games: # loop through all found games.

                            try:
                                pelipv_str = next_game.get('pelipv', '')
                                peliklo_str = next_game.get('peliklo', '')

                                if pelipv_str and peliklo_str:
                                    try:
                                        game_date_naive = datetime.strptime(f"{pelipv_str} {peliklo_str}", "%d.%m. %H:%M")                              
                                        if game_date_naive >= datenow:
                                            game_date = game_date_naive 

                                            if sport not in next_home_games_for_page:
                                                next_home_games_for_page[sport] = {}
                                            if category not in next_home_games_for_page[sport]:
                                                next_home_games_for_page[sport][category] = {}

                                            game_date = game_date.strftime("%d.%m. %H:%M")  
                                            next_home_games_for_page[sport][category][team] = {
                                                'opponent': next_game.get('vieras'),
                                                'date': game_date
                                            }
                                            found_upcoming_game = True # set to true if upcoming game found.
                                            break #stop loop if upcoming game found.
                                        else:
                                            if sport not in next_home_games_for_page:
                                                next_home_games_for_page[sport] = {}
                                            if category not in next_home_games_for_page[sport]:
                                                next_home_games_for_page[sport][category] = {}
                                            next_home_games_for_page[sport][category][team] = {'opponent': 'Ei tulevia kotipelejä', 'date': 'N/A'}
                                    except ValueError:
                                        if sport not in next_home_games_for_page:
                                            next_home_games_for_page[sport] = {}
                                        if category not in next_home_games_for_page[sport]:
                                            next_home_games_for_page[sport][category] = {}
                                        next_home_games_for_page[sport][team] = {'opponent': 'Error parsing date', 'date': 'N/A'}
                                else:
                                    if sport not in next_home_games_for_page:
                                        next_home_games_for_page[sport] = {}
                                    if category not in next_home_games_for_page[sport]:
                                        next_home_games_for_page[sport][category] = {}
                                    next_home_games_for_page[sport][team] = {'opponent': 'Ei tulevia kotipelejä', 'date': 'N/A'}
                            except Exception as e:
                                print(f"Error processing game data for {team} in home_games_page: {e}")
                                if sport not in next_home_games_for_page:
                                    next_home_games_for_page[sport] = {}
                                if category not in next_home_games_for_page[sport]:
                                    next_home_games_for_page[sport][category] = {}
                                next_home_games_for_page[sport][category][team] = {'opponent': 'Error fetching game', 'date': 'N/A'}

                        if found_upcoming_game == False: # if no upcoming game was found.
                            if sport not in next_home_games_for_page:
                                next_home_games_for_page[sport] = {}
                            if category not in next_home_games_for_page[sport]:
                                next_home_games_for_page[sport][category] = {}
                            next_home_games_for_page[sport][category][team] = {'opponent': 'Ei tulevia kotipelejä', 'date': 'N/A'}

    return render_template('home_games.html', next_home_games=next_home_games_for_page, selected_sports=selected_sports, selected_teams_by_sport=selected_teams_by_sport)

if __name__ == '__main__':
    app.run(debug=True)