<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const router = useRouter()
const authStore = useAuthStore()
const toast = useToast()

async function handleRegister() {
  if (!email.value || !password.value || !confirmPassword.value) {
    toast.add({ severity: 'warn', summary: 'Missing Fields', detail: 'Please fill in all required fields.', life: 3000 })
    return
  }

  if (password.value !== confirmPassword.value) {
    toast.add({ severity: 'error', summary: 'Password Mismatch', detail: 'Passwords do not match.', life: 3000 })
    return
  }

  const success = await authStore.register(email.value, password.value)
  if (success) {
    toast.add({ severity: 'success', summary: 'Account Created', detail: 'Welcome to RAG Platform!', life: 3000 })
    router.push('/dashboard')
  } else {
    toast.add({ severity: 'error', summary: 'Registration Failed', detail: authStore.error, life: 4000 })
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-50 px-4 py-12">
    <div class="w-full max-w-md bg-white border border-slate-200 rounded-xl p-8 space-y-6">
      <div class="text-center space-y-2">
        <h1 class="text-2xl font-bold tracking-tight text-slate-900">Create your account</h1>
        <p class="text-xs text-slate-500">Start building custom grounded AI chatbots in minutes</p>
      </div>

      <form @submit.prevent="handleRegister" class="space-y-4">
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

        <div class="space-y-1">
          <label class="block text-xs font-medium text-slate-700">Confirm Password</label>
          <InputText
            v-model="confirmPassword"
            type="password"
            placeholder="••••••••"
            class="w-full text-sm px-3 py-2 border border-slate-200 rounded-md focus:ring-2 focus:ring-indigo-500"
            required
          />
        </div>

        <Button
          type="submit"
          :loading="authStore.loading"
          label="Create Account"
          class="w-full bg-indigo-500 hover:bg-indigo-600 text-white font-medium text-sm py-2 rounded-md transition cursor-pointer"
        />
      </form>

      <div class="text-center text-xs text-slate-500 border-t border-slate-100 pt-4">
        Already have an account?
        <router-link to="/login" class="text-indigo-600 font-semibold hover:underline">
          Sign in
        </router-link>
      </div>
    </div>
  </div>
</template>
