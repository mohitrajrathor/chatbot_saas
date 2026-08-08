<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from 'primevue/usetoast'
import api from '@/services/api'

import Button from 'primevue/button'
import Textarea from 'primevue/textarea'

const route = useRoute()
const authStore = useAuthStore()
const toast = useToast()

const chatbotId = route.params.id
const chatbot = ref(null)
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const fetchingChatbot = ref(true)
const restrictedError = ref('')

const messageContainer = ref(null)

async function loadChatbotInfo() {
  fetchingChatbot.value = true
  try {
    const res = await api.get(`/chatbots/${chatbotId}`)
    chatbot.value = res.data
    // Pre-populate welcome message
    messages.value.push({
      sender: 'bot',
      text: `Hello! I am ${chatbot.value.name}. Ask me any question based on my knowledge base.`,
      sources: [],
    })
  } catch (err) {
    if (err.response?.status === 403 || err.response?.status === 401) {
      restrictedError.value = 'This chatbot is restricted to authorized users only.'
    } else {
      restrictedError.value = 'Chatbot not found or inactive.'
    }
  } finally {
    fetchingChatbot.value = false
  }
}

async function scrollToBottom() {
  await nextTick()
  if (messageContainer.value) {
    messageContainer.value.scrollTop = messageContainer.value.scrollHeight
  }
}

async function sendMessage() {
  const query = inputMessage.value.trim()
  if (!query || loading.value) return

  // Append user message
  messages.value.push({
    sender: 'user',
    text: query,
  })
  inputMessage.value = ''
  loading.value = true
  await scrollToBottom()

  try {
    const response = await api.post(`/chat/web/${chatbotId}`, { message: query })
    messages.value.push({
      sender: 'bot',
      text: response.data.answer,
      sources: response.data.sources || [],
      showSources: false,
    })
  } catch (err) {
    const errText = err.response?.data?.detail || 'Sorry, an error occurred while generating a response.'
    messages.value.push({
      sender: 'bot',
      text: errText,
      sources: [],
    })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

function handleKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

function toggleSources(msg) {
  msg.showSources = !msg.showSources
}

onMounted(() => {
  loadChatbotInfo()
})
</script>

<template>
  <div class="h-screen flex flex-col bg-slate-50 font-sans">
    <!-- Standalone Header Bar -->
    <header class="h-14 bg-white border-b border-slate-200 px-5 flex items-center justify-between shrink-0">
      <div class="flex items-center gap-2.5">
        <span class="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse"></span>
        <span class="text-sm font-semibold text-slate-900 truncate">
          {{ chatbot?.name || 'AI Assistant' }}
        </span>
      </div>
      <div class="text-xs text-slate-400 font-medium">
        Powered by <span class="text-indigo-600 font-semibold">RAG Platform</span>
      </div>
    </header>

    <!-- Restricted / Error State -->
    <div v-if="restrictedError" class="flex-1 flex items-center justify-center p-6 text-center">
      <div class="bg-white border border-slate-200 rounded-xl p-8 max-w-md space-y-3">
        <div class="w-12 h-12 bg-red-50 text-red-500 rounded-full flex items-center justify-center mx-auto text-xl">
          <i class="pi pi-lock"></i>
        </div>
        <h2 class="text-sm font-semibold text-slate-900">Access Restricted</h2>
        <p class="text-xs text-slate-500">{{ restrictedError }}</p>
        <router-link
          to="/login"
          class="inline-block px-4 py-2 bg-indigo-500 text-white text-xs font-medium rounded-md hover:bg-indigo-600 transition"
        >
          Sign In to Access
        </router-link>
      </div>
    </div>

    <!-- Active Chat Workspace -->
    <template v-else>
      <!-- Message Thread Area -->
      <main ref="messageContainer" class="flex-1 overflow-y-auto p-4 space-y-4 max-w-3xl w-full mx-auto">
        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="flex flex-col"
          :class="msg.sender === 'user' ? 'items-end' : 'items-start'"
        >
          <!-- User Bubble -->
          <div
            v-if="msg.sender === 'user'"
            class="bg-indigo-500 text-white text-sm px-4 py-2.5 rounded-xl rounded-br-sm max-w-[80%] whitespace-pre-wrap leading-relaxed shadow-xs"
          >
            {{ msg.text }}
          </div>

          <!-- Bot Bubble -->
          <div v-else class="space-y-1.5 max-w-[80%]">
            <div class="bg-white border border-slate-200 text-slate-800 text-sm px-4 py-3 rounded-xl rounded-bl-sm whitespace-pre-wrap leading-relaxed shadow-xs">
              {{ msg.text }}
            </div>

            <!-- Source Attributions -->
            <div v-if="msg.sources && msg.sources.length > 0" class="text-xs">
              <button
                @click="toggleSources(msg)"
                class="text-slate-400 hover:text-slate-600 text-[11px] font-medium flex items-center gap-1 cursor-pointer"
              >
                <i class="pi pi-file text-[10px]"></i>
                Sources ({{ msg.sources.length }})
                <i :class="msg.showSources ? 'pi pi-chevron-up' : 'pi pi-chevron-down'" class="text-[9px]"></i>
              </button>

              <div v-if="msg.showSources" class="mt-1.5 space-y-1">
                <div
                  v-for="(src, sIdx) in msg.sources"
                  :key="sIdx"
                  class="bg-slate-100 border border-slate-200 text-slate-600 text-[11px] p-2 rounded-md"
                >
                  <p class="font-semibold text-slate-800 truncate mb-0.5">📄 {{ typeof src === 'string' ? src : src.source }}</p>
                  <p v-if="src.content" class="text-slate-500 line-clamp-2 text-[10px] italic">"{{ src.content }}"</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Typing Indicator -->
        <div v-if="loading" class="flex justify-start">
          <div class="bg-white border border-slate-200 text-slate-400 text-sm px-4 py-3 rounded-xl rounded-bl-sm flex items-center gap-1.5 animate-pulse">
            <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
            <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
            <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
          </div>
        </div>
      </main>

      <!-- Input Area -->
      <footer class="border-t border-slate-200 bg-white p-4 shrink-0">
        <div class="max-w-3xl mx-auto flex items-end gap-3">
          <Textarea
            v-model="inputMessage"
            @keydown="handleKeydown"
            placeholder="Ask a question..."
            rows="1"
            autoResize
            class="flex-1 border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm max-h-32 overflow-y-auto focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none resize-none"
          />
          <Button
            @click="sendMessage"
            :disabled="!inputMessage.trim() || loading"
            icon="pi pi-send"
            class="bg-indigo-500 hover:bg-indigo-600 text-white p-2.5 rounded-lg disabled:opacity-40 transition cursor-pointer"
          />
        </div>
      </footer>
    </template>
  </div>
</template>
