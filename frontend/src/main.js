import { createApp } from 'vue'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'
import {createPinia} from 'pinia'
import App from './App.vue'
import router from './router.js'
import './style.css'

// init
const pinia = createPinia()

const app = createApp(App)

// registering store, router and ui librariess
app.use(pinia)
app.use(router)
app.use(PrimeVue, {
    theme: {
        preset: Aura
    },
    license: 'eyJpZCI6IjU4MGQzMjNiLWEwYjItNDY5MS04NTViLTJmNTkyODZkNTdjNiIsInByb2R1Y3QiOiJwcmltZXVpIiwidGllciI6ImNvbW11bml0eSIsInR5cGUiOiJkZXYiLCJpYXQiOjE3ODQyNjQwNzgsImV4cCI6MTgxNTgwMDA3OH0.VdB11IbnOeZcc7K8t9yPtparQaQ76UdTk3fqJsQJCeD6hxyTw0Qupfp1omobEc8oysQ-oedrMfzJ6ug9EJsVCg'
})
app.mount('#app')
