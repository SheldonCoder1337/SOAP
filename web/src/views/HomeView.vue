<template>
  <div class="welcome">
    <!-- <header class="glass-header">CISC7298 Project Report Demonstration: Semantic-Oriented Alignment for Prescription Generation</header> -->
    <h1>{{ title }}</h1>
    <button class="home-btn" @click="goToChat">Getting Started</button>
    <img src="/home.png" alt="Placeholder Image" />

    <footer>© 岐黄 2025 [WIP] v1.0.0</footer>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

const title = ref('岐黄')
const router = useRouter()

const goToChat = () => {
  router.push("/chat")
}

</script>


<style lang="less" scoped>
.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
  color: #333;
  text-align: center;

  background-image: url(/bgdown.png), url(/bgup.png);
  background-repeat: no-repeat, no-repeat;
  background-position: center bottom, center top; 
  background-size: cover, cover;
  background-blend-mode: multiply;
  
}



header {
  font-size: 1.2rem;
  font-weight: bold;
  color: var(--main-color);
  width: 100%;
  padding: 1rem 0;
  backdrop-filter: blur(10px);
  width: 100%;
  background-color: rgba(255, 255, 255, 0.25);
  border-bottom: 2px solid var(--main-color);
}

h1 {
  font-family: '华文新魏', sans-serif; /* 修改为你想要的字体 */
  font-size: 60px;
  font-weight: 600;
  color: #333; /* 可选：调整字体颜色 */
  margin-top: calc(20vh);
  margin-bottom: 0;
}

p {
  font-size: 18px;
  text-align: center;
}

button.home-btn {
  padding: 0.5rem 2rem;
  font-size: 24px;
  font-weight: bold;
  color: white;
  background-color: #333;
  border: none;
  border-radius: 3rem;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 20px;
  margin-bottom: calc(15vh - 80px);
  transition: all 0.3s;

  &:hover {
    background-color: #555;
    transform: translateY(-2px);
    box-shadow: 0px 5px 10px rgba(0, 0, 0, 0.1);
  }
}

img {
  width: 600px;
  height: auto;
  object-fit: cover;
  // box-shadow: 0px 5px 10px rgba(0, 0, 0, 0.05);
  border-radius: 1rem;
  max-width: 90%;
}

footer {
  font-size: 1rem;
  color: #666;
  margin-top: auto;
  padding: 1rem 0;
}

</style>
