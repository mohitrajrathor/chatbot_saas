<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import api from '@/services/api'

import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'
import ProgressBar from 'primevue/progressbar'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'

const route = useRoute()
const router = useRouter()
const toast = useToast()

const chatbotId = route.params.id
const chatbot = ref(null)
const documents = ref([])
const apiKeys = ref([])
const evalRuns = ref([])
const selectedEvalRun = ref(null)

const loading = ref(true)
const savingGeneral = ref(false)
const uploadingDoc = ref(false)
const indexingUrl = ref(false)
const generatingKey = ref(false)
const uploadingEval = ref(false)

const activeTab = ref('general')
const webUrlInput = ref('')

// General Form State
const generalForm = ref({
  name: '',
  instructions: '',
  access_type: 'public',
  allowed_emails: '',
})

// API Key Modal State
const showKeyModal = ref(false)
const generatedKeyName = ref('')
const createdPlaintextKey = ref('')

// Polling Timer Reference
let pollTimer = null

// Storage calculation (10 MB limit = 10485760 bytes)
const totalStorageBytes = computed(() => {
  return documents.value.reduce((acc, doc) => acc + (doc.size_bytes || 0), 0)
})

const storagePercentage = computed(() => {
  const bytes = totalStorageBytes.value
  return Math.min(100, Math.round((bytes / 10485760) * 100))
})

const formattedStorageUsed = computed(() => {
  const mb = totalStorageBytes.value / (1024 * 1024)
  return `${mb.toFixed(2)} MB / 10 MB`
})

async function loadChatbotData() {
  try {
    const cbRes = await api.get(`/chatbots/${chatbotId}`)
    chatbot.value = cbRes.data
    generalForm.value = {
      name: cbRes.data.name,
      instructions: cbRes.data.instructions || '',
      access_type: cbRes.data.access_type || 'public',
      allowed_emails: cbRes.data.allowed_emails ? cbRes.data.allowed_emails.join(', ') : '',
    }
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load chatbot details.', life: 3000 })
  }
}

async function loadDocuments() {
  try {
    const res = await api.get(`/chatbots/${chatbotId}/documents`)
    documents.value = res.data
  } catch (err) {
    // Silent catch during polling
  }
}

async function loadApiKeys() {
  try {
    const res = await api.get(`/chatbots/${chatbotId}/keys`)
    apiKeys.value = res.data
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load API keys.', life: 3000 })
  }
}

async function loadEvalRuns() {
  try {
    const res = await api.get(`/chatbots/${chatbotId}/eval`)
    evalRuns.value = res.data
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load eval runs.', life: 3000 })
  }
}

async function handleSaveGeneral() {
  savingGeneral.value = true
  try {
    const allowedList = generalForm.value.allowed_emails
      ? generalForm.value.allowed_emails.split(',').map((e) => e.trim()).filter(Boolean)
      : []

    await api.put(`/chatbots/${chatbotId}`, {
      name: generalForm.value.name,
      instructions: generalForm.value.instructions,
      access_type: generalForm.value.access_type,
      allowed_emails: allowedList,
    })
    toast.add({ severity: 'success', summary: 'Updated', detail: 'Chatbot settings saved.', life: 3000 })
    await loadChatbotData()
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Save Failed', detail: err.response?.data?.detail || 'Failed to update.', life: 3000 })
  } finally {
    savingGeneral.value = false
  }
}

async function handleDeleteChatbot() {
  if (!confirm('Are you sure you want to delete this chatbot? This action cannot be undone.')) return
  try {
    await api.delete(`/chatbots/${chatbotId}`)
    toast.add({ severity: 'success', summary: 'Deleted', detail: 'Chatbot deleted.', life: 3000 })
    router.push('/dashboard')
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Delete Failed', detail: 'Failed to delete chatbot.', life: 3000 })
  }
}

// Document Actions
async function handleFileUpload(event) {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  uploadingDoc.value = true
  try {
    await api.post(`/chatbots/${chatbotId}/documents/file`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    toast.add({ severity: 'success', summary: 'Uploaded', detail: 'Document processing queued.', life: 3000 })
    await loadDocuments()
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Upload Failed', detail: err.response?.data?.detail || 'Failed to upload.', life: 4000 })
  } finally {
    uploadingDoc.value = false
    event.target.value = ''
  }
}

async function handleUrlUpload() {
  if (!webUrlInput.value) return
  indexingUrl.value = true
  try {
    await api.post(`/chatbots/${chatbotId}/documents/url`, { url: webUrlInput.value })
    toast.add({ severity: 'success', summary: 'URL Submitted', detail: 'Web indexing queued.', life: 3000 })
    webUrlInput.value = ''
    await loadDocuments()
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Indexing Failed', detail: err.response?.data?.detail || 'Failed to index URL.', life: 4000 })
  } finally {
    indexingUrl.value = false
  }
}

async function handleDeleteDocument(docId) {
  try {
    await api.delete(`/chatbots/${chatbotId}/documents/${docId}`)
    toast.add({ severity: 'success', summary: 'Deleted', detail: 'Document deleted and storage reclaimed.', life: 3000 })
    await loadDocuments()
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Delete Failed', detail: 'Failed to delete document.', life: 3000 })
  }
}

// API Key Actions
async function handleGenerateKey() {
  if (!generatedKeyName.value) {
    toast.add({ severity: 'warn', summary: 'Missing Name', detail: 'API Key name required.', life: 3000 })
    return
  }
  generatingKey.value = true
  try {
    const res = await api.post(`/chatbots/${chatbotId}/keys`, { key_name: generatedKeyName.value })
    createdPlaintextKey.value = res.data.api_key
    toast.add({ severity: 'success', summary: 'Key Generated', detail: 'API Key created successfully.', life: 3000 })
    generatedKeyName.value = ''
    await loadApiKeys()
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Failed', detail: 'Failed to generate key.', life: 3000 })
  } finally {
    generatingKey.value = false
  }
}

async function handleRevokeKey(keyId) {
  try {
    await api.delete(`/chatbots/${chatbotId}/keys/${keyId}`)
    toast.add({ severity: 'success', summary: 'Revoked', detail: 'API key revoked.', life: 3000 })
    await loadApiKeys()
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Revoke Failed', detail: 'Failed to revoke key.', life: 3000 })
  }
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text)
  toast.add({ severity: 'info', summary: 'Copied', detail: 'API key copied to clipboard!', life: 2000 })
}

// Evaluation Actions
async function handleEvalUpload(event) {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  uploadingEval.value = true
  try {
    await api.post(`/chatbots/${chatbotId}/eval`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    toast.add({ severity: 'success', summary: 'Eval Dispatched', detail: 'Evaluation queued.', life: 3000 })
    await loadEvalRuns()
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Eval Failed', detail: err.response?.data?.detail || 'Failed to start evaluation.', life: 4000 })
  } finally {
    uploadingEval.value = false
    event.target.value = ''
  }
}

async function handleViewEvalRun(runId) {
  try {
    const res = await api.get(`/chatbots/${chatbotId}/eval/${runId}`)
    selectedEvalRun.value = res.data
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load evaluation details.', life: 3000 })
  }
}

// Helper formatting functions
function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function formatDate(dtStr) {
  if (!dtStr) return 'Never'
  return new Date(dtStr).toLocaleString()
}

onMounted(async () => {
  loading.value = true
  await Promise.all([loadChatbotData(), loadDocuments(), loadApiKeys(), loadEvalRuns()])
  loading.value = false

  // Polling loop for active document processing
  pollTimer = setInterval(() => {
    const hasPendingOrProcessing = documents.value.some(
      (d) => d.status === 'pending' || d.status === 'processing'
    )
    const hasEvalPending = evalRuns.value.some(
      (e) => e.status === 'pending' || e.status === 'running'
    )
    if (hasPendingOrProcessing) loadDocuments()
    if (hasEvalPending) loadEvalRuns()
  }, 4000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <!-- Header -->
    <header class="bg-white border-b border-slate-200 px-8 py-4">
      <div class="max-w-5xl mx-auto flex items-center justify-between">
        <div class="flex items-center gap-4">
          <router-link to="/dashboard" class="text-slate-500 hover:text-slate-900 text-xs font-medium flex items-center gap-1">
            <i class="pi pi-arrow-left text-xs"></i> Back
          </router-link>
          <span class="text-slate-300">|</span>
          <h1 class="text-lg font-semibold text-slate-900 truncate">{{ chatbot?.name || 'Chatbot Settings' }}</h1>
        </div>

        <div v-if="chatbot" class="flex items-center gap-2">
          <router-link
            :to="`/chat/${chatbot.id}`"
            target="_blank"
            class="px-3 py-1.5 bg-indigo-50 text-indigo-600 hover:bg-indigo-100 text-xs font-medium rounded-md transition flex items-center gap-1.5"
          >
            Test Chat <i class="pi pi-external-link text-[10px]"></i>
          </router-link>
        </div>
      </div>
    </header>

    <!-- Main Settings Area -->
    <main class="max-w-5xl mx-auto p-8 space-y-6">
      <div v-if="loading" class="bg-white border border-slate-200 rounded-lg p-8 animate-pulse space-y-4">
        <div class="h-6 bg-slate-200 rounded w-1/4"></div>
        <div class="h-4 bg-slate-100 rounded w-3/4"></div>
      </div>

      <div v-else-if="chatbot" class="bg-white border border-slate-200 rounded-lg overflow-hidden">
        <Tabs value="general">
          <TabList class="border-b border-slate-200 bg-slate-50 px-4">
            <Tab value="general" class="px-4 py-3 text-xs font-medium cursor-pointer">General</Tab>
            <Tab value="documents" class="px-4 py-3 text-xs font-medium cursor-pointer">Documents</Tab>
            <Tab value="keys" class="px-4 py-3 text-xs font-medium cursor-pointer">API Keys</Tab>
            <Tab value="eval" class="px-4 py-3 text-xs font-medium cursor-pointer">Evaluation</Tab>
          </TabList>

          <TabPanels class="p-6">
            <!-- GENERAL TAB -->
            <TabPanel value="general">
              <form @submit.prevent="handleSaveGeneral" class="space-y-5 max-w-xl">
                <div class="space-y-1">
                  <label class="block text-xs font-medium text-slate-700">Chatbot Name</label>
                  <InputText
                    v-model="generalForm.name"
                    class="w-full text-sm px-3 py-2 border border-slate-200 rounded-md focus:ring-2 focus:ring-indigo-500"
                    required
                  />
                </div>

                <div class="space-y-1">
                  <label class="block text-xs font-medium text-slate-700">System Instructions (Prompt)</label>
                  <Textarea
                    v-model="generalForm.instructions"
                    rows="4"
                    class="w-full text-sm px-3 py-2 border border-slate-200 rounded-md focus:ring-2 focus:ring-indigo-500 resize-none"
                  />
                  <p class="text-[11px] text-slate-400">Controls the persona, scope, and response format of the chatbot.</p>
                </div>

                <div class="space-y-1">
                  <label class="block text-xs font-medium text-slate-700">Access Type</label>
                  <select
                    v-model="generalForm.access_type"
                    class="w-full text-sm px-3 py-2 border border-slate-200 rounded-md bg-white focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="public">Public</option>
                    <option value="restricted">Restricted</option>
                  </select>
                </div>

                <div v-if="generalForm.access_type === 'restricted'" class="space-y-1">
                  <label class="block text-xs font-medium text-slate-700">Allowed Emails (Comma-separated)</label>
                  <InputText
                    v-model="generalForm.allowed_emails"
                    placeholder="user1@example.com, user2@example.com"
                    class="w-full text-sm px-3 py-2 border border-slate-200 rounded-md focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div class="pt-2 flex items-center justify-between border-t border-slate-100">
                  <Button
                    type="submit"
                    :loading="savingGeneral"
                    label="Save Changes"
                    class="bg-indigo-500 hover:bg-indigo-600 text-white text-xs font-medium px-4 py-2 rounded-md cursor-pointer"
                  />
                  <button
                    type="button"
                    @click="handleDeleteChatbot"
                    class="text-xs font-medium text-red-500 hover:text-red-700 px-3 py-1.5 rounded border border-red-200 hover:bg-red-50 cursor-pointer"
                  >
                    Delete Chatbot
                  </button>
                </div>
              </form>
            </TabPanel>

            <!-- DOCUMENTS TAB -->
            <TabPanel value="documents">
              <div class="space-y-6">
                <!-- Storage Quota Bar -->
                <div class="space-y-1 bg-slate-50 p-4 rounded-lg border border-slate-200">
                  <div class="flex justify-between text-xs font-medium">
                    <span class="text-slate-700">Storage Consumption</span>
                    <span class="text-slate-500">{{ formattedStorageUsed }}</span>
                  </div>
                  <ProgressBar :value="storagePercentage" :showValue="false" class="h-2 rounded-full" />
                </div>

                <!-- Upload Section -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <!-- File Upload Zone -->
                  <div class="border-2 border-dashed border-slate-200 rounded-lg p-6 text-center hover:border-indigo-300 hover:bg-indigo-50/50 transition">
                    <i class="pi pi-cloud-upload text-2xl text-slate-400 mb-2"></i>
                    <p class="text-xs font-medium text-slate-700">Upload Knowledge Documents</p>
                    <p class="text-[11px] text-slate-400 mb-3">Supports PDF, DOCX, TXT (Max 10 MB per user)</p>
                    <label class="inline-block px-3 py-1.5 bg-indigo-500 text-white text-xs font-medium rounded-md hover:bg-indigo-600 cursor-pointer transition">
                      <span>{{ uploadingDoc ? 'Processing...' : 'Browse File' }}</span>
                      <input type="file" accept=".pdf,.docx,.txt" @change="handleFileUpload" class="hidden" :disabled="uploadingDoc" />
                    </label>
                  </div>

                  <!-- Web URL Ingestion -->
                  <div class="border border-slate-200 rounded-lg p-6 space-y-3 bg-white">
                    <div class="space-y-1">
                      <p class="text-xs font-medium text-slate-700">Index Web Page URL</p>
                      <p class="text-[11px] text-slate-400">Scrapes and vectorizes text content from a web page</p>
                    </div>
                    <div class="flex gap-2">
                      <InputText
                        v-model="webUrlInput"
                        placeholder="https://docs.example.com/page"
                        class="flex-1 text-xs px-3 py-2 border border-slate-200 rounded-md focus:ring-2 focus:ring-indigo-500"
                      />
                      <Button
                        @click="handleUrlUpload"
                        :loading="indexingUrl"
                        label="Index URL"
                        class="bg-indigo-500 hover:bg-indigo-600 text-white text-xs font-medium px-3 py-1.5 rounded-md cursor-pointer"
                      />
                    </div>
                  </div>
                </div>

                <!-- Document List Table -->
                <div class="space-y-2">
                  <h3 class="text-xs font-semibold text-slate-900 uppercase tracking-wide">Uploaded Documents</h3>
                  <DataTable :value="documents" class="border border-slate-200 rounded-lg text-xs" responsiveLayout="scroll">
                    <Column field="filename" header="Name">
                      <template #body="{ data }">
                        <span class="font-medium text-slate-900">{{ data.filename || data.source_url }}</span>
                      </template>
                    </Column>
                    <Column field="file_type" header="Type">
                      <template #body="{ data }">
                        <Tag :value="data.file_type" severity="secondary" class="uppercase text-[10px]" />
                      </template>
                    </Column>
                    <Column field="size_bytes" header="Size">
                      <template #body="{ data }">
                        <span>{{ formatBytes(data.size_bytes) }}</span>
                      </template>
                    </Column>
                    <Column field="status" header="Status">
                      <template #body="{ data }">
                        <Tag
                          :value="data.status"
                          :severity="data.status === 'ready' ? 'success' : data.status === 'failed' ? 'danger' : 'warn'"
                          class="capitalize text-[10px]"
                        />
                      </template>
                    </Column>
                    <Column header="Actions">
                      <template #body="{ data }">
                        <button
                          @click="handleDeleteDocument(data.id)"
                          class="text-red-500 hover:text-red-700 text-xs font-medium cursor-pointer"
                        >
                          Delete
                        </button>
                      </template>
                    </Column>
                  </DataTable>
                </div>
              </div>
            </TabPanel>

            <!-- API KEYS TAB -->
            <TabPanel value="keys">
              <div class="space-y-6">
                <!-- Create Key Form -->
                <div class="flex items-center gap-3 bg-slate-50 p-4 rounded-lg border border-slate-200">
                  <InputText
                    v-model="generatedKeyName"
                    placeholder="Key Name (e.g. Production Mobile App)"
                    class="flex-1 text-xs px-3 py-2 border border-slate-200 rounded-md focus:ring-2 focus:ring-indigo-500"
                  />
                  <Button
                    @click="handleGenerateKey"
                    :loading="generatingKey"
                    label="Generate Key"
                    icon="pi pi-key"
                    class="bg-indigo-500 hover:bg-indigo-600 text-white text-xs font-medium px-4 py-2 rounded-md cursor-pointer"
                  />
                </div>

                <!-- API Keys Table -->
                <DataTable :value="apiKeys" class="border border-slate-200 rounded-lg text-xs" responsiveLayout="scroll">
                  <Column field="key_name" header="Name">
                    <template #body="{ data }">
                      <span class="font-medium text-slate-900">{{ data.key_name }}</span>
                    </template>
                  </Column>
                  <Column field="created_at" header="Created">
                    <template #body="{ data }">
                      <span>{{ formatDate(data.created_at) }}</span>
                    </template>
                  </Column>
                  <Column field="last_used_at" header="Last Used">
                    <template #body="{ data }">
                      <span>{{ formatDate(data.last_used_at) }}</span>
                    </template>
                  </Column>
                  <Column field="is_active" header="Status">
                    <template #body="{ data }">
                      <Tag :value="data.is_active ? 'Active' : 'Revoked'" :severity="data.is_active ? 'success' : 'danger'" class="text-[10px]" />
                    </template>
                  </Column>
                  <Column header="Actions">
                    <template #body="{ data }">
                      <button
                        v-if="data.is_active"
                        @click="handleRevokeKey(data.id)"
                        class="text-red-500 hover:text-red-700 font-medium cursor-pointer"
                      >
                        Revoke
                      </button>
                    </template>
                  </Column>
                </DataTable>
              </div>
            </TabPanel>

            <!-- EVALUATION TAB -->
            <TabPanel value="eval">
              <div class="space-y-6">
                <!-- Evaluation Dispatch -->
                <div class="bg-slate-50 p-4 rounded-lg border border-slate-200 space-y-3">
                  <div>
                    <h3 class="text-xs font-semibold text-slate-900">Run RAG Evaluation Benchmark</h3>
                    <p class="text-[11px] text-slate-500">Upload a CSV file containing <code class="bg-slate-200 px-1 py-0.5 rounded">question</code> and <code class="bg-slate-200 px-1 py-0.5 rounded">ground_truth</code> columns.</p>
                  </div>
                  <label class="inline-block px-4 py-2 bg-indigo-500 text-white text-xs font-medium rounded-md hover:bg-indigo-600 cursor-pointer transition">
                    <span>{{ uploadingEval ? 'Dispatching...' : 'Upload Test Set CSV' }}</span>
                    <input type="file" accept=".csv" @change="handleEvalUpload" class="hidden" :disabled="uploadingEval" />
                  </label>
                </div>

                <!-- Past Runs List -->
                <div class="space-y-2">
                  <h3 class="text-xs font-semibold text-slate-900 uppercase tracking-wide">Evaluation Runs</h3>
                  <DataTable :value="evalRuns" class="border border-slate-200 rounded-lg text-xs" responsiveLayout="scroll">
                    <Column field="id" header="Run ID">
                      <template #body="{ data }">
                        <span class="font-mono text-[11px] text-slate-600">{{ String(data.id).slice(0, 8) }}...</span>
                      </template>
                    </Column>
                    <Column field="status" header="Status">
                      <template #body="{ data }">
                        <Tag
                          :value="data.status"
                          :severity="data.status === 'complete' ? 'success' : data.status === 'failed' ? 'danger' : 'warn'"
                          class="capitalize text-[10px]"
                        />
                      </template>
                    </Column>
                    <Column field="created_at" header="Date">
                      <template #body="{ data }">
                        <span>{{ formatDate(data.created_at) }}</span>
                      </template>
                    </Column>
                    <Column header="Actions">
                      <template #body="{ data }">
                        <button
                          @click="handleViewEvalRun(data.id)"
                          class="text-indigo-600 hover:text-indigo-800 font-medium cursor-pointer"
                        >
                          View Report
                        </button>
                      </template>
                    </Column>
                  </DataTable>
                </div>

                <!-- Selected Run Report View -->
                <div v-if="selectedEvalRun" class="border border-slate-200 rounded-lg p-5 bg-white space-y-4">
                  <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                    <h3 class="text-sm font-semibold text-slate-900">
                      Evaluation Report (Run: <span class="font-mono text-xs">{{ String(selectedEvalRun.id).slice(0, 8) }}</span>)
                    </h3>
                    <button @click="selectedEvalRun = null" class="text-xs text-slate-400 hover:text-slate-600">Close</button>
                  </div>

                  <!-- Metrics Summary Cards -->
                  <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                    <div class="bg-slate-50 border border-slate-200 p-3 rounded-md">
                      <p class="text-[11px] text-slate-500">Faithfulness</p>
                      <p class="text-base font-bold text-slate-900">{{ selectedEvalRun.average_faithfulness ?? 'N/A' }}</p>
                    </div>
                    <div class="bg-slate-50 border border-slate-200 p-3 rounded-md">
                      <p class="text-[11px] text-slate-500">Answer Relevancy</p>
                      <p class="text-base font-bold text-slate-900">{{ selectedEvalRun.average_answer_relevancy ?? 'N/A' }}</p>
                    </div>
                    <div class="bg-slate-50 border border-slate-200 p-3 rounded-md">
                      <p class="text-[11px] text-slate-500">Context Recall</p>
                      <p class="text-base font-bold text-slate-900">{{ selectedEvalRun.average_context_recall ?? 'N/A' }}</p>
                    </div>
                    <div class="bg-slate-50 border border-slate-200 p-3 rounded-md">
                      <p class="text-[11px] text-slate-500">Context Precision</p>
                      <p class="text-base font-bold text-slate-900">{{ selectedEvalRun.average_context_precision ?? 'N/A' }}</p>
                    </div>
                  </div>

                  <!-- Per-Question Score Breakdown -->
                  <DataTable :value="selectedEvalRun.results" class="border border-slate-200 rounded-lg text-xs" responsiveLayout="scroll">
                    <Column field="question" header="Question" />
                    <Column field="ground_truth" header="Ground Truth" />
                    <Column field="generated_answer" header="Generated Answer" />
                    <Column field="faithfulness" header="Faithfulness" />
                    <Column field="answer_relevancy" header="Relevancy" />
                  </DataTable>
                </div>
              </div>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </div>
    </main>

    <!-- Created Plaintext Key Dialog -->
    <Dialog
      v-model:visible="createdPlaintextKey"
      header="API Key Generated"
      :modal="true"
      class="w-full max-w-md"
    >
      <div class="space-y-4 py-2">
        <p class="text-xs text-amber-600 font-medium bg-amber-50 p-3 rounded border border-amber-200">
          ⚠️ Copy this API key now. You will not be able to view it again!
        </p>
        <div class="flex items-center gap-2">
          <InputText
            :value="createdPlaintextKey"
            readonly
            class="flex-1 font-mono text-xs px-3 py-2 border border-slate-200 rounded-md bg-slate-50"
          />
          <Button
            @click="copyToClipboard(createdPlaintextKey)"
            label="Copy"
            icon="pi pi-copy"
            class="bg-indigo-500 hover:bg-indigo-600 text-white text-xs px-3 py-2 rounded-md cursor-pointer"
          />
        </div>
      </div>
    </Dialog>
  </div>
</template>
