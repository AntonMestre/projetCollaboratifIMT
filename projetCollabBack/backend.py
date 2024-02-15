from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
import json
import random
import string
import time
from threading import Thread

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="http://localhost:5173")

with open('quiz_questions.json', 'r') as file:
    quiz_questions = json.load(file)

# util function 
def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

# TODO: PROBLEME AVEC MES DICTIONNAIRES + les noms de variables c'est pas du java ici

# Variables =======================================================================

possibleSatusOfQuizz = {1: "Waiting", 2: "Started"}
statusOfQuizz = possibleSatusOfQuizz.get(1)
quizzId = get_random_string(4)
quizzData = quiz_questions
teams = [] 
""" 
teams = [
     {
        "id": "1234",
        "name": "dzqdzqd",
        "players": [ { id: 1234, username: "jean" },... ],
        "numberOfGoodAnswer": 0,
    },
    ...]
"""
numberOfPeoplePerTeam = 2
pourcentageAnswersForTheQuestion = [] # [ { "teamId" : 1234, "answersByPlayer": [ { "username" : 1224, "answers":[12, 14, 14, 12] }] } ] 
# { 1234(team): { "usernmae124" : [12, 14, 14, 12] } }
finalAnswersForTheQuestion = [] # [ { "teamId" : 1234, "finalAnswers": [{ "username": 1234, answer:"" }] } ]

# USEFULL Functions =======================================================================

def addPlayerToATeam(username, sid):

    didFoundATeam = False

    # Adding on an existing team
    for team in teams:
        if len(team["players"]) < numberOfPeoplePerTeam:
            team["players"].append({ "id": sid, "username": username})
            didFoundATeam = True
            break
        
    # Adding on a new team
    if not didFoundATeam:
        teams.append({ "id": get_random_string(4), "name": get_random_string(4), "players": [{ "id": sid, "username": username}], "numberOfGoodAnswer": 0})

def findTeamNameOfPlayer(username):
    userTeam = ""
    for team in teams:
        for player in team["players"]:
            if player["username"] == username:
                userTeam = team["id"]
                break

    return userTeam

# findTeamIdOfPlayer : return the team id of a player
def findTeamIdOfPlayer(username):
    userTeam = ""
    for team in teams:
        for player in team["players"]:
            if player["username"] == username:
                userTeam = team["id"]
                break

    return userTeam

def displayQuestionAndAnswers(question, answers):
    socketio.emit('questionAndAnswers', { "question" : question, "answers" : answers}, room=quizzId)

def displayProcessedAnswers():
    answersProcessed = [] # [ { "teamId" : 1234, "answers": [12, 14, 14, 12] }

    # for each team in pourcentageAnswersForTheQuestion
    # calculate the sum for each answers divided by the number of players in the team
    # and add it to the answersProcessed
    for team in pourcentageAnswersForTheQuestion:
        sumAnswers = [0, 0, 0, 0]
        for player in team["answersByPlayer"]:
            for i in range(len(player["answers"])):
                sumAnswers[i] += player["answers"][i]
        answersProcessed.append({ "teamId": team["teamId"], "answers": [ x / len(team["answersByPlayer"]) for x in sumAnswers ]})

    socketio.emit('processedAnswers', answersProcessed, room=quizzId)

def displayTheCorrectAnswer(correct):
    # in quizzData find the correct answer
    for part in quizzData:
        for answer in part.get("answers"):
            if answer.get("id") == correct:
                socketio.emit('correctAnswer', answer, room=quizzId)
                break

def processGoodAnswerByTeams(correct):
    # finalAnswersForTheQuestion  = [ { "teamId" : 1234, "finalAnswers": [{ "username": 1234, answer:"" }] } ]
    # for each team: calculate the most reprensentative answer
    # if the answer is the good one -> add 1 to the numberOfGoodAnswer
    print(finalAnswersForTheQuestion)
    for team in finalAnswersForTheQuestion:
        possible_answers = set(answer["answer"] for answer in team["finalAnswers"])
        print(possible_answers)
        mostRepresentativeAnswer = max(possible_answers, key=team["finalAnswers"].count)
        print(mostRepresentativeAnswer)
        print(correct)
        if mostRepresentativeAnswer == correct:
            for teamInTeams in teams:
                if teamInTeams["id"] == team["teamId"]:
                    teamInTeams["numberOfGoodAnswer"] += 1

def displayTheRanking():
    ranking = sorted(teams, key=lambda x: x['numberOfGoodAnswer'], reverse=True)
    socketio.emit('ranking', ranking, room=quizzId)

def rollingTheQuizz():
    with app.test_request_context():
        for part in quizzData:
            pourcentageAnswersForTheQuestion = []
            finalAnswersForTheQuestion = []
            
            ############### Phase 1
            displayQuestionAndAnswers(part.get("question"), part.get("answers"))
            time.sleep(5)
            socketio.emit('phase1Ended', room=quizzId)
            
            ############### Phase 2
            time.sleep(1) # to be sure to have all answers
            displayProcessedAnswers()
            
            time.sleep(5)
            socketio.emit('phase2Ended', room=quizzId)
            time.sleep(1) # to be sure to have all answers
            processGoodAnswerByTeams(part.get("correctID"))
            
            ############### Phase 3
            print("not hello")
            displayTheCorrectAnswer(part.get("correctID"))
            displayTheRanking()
            time.sleep(6)

# Websockets Functions =======================================================================

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
    teamIdOfThePlayer = findTeamIdOfPlayer(username)

    emit('teams', teams, room=quizzId)
    emit('username', username)
    emit('userTeam', teamOfThePlayer)
    emit('teamId', teamIdOfThePlayer)

# startTheQuizz : Launch the quizz for all participants
@socketio.on('startTheQuizz')
def startTheQuizz():
    statusOfQuizz = possibleSatusOfQuizz.get(2)
    emit('quizzHasStarted', room=quizzId)
    emit('getStatusOfQuizz', statusOfQuizz, room=quizzId)

    Thread(target=rollingTheQuizz).start()

    """# Rankings per team
    ranking = sorted(teams, key=lambda x: x['numberOfGoodAnswer'], reverse=True)
    emit('ranking', ranking, room=quizzId)"""

@socketio.on('sendAnswerPhase1')
def sendAnswerPhase1(data):
    # { "username": username, "answers": userAnswer}
    teamOfThePlayer = findTeamIdOfPlayer(data["username"])
    
    # if the team is not in the list of pourcentageAnswersForTheQuestion
    # add it with the username and the answers to match  [ { "teamId" : 1234, "answersByPlayer": [ { "username" : 1224, "answers":[12, 14, 14, 12] }] } ] 
    if teamOfThePlayer not in pourcentageAnswersForTheQuestion:
        pourcentageAnswersForTheQuestion.append({ "teamId": teamOfThePlayer, "answersByPlayer": [{ "username": data["username"], "answers": data["answers"] }]})
    else:
        for team in pourcentageAnswersForTheQuestion:
            if team["teamId"] == teamOfThePlayer:
                team["answersByPlayer"].append({ "username": data["username"], "answers": data["answers"] })

@socketio.on('sendAnswerPhase2')
def sendAnswerPhase2(data):
    # { "username": username, "finalAnswer": finalAnswer}
    teamOfThePlayer = findTeamIdOfPlayer(data["username"])
    print("hello")
    finalAnswersForTheQuestion.append({ "teamId": teamOfThePlayer, "finalAnswers": [{ "username": data["username"], "answer": data["finalAnswer"] }]})

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