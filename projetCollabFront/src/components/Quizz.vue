<script setup>
import { ref, computed } from 'vue';
import io from 'socket.io-client';

const socket = io.connect('http://localhost:5000');
const statusOfQuizz = ref(false);
const username = ref('');
const teams = ref([]);
const teamOfThePlayer = ref('');
const isInTheWaitingRoom = ref(false);
const actualQuestion = ref('');
const actualAnswers = ref([]);
const userAnswer = ref([0,0,0,0]);
const remainingToDistribute = computed(() => {
  return 100 - userAnswer.value.reduce((a, b) => Number(a) + Number(b), 0);
});

const phase = ref('');
const teamIdOfThePlayer = ref('');
const confidenceOfTheTeamOnTheAnswer = ref([]);
const isProcessingAnswersOfPhase1 = ref(false);
const finalAnswer = ref('');
const correctAnswer = ref('');
const ranking = ref([]);
const quizzEnded = ref(false);
const teamAnswer = ref('');

const counter = ref(20);
setInterval(() => {
  if (counter.value > 0) {
    counter.value--;
  }
}, 1000);

const answerColors = [
    '#FF203B',
    '#6AC03B',
    '#FEC00A',
    '#45A2E5',
];

socket.on('mostRepresentativeAnswer', (data) => {
  if(data.teamId === teamIdOfThePlayer.value) {
    console.log(data.answer)
    teamAnswer.value = data.answer
  }
})

/* Status Of Quizz part */
const getStatusOfQuizz = () => {
    socket.emit('getStatusOfQuizz');
};
socket.on('getStatusOfQuizz', (data) => {
    statusOfQuizz.value = data;
});

/* Join Quizz part */
const joinQuiz = () => {
    socket.emit('joinWaitingRoom', { "username": username.value });
    isInTheWaitingRoom.value = true;
};
socket.on('userTeam', (data) => {
    teamOfThePlayer.value = data;
});
socket.on('username', (data) => {
    username.value = data;
});
socket.on('teamId', (data) => {
    teamIdOfThePlayer.value = data;
});
socket.on('teams', (data) => {
    teams.value = data;
});

/* Start Quizz part */
const startQuizz = () => {
    socket.emit('startTheQuizz');
};
socket.on('quizzHasStarted', () => {
    phase.value = 'phase1';
});
socket.on('questionAndAnswers', (data) => {
    actualQuestion.value = data.question;
    actualAnswers.value = data.answers;
});

/* Quizz rolling */
socket.on("phase1Starting", (data) => {
    userAnswer.value = [0,0,0,0];
    finalAnswer.value = '';
    correctAnswer.value = '';
    teamAnswer.value = '';
    counter.value = 15;
    phase.value = 'phase1';
});
socket.on('phase1Ended', (data) => {
    // verifier les valeurs des answersj'attend [15, 22, 39, 45]
    phase.value = 'phase2';
    isProcessingAnswersOfPhase1.value = true;
    // convert string to numbers in the array userAnswer
    userAnswer.value = userAnswer.value.map(Number);
    counter.value = 20;
    socket.emit('sendAnswerPhase1', { "username": username.value, "answers": userAnswer.value});
});
socket.on('processedAnswers', (data) => {
    // find by the answers array the team of the user in the data wich is in the form of [ { "teamId" : 1234, "answers": [12, 14, 14, 12] } ]
    let team = data.find(team => team.teamId == teamIdOfThePlayer.value);
    confidenceOfTheTeamOnTheAnswer.value = team.answers;
    isProcessingAnswersOfPhase1.value = false;
});
socket.on('phase2Ended', (data) => {
    phase.value = 'phase3';
    socket.emit('sendAnswerPhase2', { "username": username.value, "finalAnswer": finalAnswer.value});
});
socket.on('correctAnswer', (data) => {
    correctAnswer.value = data;
});
socket.on('ranking', (data) => {
    ranking.value = data;
});
socket.on('quizzEnded', (data) => {
    console.log("quiz ended")
    quizzEnded.value = true;
});

getStatusOfQuizz();
</script>
<template>
    <div v-if="!teamOfThePlayer && statusOfQuizz == 'Started'">Le quizz a commencé, merci d'attendre</div>
    <div v-if="!isInTheWaitingRoom && statusOfQuizz != 'Started'" id="join-quizz">
        <h1>Enter your pseudo</h1>
        <div id="join-quizz-inputs">
            <input type="text" placeholder="Pseudo" v-model="username">
            <button @click="joinQuiz" :disabled="username === ''">→</button>
        </div>
    </div>
    <div v-if="teamOfThePlayer && statusOfQuizz == 'Waiting'" id="waiting-room">
        <h1>Waiting room</h1>
        <div id="waiting-room-container">
            <div id="teams-container">
                <div v-for="team in teams" :key="team.id" class="team">
                    <h3 :style="{ color: '#' + team.color }">{{ team.name }}</h3>
                    <div class="teammates-container">
                        <div  v-for="teammate in team.players" :key="teammate.id" class="teammate" :style="{ backgroundColor: '#' + team.color }">
                            {{ teammate.username}} {{ teammate.username === username ? '(you)' : '' }}
                        </div>
                    </div>
                </div>
            </div>
            <div id="instructions-container">
                <div id="instructions">
                    <h2>How to play ???</h2>
                    <p>
                      Each question is divided in two rounds. In the first round, you have to distribute your confidence on each answers.
                      Then you have a few seconds to discuss with your team and choose the final answer, based on the average confidence for each answer.
                    </p>
                </div>
                <button v-if="isInTheWaitingRoom && statusOfQuizz == 'Waiting'" @click="startQuizz">Start the quizz →</button>
            </div>
        </div>
    </div>
    <!-- QUIZZ PART -->
    <div v-if="statusOfQuizz == 'Started' && phase == 'phase1'" class="quizz-container">
        <div id="quizz-header">
            <h3>Round 1</h3>
            <h1>{{ actualQuestion }}</h1>
            <div id="counter">{{counter}}</div>
        </div>
        <div class="answers-container">
            <div v-for="(answer, index) in actualAnswers" :key="index" class="answer-container" :style="{backgroundColor: answerColors[index]}">
                <h3>{{ answer.answer }}</h3>
                <div class="range-container">
                    <p>Sure at <span>{{ userAnswer[index] }} %</span></p>
                    <div class="range-input-container">
                        <div>0%</div>
                        <input type="range" min="1" max="100" v-model="userAnswer[index]">
                        <div>100%</div>
                    </div>
                </div>
            </div>
            <div id="quizz-percentage-to-distribute">
                <span>{{ remainingToDistribute }} %</span> to distribute
            </div>
        </div>
    </div>
    <div id="phase2" v-if="statusOfQuizz == 'Started' && phase == 'phase2'" class="quizz-container">
        <div id="quizz-header">
            <h3>Round 2</h3>
            <h1>{{ actualQuestion }}</h1>
            <div id="counter">{{counter}}</div>
        </div>
        <div class="answers-container">
            <div v-for="(answer, index) in actualAnswers" :key="index" class="answer-container" :style="{backgroundColor: answerColors[index]}" :class="{ 'selected': finalAnswer == index + 1 }" @click="finalAnswer = (index + 1).toString()">
                <template v-if="!isProcessingAnswersOfPhase1">
                    <h3>{{answer.answer}}</h3>
                    <p class="answer-confidence">{{confidenceOfTheTeamOnTheAnswer[index]}} % confidence</p>
                </template>
            </div>
        </div>
    </div>
    <div id="phase3" v-if="statusOfQuizz == 'Started' && phase == 'phase3' && !quizzEnded"  class="quizz-container">
        <div id="quizz-header">
            <h3>Round 2</h3>
            <h1>{{ actualQuestion }}</h1>
            <div></div>
        </div>
        <div class="answers-container">
          {{console.log(teamAnswer)}}
            <div v-for="(answer, index) in actualAnswers" :key="index" class="answer-container" :style="{backgroundColor: answerColors[index]}" :class="{ 'selected': correctAnswer.id == index + 1, 'team-answer': teamAnswer == answer.id}">
                <template v-if="correctAnswer !== ''">
                  <p v-if="answer.id == teamAnswer" id="team-answer-indicator">Your team answer</p>
                  <h3>{{answer.answer}}</h3>
                    <p class="answer-confidence">{{confidenceOfTheTeamOnTheAnswer[index]}} % confidence</p>
                    <div class="answer-icon" v-if="correctAnswer.id === index + 1">
                        <svg width="83" height="83" viewBox="0 0 83 83" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <rect y="48.139" width="15.1136" height="47.9692" transform="rotate(-44.2429 0 48.139)" fill="white"/>
                            <rect x="33.4688" y="82.5036" width="15.1136" height="68.9968" transform="rotate(-134.243 33.4688 82.5036)" fill="white"/>
                        </svg>
                    </div>
                    <div class="answer-icon" v-else>
                        <svg width="60" height="59" viewBox="0 0 60 59" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M10.5455 58.9664L0.000691027 48.1392L49.4292 0L59.9739 10.8272L10.5455 58.9664Z" fill="white"/>
                            <path d="M59.9752 48.1377L49.4309 58.9654L0 10.8287L10.5442 0.000982196L59.9752 48.1377Z" fill="white"/>
                        </svg>
                    </div>
                </template>
            </div>
        </div>
    </div>
    <div id="podium" v-if="quizzEnded">
        <div v-for="(rank, index) in ranking.slice(0, 3)" :key="index" :id="'podium' + (index + 1)" :style="{ backgroundColor: '#' + rank.color }">
            <h1>{{ rank.name }}</h1>
            <h2>{{ index + 1 }}</h2>
        </div>
    </div>
</template>
<style>
#join-quizz {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    background-color: #7000FF;
}

#join-quizz h1 {
    color: white;
    font-weight: normal;
    font-size: 3rem;
    margin: 0;
}

#join-quizz-inputs {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;
    height: 10%;
    margin-top: 3vh;
    column-gap: 1vw;
}

#join-quizz-inputs input, #join-quizz-inputs button {
    padding: 10px;
    border: none;
    border-radius: 2px;
    font-size: 2rem;
    height: 100%;
    box-sizing: border-box;
}

#join-quizz-inputs input {
    color: black;
    font-family: "Londrina Solid", sans-serif;
    text-align: center;
}

#join-quizz-inputs input:focus {
    outline: none;
}

#join-quizz-inputs input::placeholder {
    color: black;
    font-family: "Londrina Solid", sans-serif;
    font-size: 2rem;
    text-align: center;
}

#join-quizz-inputs button {
    color: #7000FF;
    background-color: white;
    aspect-ratio: 1/1;
    transition: all 0.3s;
    opacity: 1;
}

#join-quizz-inputs button:hover {
    background-color: #E0E0E0;
}

#join-quizz-inputs button:disabled {
    opacity: .5;
}

#waiting-room {
    height: 100vh;
}
#waiting-room h1 {
    font-size: 3rem;
    margin: 0;
    text-align: center;
    background-color: white;
    color: #7000FF;
    font-weight: normal;
    padding: 2vh 0;
}

#waiting-room-container {
    display: flex;
    flex-direction: row;
    margin-top: 10vh;
    margin-left: 4vw;
    margin-right: 4vw;
}

#teams-container {
    display: flex;
    flex-direction: column;
    width: 65%;
}

.team {
    margin-bottom: 3vh;
}

#teams-container h3 {
    font-size: 1.5rem;
    margin: 0;
    padding: 1vh 0;
}

.teammates-container {
    display: flex;
    flex-direction: row;
    column-gap: 1vw;
    align-items: center;
}

.teammate {
    color: white;
    border-radius: 4px;
    font-size: 1.2em;
    padding: 1vh 1vw;
}

#instructions-container {
    display: flex;
    flex-direction: column;
    width: 35%;
}

#instructions {
    background-color: white;
    border-radius: 4px;
    padding: 3vh 3vw;
}

#instructions h2 {
    font-size: 2rem;
    margin: 0;
    text-align: center;
    font-weight: normal;
}

#instructions p {
    margin: 0;
    padding-top: 2vh;
    padding-bottom: 2vh;
    text-align: justify;
    font-family: "Roboto", sans-serif;
    font-weight: lighter;
}

#instructions-container button {
    background-color: #7000FF;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 1.5vh 2vw;
    font-size: 1.3rem;
    margin-top: 8vh;
    transition: background-color 0.3s;
    font-family: "Londrina Solid", sans-serif;
}

.quizz-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
}

.quizz-container #quizz-header {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    margin: 0;
    text-align: center;
    background-color: white;
    padding: 2vh 2vw;
}

#quizz-header h1 {
    font-size: 3rem;
    color: #7000FF;
    font-weight: normal;
    margin: 0;
}

#quizz-header h3 {
    font-size: 2rem;
    color: #B5B5B5;
    font-weight: normal;
    margin: 0;
}

#quizz-header #counter {
    font-size: 1.6rem;
    color: white;
    font-weight: normal;
    background-color: #7000FF;
    border-radius: 50%;
    width: 5vw;
    height: 5vw;
    padding: 1vw;
    display: flex;
    justify-content: center;
    align-items: center;
    box-sizing: border-box;
}

.answers-container {
    position: relative;
    display: grid;
    grid-template-columns: 1fr 1fr;
    height: 100%;
    margin: 4vh 6vw;
    column-gap: 3vw;
    row-gap: 3vw;
}

.answers-container h3 {
    font-size: 3rem;
    color: white;
    font-weight: normal;
    margin: 0;
    text-align: center;
}

.answer-container {
    display: flex;
    position: relative;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2vh 2vw;
    border-radius: 4px;
    transition: opacity 0.2s, outline-width 0.1s;
    outline: #7000FF 0 solid;
}

.answer-icon {
    position: absolute;
    top: 50%;
    right: 0;
    transform: translate(-80%, -50%);
}

.answer-icon svg {
    width: 4vw;
    height: 4vw;
}

#phase2 .answer-container {
    cursor: pointer;
}

.answer-container.selected {
    opacity: 1 !important;
    outline: #7000FF 5px solid;
}

#phase3 .answer-container {
    opacity: .2;
}

#phase3 .answer-container.selected {
    outline: none
}

.answer-container:not(:hover) {
    opacity: 0.5;
}

.range-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 100%;
    color: white;
    transition: opacity 0.3s; /* animate the opacity change */
}

.range-container span {
    font-size: 1.5rem;
    font-weight: normal;
}

.range-input-container {
    flex-direction: row;
    align-items: center;
    justify-content: center;
    column-gap: 1vw;
    color: white;
    font-size: 1.3rem;
    font-weight: normal;
    width: 90%;
    display: flex;
}

.range-input-container input[type="range"] {
    width: 100%;
}


#quizz-percentage-to-distribute {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    padding: 1.5vh 2vw;
    background-color: white;
    color: black;
    font-size: 1.5rem;
    border-radius: 10px;
    border: #E9E9E9 10px solid;
}

#quizz-percentage-to-distribute span {
    color: #7000FF;
}

.answer-confidence {
    font-size: 2rem;
    color: white;
    font-weight: normal;
    margin: 0;
}

#podium {
    height: 100vh;
    background-color: #7000FF;
    position: relative;
}

#podium1, #podium2, #podium3 {
    position: absolute;
}

#podium1 {
    bottom: 0%;
    left: 50%;
    transform: translate(-50%, 0);
    width: 20%;
    height: 75%;
}

#podium2 {
    bottom: 0%;
    left: 30%;
    transform: translate(-50%, 0);
    width: 20%;
    height: 60%;
}

#podium3 {
    bottom: 0%;
    left: 70%;
    transform: translate(-50%, 0);
    width: 20%;
    height: 50%;
}

#podium h1 {
    font-size: 2rem;
    color: white;
    font-weight: normal;
    margin: 0;
    text-align: center;
    background-color: #7000FF;
    padding-bottom: 4vh;
}

#podium h2 {
    font-size: 5rem;
    color: white;
    font-weight: normal;
    margin: 0;
    text-align: center;
    padding-top: 4vh;
}

.team-answer {
  outline: #7000FF 5px solid !important;
}

#team-answer-indicator {
  position: absolute;
  top: 5%;
  left: 5%;
  color: #7000FF;
  font-size: 3rem;
  padding: 0;
  margin: 0;
}

</style>