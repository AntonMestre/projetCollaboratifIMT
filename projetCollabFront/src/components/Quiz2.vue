<script setup>
import { ref, computed } from 'vue';
import io from 'socket.io-client';

const socket = io.connect('http://localhost:5000');
const statusOfQuizz = ref(false);
const username = ref('');
const teamOfThePlayer = ref('');

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
};
socket.on('userTeam', (data) => {
    teamOfThePlayer.value = data;
});
socket.on('username', (data) => {
    username.value = data;
});

</script>
<template>
    <h1>QUIZZ</h1>
    <div v-if="statusOfQuizz == 'Started'">Le quizz a commencé, merci d'attendre</div>
    <div v-else>
        <button @click="joinQuiz">Rejoindre la salle d'attente du quizz</button>
    </div>
    <div v-if="teamOfThePlayer">
        <p>Vous êtes dans l'équipe : {{ teamOfThePlayer }}</p>
        <p>Votre nom d'utilisateur est : {{ username }}</p>
        <p>Vous etes dans la salle d'attente</p>
    </div>
</template>
<style>
</style>