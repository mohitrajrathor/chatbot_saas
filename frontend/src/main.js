import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'
import ConfirmationService from 'primevue/confirmationservice'
import { definePreset } from '@primeuix/themes'
import Aura from '@primeuix/themes/aura'

import App from './App.vue'
import router from './router'

import './style.css'
import 'primeicons/primeicons.css'

const app = createApp(App)
const pinia = createPinia()

const AppPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '#EEF2FF',
      100: '#E0E7FF',
      200: '#C7D2FE',
      300: '#A5B4FC',
      400: '#818CF8',
      500: '#6366F1',
      600: '#4F46E5',
      700: '#4338CA',
      800: '#3730A3',
      900: '#312E81',
    },
    colorScheme: {
      light: {
        surface: {
          0: '#FFFFFF',
          50: '#F8FAFC',
          100: '#F1F5F9',
          200: '#E2E8F0',
          300: '#CBD5E1',
          400: '#94A3B8',
          500: '#64748B',
          600: '#475569',
          700: '#334155',
          800: '#1E293B',
          900: '#0F172A',
        }
      }
    }
  }
})

app.use(pinia)
app.use(router)
app.use(PrimeVue, {
  licenseKey: import.meta.env.VITE_PRIMEVUE_LICENSE_KEY || import.meta.env.PRIMEVUE_LICENSE_KEY || '',
  theme: {
    preset: AppPreset,
    options: {
      darkModeSelector: false,
    }
  }
})
app.use(ToastService)
app.use(ConfirmationService)

app.mount('#app')
