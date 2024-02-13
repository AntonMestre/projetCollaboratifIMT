<script setup>
import { ref, computed } from 'vue';
import io from 'socket.io-client';

const socket = io.connect('http://localhost:5000');
const statusOfQuizz = ref(false);
const username = ref('');
const teamOfThePlayer = ref('');
const isInTheWaitingRoom = ref(false);
const actualQuestion = ref('');
const actualAnswers = ref([]);
const userAnswer = ref([]);

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

/* Start Quizz part */
const startQuizz = () => {
    socket.emit('startTheQuizz');
};
socket.on('quizzHasStarted', () => {
    
});
socket.on('questionAndAnswers', (data) => {
    console.log(data)
    actualQuestion.value = data.question;
    actualAnswers.value = data.answers;
});

/* Quizz rolling */
socket.on('phase1Ended', (data) => {
    // verifier les valeurs des answersj'attend [15, 22, 39, 45]
    console.log(userAnswer);
    emit('sendAnswerPhase1', { "username": username, "answers": userAnswer});
});


getStatusOfQuizz();
</script>
<template>
    <h1>QUIZZ</h1>
    <div v-if="!teamOfThePlayer && statusOfQuizz == 'Started'">Le quizz a commencé, merci d'attendre</div>
    <div v-else>
        <button v-if="!isInTheWaitingRoom" @click="joinQuiz">Rejoindre la salle d'attente du quizz</button>
    </div>
    <div v-if="teamOfThePlayer && statusOfQuizz == 'Waiting'">
        <p>Vous êtes dans l'équipe : {{ teamOfThePlayer }}</p>
        <p>Votre nom d'utilisateur est : {{ username }}</p>
        <p>Vous etes dans la salle d'attente</p>
    </div>
    <div>
        <button v-if="isInTheWaitingRoom && statusOfQuizz == 'Waiting'" @click="startQuizz">Lancer le quizz</button>
    </div>
    <!-- QUIZZ PART -->
    <div v-if="statusOfQuizz == 'Started'">
        <div>
            <p>Question : {{ actualQuestion }}</p>
            <p>
                <div class="slidecontainer">
                    <ul>
                        <li v-for="(answer, index) in actualAnswers" :key="answer.id" >
                            <label :for="answer.id">{{ answer.answer }}</label>
                            <input type="range" min="1" max="100" value="50" :id="answer.id" :name="answer.id" v-model="userAnswer[answer]">
                        </li>
                    </ul>
                </div>
            </p>
        </div>
    </div>
</template>
<style>
</style>