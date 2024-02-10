from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
import json
import random

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="http://localhost:5173")

with open('quiz_questions.json', 'r') as file:
    quiz_questions = json.load(file)

quizzes = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join(data):
    username = data['username']
    quiz_id = data['quiz_id']
    join_room(quiz_id)

    if quiz_id not in quizzes:
        quizzes[quiz_id] = {'participants': {}, 'answers': {}, 'asked_questions': [], 'teams': {}}

    incomplete_teams = [team_id for team_id, players in quizzes[quiz_id]['teams'].items() if len(players) < 2]
    
    if incomplete_teams:
        team_id = incomplete_teams[0]
    else:
        team_id = len(quizzes[quiz_id]['teams']) + 1
    
    quizzes[quiz_id]['teams'].setdefault(team_id, []).append(request.sid)
    quizzes[quiz_id]['participants'][request.sid] = {'username': username, 'team_id': team_id}
    
    emit('message', f"{username} joined the quiz", room=quiz_id)
    emit('connected_users', len(quizzes[quiz_id]['participants']), room=quiz_id)
    emit('teams_info', quizzes[quiz_id]['teams'], room=quiz_id)
    emit('user_team_info', {'team_id': team_id}, room=request.sid)

@socketio.on('start_quiz')
def handle_start_quiz(data):
    quiz_id = data['quiz_id']
    if quiz_id in quizzes:
        available_questions = [q for q in quiz_questions if q not in quizzes[quiz_id]['asked_questions']]
        if available_questions:
            question = random.choice(available_questions)
            quizzes[quiz_id]['asked_questions'].append(question)
            quizzes[quiz_id]['question'] = question
            quizzes[quiz_id]['answers'] = {}

            emit('quiz_question', question, room=quiz_id)
            emit('start_quiz', room=quiz_id)
        else:
            emit('message', "All questions have been asked in this quiz", room=quiz_id)
            rankings = compute_rankings(quizzes[quiz_id]['answers'])
            emit('rankings', rankings, room=quiz_id)

def compute_rankings(answers):
    # Count correct answers for each participant
    scores = {}
    
    for user, answer in answers.items():
        scores[user] = scores.get(user, 0) + 1 if answer else 0
   
    # Sort participants by score
    rankings = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return rankings

if __name__ == '__main__':
    socketio.run(app)
