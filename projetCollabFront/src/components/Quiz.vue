<template>
  <div>
    <div>
      <h3>Teams</h3>
      <ul>
        <li v-for="(players, teamId) in teams" :key="teamId">
          <p>Team {{ teamId }}</p>
          <ul>
            <li v-for="(player, playerId) in players" :key="playerId">
              {{ player.username }}
            </li>
          </ul>
        </li>
      </ul>
    </div>
    <div class="quiz-container">
      <div class="event-zone">
        <h3>Event Log</h3>
        <ul>
          <li v-for="event in eventLog" :key="event.id">{{ event.message }}</li>
        </ul>
      </div>
      <div v-if="!username">
        <input type="text" v-model="tempUsername" placeholder="Enter your username">
        <button @click="joinQuiz">Join Quiz</button>
      </div>
      <div v-else>
        <div class="user-info">
          <p>Connected Users: {{ connectedUsers }}</p>
          <p>Users Answered: {{ usersAnswered }}</p>
          <p v-if="userTeam !== null">Your team: {{ userTeam }}</p>
        </div>
        <button @click="startQuiz" v-if="shouldShowStartButton">Start Quiz</button>
        <div v-if="quizStarted && question">
          <h2>{{ question.question }}</h2>
          <ul>
            <li v-for="(answer, index) in question.answers" :key="index">
              <button @click="submitAnswer(index)">{{ answer }}</button>
            </li>
          </ul>
          <p v-if="answerStatus" :style="{ color: answerStatus.color }">{{ answerStatus.message }}</p>
        </div>
      </div>
    </div>
    <div v-if="rankings">
      <h3>Rankings</h3>
      <ol>
        <li v-for="(user, score) in rankings" :key="user">{{ user }}: {{ score }}</li>
      </ol>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import io from 'socket.io-client';

const socket = io.connect('http://localhost:5000');
const tempUsername = ref('');
const username = ref('');
const quizStarted = ref(false);
const question = ref(null);
const eventLog = ref([]);
const answerStatus = ref(null);
const connectedUsers = ref(0);
const usersAnswered = ref(0);
const rankings = ref(null);
const teams = ref({});
const userTeam = ref(null);

const joinQuiz = () => {
  if (tempUsername.value) {
    username.value = tempUsername.value;
    socket.emit('join', { username: tempUsername.value, quiz_id: 'unique_quiz_id' });
  }
};

const startQuiz = () => {
  socket.emit('start_quiz', { quiz_id: 'unique_quiz_id' });
  quizStarted.value = true;
};

const submitAnswer = (index) => {
  socket.emit('answer', { answer: index, quiz_id: 'unique_quiz_id' });
};

const shouldShowStartButton = computed(() => {
  return username.value && !quizStarted.value;
});

socket.on('quiz_question', (data) => {
  question.value = data;
});

socket.on('message', (data) => {
  eventLog.value.push({ id: Date.now(), message: data });
});

socket.on('answer_status', (status) => {
  answerStatus.value = status;
});

socket.on('connected_users', (numUsers) => {
  connectedUsers.value = numUsers;
});

socket.on('users_answered', (numUsers) => {
  usersAnswered.value = numUsers;
});

socket.on('rankings', (data) => {
  rankings.value = data;
});

socket.on('teams_info', (data) => {
  teams.value = data;
  // Find the team of the current user
  for (const [teamId, players] of Object.entries(data)) {
    if (players.find(player => player.username === username.value)) {
      userTeam.value = teamId;
      break;
    }
  }
});
</script>

<style scoped>
.quiz-container {
  display: flex;
}

.event-zone {
  width: 400px;
  height: 300px; /* Fixed height */
  overflow-y: auto;
  background-color: #f2f2f2; /* Gray background */
  margin-right: 20px;
}

.user-info {
  margin-bottom: 10px;
}
</style>
