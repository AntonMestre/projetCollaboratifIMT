<script setup>
import { ref, computed } from 'vue';
import io from 'socket.io-client';

const socket = io.connect('http://localhost:5000');
const is_quiz_started = ref(false);
const username = ref('');

const joinPresentationQuiz = () => {
    socket.emit('joinPresentationQuiz');
};

const joinQuiz = () => {
    socket.emit('joinQuiz');
};

socket.on('is_quiz_started', (data) => {
    is_quiz_started.value = data;
});

</script>
<template>
    <h1>QUIZZ</h1>
    <div v-if="is_quiz_started">Le quizz a commencé, merci d'attendre</div>
    <div v-else>
        <button @click="joinQuiz">Rejoindre la salle d'attente du quizz</button>
    </div>
</template>
<style>
</style>