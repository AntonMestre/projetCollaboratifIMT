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
    const phase = ref('');
const teamIdOfThePlayer = ref('');
const confidenceOfTheTeamOnTheAnswer = ref([]);
const isProcessingAnswersOfPhase1 = ref(false);
const finalAnswer = ref('');
const correctAnswer = ref('');
const ranking = ref([]);

/* Status Of Quizz part */
const getStatusOfQuizz = () => {
    socket.emit('getStatusOfQuizz');
};
socket.on('getStatusOfQuizz', (data) => {
    statusOfQuizz.value = data;
});

/* Join Quizz part */
const joinQuiz = () => {
    socket.emit('joinWaitingRoom');
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
    console.log(data);
});

/* Start Quizz part */
const startQuizz = () => {
    socket.emit('startTheQuizz');
};
socket.on('quizzHasStarted', () => {
    phase.value = 'phase1';
});
socket.on('questionAndAnswers', (data) => {
    console.log(data)
    actualQuestion.value = data.question;
    actualAnswers.value = data.answers;
});

/* Quizz rolling */
socket.on("phase1Starting", (data) => {
    phase.value = 'phase1';
});
socket.on('phase1Ended', (data) => {
    // verifier les valeurs des answersj'attend [15, 22, 39, 45]
    phase.value = 'phase2';
    isProcessingAnswersOfPhase1.value = true;
    // convert string to numbers in the array userAnswer
    userAnswer.value = userAnswer.value.map(Number);
    
    socket.emit('sendAnswerPhase1', { "username": username.value, "answers": userAnswer.value});
});
socket.on('processedAnswers', (data) => {
    // find by the answers array the team of the user in the data wich is in the form of [ { "teamId" : 1234, "answers": [12, 14, 14, 12] } ]
    console.log(teamIdOfThePlayer.value);
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

getStatusOfQuizz();
</script>
<template>
    <div v-if="!teamOfThePlayer && statusOfQuizz == 'Started'">Le quizz a commencé, merci d'attendre</div>
    <div v-if="!isInTheWaitingRoom && statusOfQuizz != 'Started'" id="join-quizz">
        <h1>Enter your pseudo</h1>
        <div id="join-quizz-inputs">
            <input type="text" placeholder="Pseudo">
            <button @click="joinQuiz">→</button>
        </div>
    </div>
    <div v-if="teamOfThePlayer && statusOfQuizz == 'Waiting'" id="waiting-room">
        <h1>Waiting room</h1>
        <div id="waiting-room-container">
            <div id="teams-container">
                <div v-for="team in teams" :key="team.id" class="team">
                    <h3 :style="{ color: '#' + team.color }">{{ team.name }}</h3>
                    <div class="teammates-container">
                        <div v-for="teammate in team.players" :key="teammate.id" class="teammate" :style="{ backgroundColor: '#' + team.color }">
                            {{ teammate.username }}
                        </div>
                    </div>
                </div>
            </div>
            <div id="instructions-container">
                <div>
                    <button v-if="isInTheWaitingRoom && statusOfQuizz == 'Waiting'" @click="startQuizz">Lancer le quizz</button>
                </div>
            </div>
        </div>
    </div>
    <!-- QUIZZ PART -->
    <div v-if="statusOfQuizz == 'Started' && phase == 'phase1'">
        <div>
            <p>Question : {{ actualQuestion }}</p>
            <p>
                <div class="slidecontainer">
                    <ul>
                        <li>
                            <label >{{ actualAnswers[0].answer }}</label> 
                            <input type="range" min="1" max="100" value="0" id="answer.id" v-model="userAnswer[0]">
                        </li>
                        <li>
                            <label >{{ actualAnswers[1].answer }}</label> 
                            <input type="range" min="1" max="100" value="0" id="answer.id" v-model="userAnswer[1]">
                        </li>
                        <li>
                            <label >{{ actualAnswers[2].answer }}</label> 
                            <input type="range" min="1" max="100" value="0" id="answer.id" v-model="userAnswer[2]">
                        </li>
                        <li>
                            <label >{{ actualAnswers[3].answer }}</label> 
                            <input type="range" min="1" max="100" value="0" id="answer.id" v-model="userAnswer[3]">
                        </li>
                    </ul>
                </div>
            </p>
        </div>
    </div>
    <div v-if="statusOfQuizz == 'Started' && phase == 'phase2' && !isProcessingAnswersOfPhase1">
        <ul>
            <li>
                <label >{{ actualAnswers[0].answer }} | Confidence of the team: {{ confidenceOfTheTeamOnTheAnswer[0] }}</label> 
                <input type="radio" v-model="finalAnswer" name="finalAnswer" :value="1">
            </li>
            <li>
                <label >{{ actualAnswers[1].answer }} | Confidence of the team: {{ confidenceOfTheTeamOnTheAnswer[1] }}</label> 
                <input type="radio" v-model="finalAnswer" name="finalAnswer" :value="2">
            </li>
            <li>
                <label >{{ actualAnswers[2].answer }} | Confidence of the team: {{ confidenceOfTheTeamOnTheAnswer[2] }}</label> 
                <input type="radio" v-model="finalAnswer" name="finalAnswer" :value="3">
            </li>
            <li>
                <label >{{ actualAnswers[3].answer }} | Confidence of the team: {{ confidenceOfTheTeamOnTheAnswer[3] }}</label> 
                <input type="radio" v-model="finalAnswer" name="finalAnswer" :value="4">
            </li>
        </ul>
    </div>
    <div v-if="statusOfQuizz == 'Started' && phase == 'phase3'">
        <p>La bonne réponse était:  {{ correctAnswer.answer }}</p>
        <p>Classement: {{ console.log(ranking) }}</p>
        <ul>
            <li v-for="team in ranking">{{ team.id }} - {{ team.numberOfGoodAnswer }}</li>
        </ul>
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
    height: 8vh;
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
    transition: background-color 0.3s;
}

#join-quizz-inputs button:hover {
    background-color: #E0E0E0;
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
</style>