---
name: rag-chatbot-saas-frontend-coding
description: Frontend design, architecture, PrimeVue 4 preset rules, Vue 3 Composition API guidelines, and styling standards for the RAG Chatbot SaaS project. Use whenever writing, refactoring, or reviewing Vue 3 components, views, pinia stores, router, or styling.
---

# RAG Chatbot SaaS — Frontend Coding Skill

## Architecture & Technology Stack
- **Framework**: Vue 3 (`<script setup>` Composition API only — Options API is strictly forbidden).
- **UI Kit**: PrimeVue 4 (`@primevue/themes` using `definePreset(Aura, ...)` preset).
- **Styling**: Vanilla CSS + TailwindCSS (Slate neutral palette + Indigo primary accent).
- **State Management**: Pinia (`defineStore` with Composition API setup syntax `ref()`, `computed()`).
- **Routing**: Vue Router 4 (HTML5 history mode `createWebHistory()`, route meta auth guards).
- **HTTP Client**: Axios instance (`src/services/api.js`) with JWT Bearer token interceptor and 401 token refresh flow.

---

## Design System & Aesthetics

### 1. Color Palette (Slate Neutral + Indigo Accent)
- Background: `bg-slate-50` (`#F8FAFC`)
- Surface / Cards: `bg-white` (`#FFFFFF`)
- Surface Alt (Inputs/Bubbles): `bg-slate-100` (`#F1F5F9`)
- Borders & Dividers: `border-slate-200` (`#E2E8F0`)
- Text Primary: `text-slate-900` (`#0F172A`)
- Text Secondary: `text-slate-500` (`#64748B`)
- Primary Accent: `bg-indigo-500` (`#6366F1`) / Hover `bg-indigo-600` (`#4F46E5`) / Light `bg-indigo-50` (`#EEF2FF`)
- Status Green (Ready): `bg-emerald-50 text-emerald-700`
- Status Amber (Processing): `bg-amber-50 text-amber-700`
- Status Red (Failed): `bg-red-50 text-red-700`

### 2. Typography
- Font Family: `Inter`, sans-serif.
- Page Title: `text-xl font-semibold text-slate-900`
- Section Heading: `text-base font-semibold text-slate-900`
- Card Title: `text-sm font-medium text-slate-900`
- Body Text: `text-sm text-slate-700`
- Secondary / Captions: `text-xs text-slate-500`

### 3. Cards & Borders
- **NO Heavy Box Shadows**: Cards use `border border-slate-200 bg-white rounded-lg p-5` with zero drop-shadow.
- Buttons: `rounded-md font-medium text-sm px-4 py-2`
- Inputs: `rounded-md border-slate-200 focus:ring-2 focus:ring-indigo-500`
- Chat Bubbles: `rounded-xl` (User: `bg-indigo-500 text-white rounded-br-sm self-end`, Bot: `bg-slate-100 text-slate-800 rounded-bl-sm self-start`).

---

## PrimeVue 4 Integration Rules
- Configure `definePreset(Aura, ...)` in `main.js`.
- Always prefer PrimeVue 4 components (`Button`, `InputText`, `Textarea`, `DataTable`, `Dialog`, `Toast`, `Tabs`, `TabPanel`, `Tag`, `ProgressBar`, `FileUpload`, `Skeleton`) over writing custom UI elements from scratch.
- Apply Tailwind utility classes only for layout, flexbox, grid, spacing, and specific alignment adjustments.

---

## Component & State Code Guidelines
- **Single-File Component Structure**:
  ```vue
  <script setup>
  import { ref, computed, onMounted } from 'vue'
  import { useAuthStore } from '@/stores/auth'
  // 1. Props & Emits
  // 2. Stores & Reactive state
  // 3. Computed properties
  // 4. Methods / Handlers
  // 5. Lifecycle hooks
  </script>

  <template>
    <!-- Template markup -->
  </template>
  ```
- **Axios Interceptor**: Automatically attach `Authorization: Bearer <access_token>`. On 401 responses, call refresh token endpoint; if refresh fails, clear auth state and redirect to `/login`.

---

## Anti-Patterns to Avoid
- **DO NOT** use Options API (`export default { data(), methods: {} }`).
- **DO NOT** use inline style attributes (`style="..."`).
- **DO NOT** use gradients or heavy drop-shadows on dashboard cards.
- **DO NOT** use icons larger than 20px in header or navigation bars.
- **DO NOT** mutate Pinia store state directly outside store actions or composables.
