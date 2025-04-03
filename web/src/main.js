import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

import Antd from 'ant-design-vue';
import 'ant-design-vue/dist/reset.css';
import './assets/main.css'

import { createI18n } from 'vue-i18n' 
import en from './locales/en.json'
import cn from './locales/cn.json'

const i18n = createI18n({
    locale: 'cn',
    fallbackLocale: 'en',
    messages: {
        en,
        cn
    }
});


const app = createApp(App)

app.use(i18n)
app.use(createPinia())
app.use(router)
app.use(Antd)

app.mount('#app')
