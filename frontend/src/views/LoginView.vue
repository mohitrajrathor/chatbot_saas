<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'

const email = ref('')
const password = ref('')
const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const toast = useToast()

async function handleLogin() {
  if (!email.value || !password.value) {
    toast.add({ severity: 'warn', summary: 'Missing Fields', detail: 'Please fill in both email and password.', life: 3000 })
    return
  }

  const success = await authStore.login(email.value, password.value)
  if (success) {
    toast.add({ severity: 'success', summary: 'Welcome back!', detail: 'Successfully logged in.', life: 3000 })
    const redirectPath = route.query.redirect || '/dashboard'
    router.push(redirectPath)
  } else {
    toast.add({ severity: 'error', summary: 'Login Failed', detail: authStore.error, life: 4000 })
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-50 px-4 py-12">
    <div class="w-full max-w-md bg-white border border-slate-200 rounded-xl p-8 space-y-6">
      <div class="text-center space-y-2">
        <h1 class="text-2xl font-bold tracking-tight text-slate-900">Sign in to your account</h1>
        <p class="text-xs text-slate-500">Access your chatbots, documents, and RAG analytics</p>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-4">
        <div class="space-y-1">
          <label class="block text-xs font-medium text-slate-700">Email Address</label>
          <InputText
            v-model="email"
            type="email"
            placeholder="name@company.com"
            class="w-full text-sm px-3 py-2 border border-slate-200 rounded-md focus:ring-2 focus:ring-indigo-500"
            required
          />
        </div>

        <div class="space-y-1">
          <label class="block text-xs font-medium text-slate-700">Password</label>
          <InputText
            v-model="password"
            type="password"
            placeholder="••••••••"
            class="w-full text-sm px-3 py-2 border border-slate-200 rounded-md focus:ring-2 focus:ring-indigo-500"
            required
          />
        </div>

        <Button
          type="submit"
          :loading="authStore.loading"
          label="Sign In"
          class="w-full bg-indigo-500 hover:bg-indigo-600 text-white font-medium text-sm py-2 rounded-md transition cursor-pointer"
        />
      </form>

      <div class="text-center text-xs text-slate-500 border-t border-slate-100 pt-4">
        Don't have an account yet?
        <router-link to="/register" class="text-indigo-600 font-semibold hover:underline">
          Create account
        </router-link>
      </div>
    </div>
  </div>
</template>
