from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
import json
import random
import string
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="http://localhost:5173")

with open('quiz_questions.json', 'r') as file:
    quiz_questions = json.load(file)

possibleSatutusOfQuizz = {1: "Waiting", 2: "Started"}
statusOfQuizz = possibleSatutusOfQuizz.get(1)
quizzId = get_random_string(4)
quizzData = quiz_questions
teams = {} 
# teams = { 1234: 
#    { 
#    name: "dzqdzqd",
#    players: { 1234: { username: "jean" },... },
#    numberOfGoodAnswer: 0,
#    },
#    ...}
#
numberOfPeoplePerTeam = 2
pourcentageAnswersForTheQuestion = {} # { 1234(team): { "usernmae124" : [12, 14, 14, 12] } }
answersForTheQuestion = {} # { 1234(team): { "usernmae124" : 2 } }

@app.route('/')
def index():
    return render_template('index.html')

# getStatusOfQuizz : to know if the quizz is started
@socketio.on('getStatusOfQuizz')
def getStatusOfQuizz():
     emit('getStatusOfQuizz', statusOfQuizz)

# joinWaitingRoom : Player get an username and is added to a team
@socketio.on('joinWaitingRoom')
def joinWaitingRoom():
    
    username = get_random_string(4)
    join_room(quizzId)
    
    addPlayerToATeam(username, request.sid)
    teamOfThePlayer = findTeamNameOfPlayer(username)

    emit('teams', teams, room=quizzId)
    emit('userTeam', teamOfThePlayer)

# startTheQuizz : Launch the quizz for all participants
@socketio.on('startTheQuizz')
def startTheQuizz():
    emit('quizzHasStarted', room=quizzId)

    for id, question, answers, correct in quizzData:
        pourcentageAnswersForTheQuestion = {}
        
        ############### Phase 1
        displayQuestionAndAnswers(question, answers)
        time.sleep(15)
        emit('phase1Ended', room=quizzId)
        ############### Phase 2
        displayProcessedAnswers()
        time.sleep(25)
        emit('phase2Ended', room=quizzId)
        processGoodAnswerByTeams(correct)
        ############### Phase 3
        displayTheCorrectAnswer(correct)

    # Rankings per team
    ranking = sorted(teams, key=lambda x: x['numberOfGoodAnswer'], reverse=True)
    emit('ranking', ranking, room=quizzId)

@socketio.on('sendAnswerPhase1')
def sendAnswerPhase1(data):
    # data : { username: "dzkoqd", teamId: "1234" , answers: [12, 14, 12, 14] }
    for team in pourcentageAnswersForTheQuestion:
        if team == data.teamId:
            pourcentageAnswersForTheQuestion[team][data.username] = data.answers

@socketio.on('sendAnswerPhase2')
def sendAnswerPhase2(data):
    # data : { username: "dzkoqd", teamId: "1234" , answers: 2 }
    for team in answersForTheQuestion:
        if team == data.teamId:
            answersForTheQuestion[team][data.username] = data.answers



# USEFULL Functions =======================================================================
            
def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    print("Random string of length", length, "is:", result_str)

def addPlayerToATeam(username, sid):

    didFoundATeam = False

    # Adding on an existing team
    for name, players in teams:
        if len(players) < numberOfPeoplePerTeam:
            players.update({ sid : { "username": username }})
            didFoundATeam = True
    
    # Adding on a new team
    if not didFoundATeam:
        teams.update({ name: get_random_string(6), players: { sid: { "username": username }} })

def findTeamNameOfPlayer(username):
    userTeam = None
    for name, players in teams:
        for usernamePlayer in players:
            if usernamePlayer == username:
                userTeam = name
                break
    
    return userTeam

def displayQuestionAndAnswers(question, answers):

    emit('questionAndAnswers', { "question" : question, "answers" : answers}, room=quizzId)

def displayProcessedAnswers():

    answersProcessed = {}

    for team in pourcentageAnswersForTheQuestion:
        sumTeam = [0, 0, 0, 0]
        for user in team:
            for i in range(4):
                sumTeam[i] += pourcentageAnswersForTheQuestion[team][user][i]
        
        for i in range(4):
            sumTeam[i] = sumTeam[i] / numberOfPeoplePerTeam
        
        answersProcessed.update({ team: sumTeam })
        
    emit('processedAnswers', answersProcessed, room=quizzId)

def displayTheCorrectAnswer(correct):
    emit('correctAnswer', correct, room=quizzId)

def processGoodAnswerByTeams(correct):
    for team in answersForTheQuestion:
        goodAnswer = max(answersForTheQuestion[team], key=answersForTheQuestion[team].get)
        if goodAnswer == correct:
            teams[team]["numberOfGoodAnswer"] += 1



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
    # choix d'équipe si possible