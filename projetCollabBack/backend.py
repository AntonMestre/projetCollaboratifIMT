from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
import json
import random
import string

def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    print("Random string of length", length, "is:", result_str)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="http://localhost:5173")

with open('quiz_questions.json', 'r') as file:
    quiz_questions = json.load(file)

is_quiz_started = False
quizId = None
quizData = {'answers': {}, 'asked_questions': []}
# teams = [{teamId:1234, players: [{ sid: 123, username: 1243}]}]
teams = []

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('joinPresentationQuiz')
def joinPresentationQuiz(data):
     emit('is_quiz_started', is_quiz_started)

@socketio.on('joinQuiz')
def joinQuiz():
    username = get_random_string(4)

    # joining the quizz room
    if quizId is None:
        quizId = get_random_string(4)
    
    join_room(quizId)
    
    didFoundATeam = False
    for team in teams:
        if len(team['players']) < 2:
            team['players'].append({'sid': request.sid, 'username': username})
            #emit('user_team_info', {'teamId': team['teamId']}, room=request.sid)
            didFoundATeam = True
    
    if not didFoundATeam:
        teams.append({'teamId': get_random_string(4), 'players': [{'sid': request.sid, 'username': username}]})
        #emit('user_team_info', {'teamId': teams[-1]['teamId']}, room=request.sid)
    
    # Find the team of the user
    userTeam = None
    for team in teams:
        for player in team['players']:
            if player['sid'] == request.sid:
                userTeam = team
                break

    emit('teams', teams, room=quizId)
    emit('userTeam', userTeam)



if __name__ == '__main__':
    socketio.run(app)

# Arrivé du joueur sur la page
    # Si quizz deja demaré -> peut pas rejoindre
    # Si quizz pas démré -> peut rejoindre la salle d'attente
        # Dans la salle d'attente:
            # - Ton equipe, les autres équipes, (nombre de personne conecté), + bouton pour démarrer le quizz

            # Si le bouton est appué -> le quizz démarre
                # Affichage de la question
                # Phase 1:
                    # Affichage des réponses selecteur en pourcentage ()
                    # 15sec
                # Phase 2:
                    # Affichage des pourcentages par question
                    # Choix final (1)
                    # 25sec
                # phase 3:
                    # Affichage de la bonne réponse

                # Fin du jeu : classement par équipe
    
    # ne se prononce pas
    # tchat si possible