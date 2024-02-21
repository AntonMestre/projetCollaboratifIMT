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

# Util functions =======================================================================
def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

def get_random_color():
    color = "%06x" % random.randint(0, 0xFFFFFF)
    return color

def get_random_team_name():
    word1 = ["Les"]
    word2 = ["triple moonstres", "beaux gosse", "loooosers", "super puissants"]
    word3 = ["de la mort", "de la loose", "de l'IMT", "de la win", "des proba stats"]
    return f"{random.choice(word1)} {random.choice(word2)} {random.choice(word3)}"

# Variables =======================================================================
possibleSatusOfQuizz = {1: "Waiting", 2: "Started"}
statusOfQuizz = possibleSatusOfQuizz.get(1)
quizzId = get_random_string(4)
quizzData = quiz_questions
teams = [] 
numberOfPeoplePerTeam = 2
pourcentageAnswersForTheQuestion = [] 
finalAnswersForTheQuestion = []

# Processing Functions =======================================================================
def addPlayerToATeam(username, sid):
    didFoundATeam = False

    for team in teams:
        if len(team["players"]) < numberOfPeoplePerTeam:
            team["players"].append({ "id": sid, "username": username})
            didFoundATeam = True
            break
        
    if not didFoundATeam:
        teams.append({ "id": get_random_string(4), "name": get_random_team_name(), "color": get_random_color(), "players": [{ "id": sid, "username": username}], "numberOfGoodAnswer": 0})

def findTeamNameOfPlayer(username):
    userTeam = ""

    for team in teams:
        for player in team["players"]:
            if player["username"] == username:
                userTeam = team["id"]
                break

    return userTeam

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
    answersProcessed = []

    for team in pourcentageAnswersForTheQuestion:
        sumAnswers = [0, 0, 0, 0]
        for player in team["answersByPlayer"]:
            for i in range(len(player["answers"])):
                sumAnswers[i] += player["answers"][i]
        answersProcessed.append({ "teamId": team["teamId"], "answers": [ x / len(team["answersByPlayer"]) for x in sumAnswers ]})

    socketio.emit('processedAnswers', answersProcessed, room=quizzId)

def displayTheCorrectAnswer(correct):
    for part in quizzData:
        for answer in part.get("answers"):
            if answer.get("id") == correct:
                socketio.emit('correctAnswer', answer, room=quizzId)
                break

def processGoodAnswerByTeams(correct):
    for team in finalAnswersForTheQuestion:
        possible_answers = set(answer["answer"] for answer in team["finalAnswers"])
        mostRepresentativeAnswer = max(possible_answers, key=team["finalAnswers"].count)
        socketio.emit('mostRepresentativeAnswer', { "teamId": team["teamId"], "answer": mostRepresentativeAnswer }, room=quizzId)
        if mostRepresentativeAnswer == correct:
            for teamInTeams in teams:
                if teamInTeams["id"] == team["teamId"]:
                    teamInTeams["numberOfGoodAnswer"] += 1
                    

def displayTheRanking():
    ranking = sorted(teams, key=lambda x: x['numberOfGoodAnswer'], reverse=True)
    socketio.emit('ranking', ranking, room=quizzId)

def resetValuesOfAnswers():
    global pourcentageAnswersForTheQuestion
    pourcentageAnswersForTheQuestion = []
    global finalAnswersForTheQuestion
    finalAnswersForTheQuestion = []

def sendTheAnswerOfTheTeams():
    socketio.emit('answersOfTheTeams', finalAnswersForTheQuestion, room=quizzId)

def rollingTheQuizz():
    with app.test_request_context():
        for part in quizzData:
            resetValuesOfAnswers()

            socketio.emit('phase1Starting', room=quizzId)
            displayQuestionAndAnswers(part.get("question"), part.get("answers"))
            time.sleep(15)
            socketio.emit('phase1Ended', room=quizzId)
            
            time.sleep(1)
            displayProcessedAnswers()
            time.sleep(20)
            socketio.emit('phase2Ended', room=quizzId)

            time.sleep(1)
            processGoodAnswerByTeams(part.get("correctID"))
            sendTheAnswerOfTheTeams()
            
            displayTheCorrectAnswer(part.get("correctID"))
            displayTheRanking()
            time.sleep(5)
        socketio.emit('quizzEnded', room=quizzId)


# Websockets Functions =======================================================================
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('getStatusOfQuizz')
def getStatusOfQuizz():
     emit('getStatusOfQuizz', statusOfQuizz)

@socketio.on('joinWaitingRoom')
def joinWaitingRoom(data):
    username = data["username"] or get_random_string(4)
    join_room(quizzId)
    
    addPlayerToATeam(username, request.sid)
    teamOfThePlayer = findTeamNameOfPlayer(username)
    teamIdOfThePlayer = findTeamIdOfPlayer(username)

    emit('teams', teams, room=quizzId)
    emit('username', username)
    emit('userTeam', teamOfThePlayer)
    emit('teamId', teamIdOfThePlayer)

@socketio.on('startTheQuizz')
def startTheQuizz():
    statusOfQuizz = possibleSatusOfQuizz.get(2)
    emit('quizzHasStarted', room=quizzId)
    emit('getStatusOfQuizz', statusOfQuizz, room=quizzId)

    Thread(target=rollingTheQuizz).start()


@socketio.on('sendAnswerPhase1')
def sendAnswerPhase1(data):
    teamOfThePlayer = findTeamIdOfPlayer(data["username"])

    for team in pourcentageAnswersForTheQuestion:
        if team["teamId"] == teamOfThePlayer:
            team["answersByPlayer"].append({ "username": data["username"], "answers": data["answers"] })
            return
    
    pourcentageAnswersForTheQuestion.append({ "teamId": teamOfThePlayer, "answersByPlayer": [{ "username": data["username"], "answers": data["answers"] }]})


@socketio.on('sendAnswerPhase2')
def sendAnswerPhase2(data):
    teamOfThePlayer = findTeamIdOfPlayer(data["username"])
    finalAnswersForTheQuestion.append({ "teamId": teamOfThePlayer, "finalAnswers": [{ "username": data["username"], "answer": data["finalAnswer"] }]})

if __name__ == '__main__':
    socketio.run(app)