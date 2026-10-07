import { createApp } from 'vue'
import App from './App.vue'
import router from './router/index.js'
import { fetchMe } from './store/auth.js'
import './styles.css'

fetchMe()
const app = createApp(App)
app.use(router)
app.mount('#app')