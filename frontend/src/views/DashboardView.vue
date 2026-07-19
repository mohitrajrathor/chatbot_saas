<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from 'primevue/usetoast'
import api from '@/services/api'

import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'

const router = useRouter()
const authStore = useAuthStore()
const toast = useToast()

const chatbots = ref([])
const loading = ref(true)
const showCreateModal = ref(false)
const creating = ref(false)

const newChatbot = ref({
  name: '',
  instructions: 'You are a helpful AI assistant.',
  access_type: 'public',
  allowed_emails: '',
})

async function fetchChatbots() {
  loading.value = true
  try {
    const res = await api.get('/chatbots')
    chatbots.value = res.data
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load chatbots.', life: 3000 })
  } finally {
    loading.value = false
  }
}

async function handleCreateChatbot() {
  if (!newChatbot.value.name) {
    toast.add({ severity: 'warn', summary: 'Missing Name', detail: 'Chatbot name is required.', life: 3000 })
    return
  }

  creating.value = true
  try {
    const allowedList = newChatbot.value.allowed_emails
      ? newChatbot.value.allowed_emails.split(',').map((e) => e.trim()).filter(Boolean)
      : []

    const payload = {
      name: newChatbot.value.name,
      instructions: newChatbot.value.instructions,
      access_type: newChatbot.value.access_type,
      allowed_emails: allowedList,
    }

    const res = await api.post('/chatbots', payload)
    toast.add({ severity: 'success', summary: 'Success', detail: 'Chatbot created successfully.', life: 3000 })
    showCreateModal.value = false
    newChatbot.value = { name: '', instructions: 'You are a helpful AI assistant.', access_type: 'public', allowed_emails: '' }
    await fetchChatbots()
    router.push(`/dashboard/chatbots/${res.data.id}`)
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Creation Failed', detail: err.response?.data?.detail || 'Failed to create chatbot.', life: 3000 })
  } finally {
    creating.value = false
  }
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  fetchChatbots()
})
</script>

<template>
  <div class="min-h-screen flex bg-slate-50">
    <!-- Sidebar Navigation -->
    <aside class="w-60 bg-white border-r border-slate-200 flex flex-col justify-between h-screen sticky top-0">
      <div>
        <div class="h-14 px-5 flex items-center border-b border-slate-200">
          <span class="font-bold text-slate-900 text-base tracking-tight flex items-center gap-2">
            <span class="w-2.5 h-2.5 bg-indigo-500 rounded-full"></span>
            RAG SaaS
          </span>
        </div>

        <nav class="p-3 space-y-1">
          <router-link
            to="/dashboard"
            class="flex items-center gap-2.5 px-3 py-2 text-sm font-medium text-indigo-600 bg-indigo-50 rounded-md"
          >
            <i class="pi pi-home text-sm"></i>
            My Chatbots
          </router-link>
        </nav>
      </div>

      <div class="p-4 border-t border-slate-200 space-y-3">
        <div class="flex items-center justify-between">
          <div class="truncate">
            <p class="text-xs font-semibold text-slate-900 truncate">{{ authStore.user?.email || 'User' }}</p>
            <p class="text-[11px] text-slate-500">Free Tier</p>
          </div>
        </div>
        <button
          @click="handleLogout"
          class="w-full flex items-center justify-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-600 border border-slate-200 rounded-md hover:bg-slate-50 transition cursor-pointer"
        >
          <i class="pi pi-sign-out text-xs"></i>
          Sign Out
        </button>
      </div>
    </aside>

    <!-- Main Content Area -->
    <main class="flex-1 p-8 max-w-5xl mx-auto space-y-6">
      <!-- Top Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-semibold text-slate-900">My Chatbots</h1>
          <p class="text-xs text-slate-500 mt-0.5">Manage your grounded AI assistants and knowledge bases</p>
        </div>
        <Button
          @click="showCreateModal = true"
          label="New Chatbot"
          icon="pi pi-plus"
          class="bg-indigo-500 hover:bg-indigo-600 text-white text-sm font-medium px-4 py-2 rounded-md transition cursor-pointer"
        />
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="i in 3" :key="i" class="bg-white border border-slate-200 rounded-lg p-5 animate-pulse space-y-3">
          <div class="h-4 bg-slate-200 rounded w-3/4"></div>
          <div class="h-3 bg-slate-100 rounded w-full"></div>
          <div class="h-3 bg-slate-100 rounded w-1/2"></div>
        </div>
      </div>

      <!-- Empty State -->
      <div
        v-else-if="chatbots.length === 0"
        class="bg-white border border-slate-200 rounded-lg p-12 text-center flex flex-col items-center justify-center space-y-3"
      >
        <div class="w-12 h-12 bg-indigo-50 text-indigo-500 rounded-full flex items-center justify-center text-xl">
          <i class="pi pi-comments"></i>
        </div>
        <h3 class="text-sm font-medium text-slate-800">No chatbots created yet</h3>
        <p class="text-xs text-slate-500 max-w-sm">
          Create your first custom AI chatbot to index your documents and start answering questions.
        </p>
        <Button
          @click="showCreateModal = true"
          label="Create Your First Chatbot"
          class="bg-indigo-500 hover:bg-indigo-600 text-white text-xs font-medium px-4 py-2 rounded-md mt-2 cursor-pointer"
        />
      </div>

      <!-- Chatbots Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="bot in chatbots"
          :key="bot.id"
          class="bg-white border border-slate-200 rounded-lg p-5 hover:border-slate-300 transition flex flex-col justify-between space-y-4"
        >
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <h2 class="text-sm font-medium text-slate-900 truncate">{{ bot.name }}</h2>
              <Tag
                :value="bot.access_type"
                :severity="bot.access_type === 'public' ? 'success' : 'info'"
                class="text-[10px] px-2 py-0.5"
              />
            </div>
            <p class="text-xs text-slate-500 line-clamp-2">{{ bot.instructions }}</p>
          </div>

          <div class="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <router-link
              :to="`/chat/${bot.id}`"
              target="_blank"
              class="text-indigo-600 font-medium hover:underline flex items-center gap-1"
            >
              Open Chat <i class="pi pi-external-link text-[10px]"></i>
            </router-link>
            <router-link
              :to="`/dashboard/chatbots/${bot.id}`"
              class="text-slate-600 hover:text-slate-900 font-medium flex items-center gap-1"
            >
              <i class="pi pi-cog text-xs"></i> Settings
            </router-link>
          </div>
        </div>
      </div>
    </main>

    <!-- Create Chatbot Modal -->
    <Dialog
      v-model:visible="showCreateModal"
      header="Create New Chatbot"
      :modal="true"
      class="w-full max-w-lg"
    >
      <form @submit.prevent="handleCreateChatbot" class="space-y-4 py-2">
        <div class="space-y-1">
          <label class="block text-xs font-medium text-slate-700">Chatbot Name</label>
          <InputText
            v-model="newChatbot.name"
            placeholder="e.g. Customer Support Bot"
            class="w-full text-sm px-3 py-2 border border-slate-200 rounded-md focus:ring-2 focus:ring-indigo-500"
            required
          />
        </div>

        <div class="space-y-1">
          <label class="block text-xs font-medium text-slate-700">System Instructions</label>
          <Textarea
            v-model="newChatbot.instructions"
            rows="3"
            placeholder="You are a helpful AI assistant..."
            class="w-full text-sm px-3 py-2 border border-slate-200 rounded-md focus:ring-2 focus:ring-indigo-500 resize-none"
          />
        </div>

        <div class="space-y-1">
          <label class="block text-xs font-medium text-slate-700">Access Control</label>
          <select
            v-model="newChatbot.access_type"
            class="w-full text-sm px-3 py-2 border border-slate-200 rounded-md bg-white focus:ring-2 focus:ring-indigo-500"
          >
            <option value="public">Public (Anyone with link/key can access)</option>
            <option value="restricted">Restricted (Specific emails only)</option>
          </select>
        </div>

        <div v-if="newChatbot.access_type === 'restricted'" class="space-y-1">
          <label class="block text-xs font-medium text-slate-700">Allowed Emails (Comma-separated)</label>
          <InputText
            v-model="newChatbot.allowed_emails"
            placeholder="user1@example.com, user2@example.com"
            class="w-full text-sm px-3 py-2 border border-slate-200 rounded-md focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div class="flex justify-end gap-2 pt-4">
          <Button
            type="button"
            label="Cancel"
            @click="showCreateModal = false"
            class="px-4 py-2 text-xs font-medium text-slate-600 border border-slate-200 rounded-md hover:bg-slate-50 cursor-pointer"
          />
          <Button
            type="submit"
            :loading="creating"
            label="Create Chatbot"
            class="px-4 py-2 text-xs font-medium text-white bg-indigo-500 hover:bg-indigo-600 rounded-md cursor-pointer"
          />
        </div>
      </form>
    </Dialog>
  </div>
</template>
