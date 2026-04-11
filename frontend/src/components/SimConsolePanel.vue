<template>
  <div class="console-box">
    <!-- Upload Area -->
    <div class="console-section">
      <div class="console-header">
        <span class="console-label">01 / Reality Seeds</span>
        <span class="console-meta">Supported formats: PDF, MD, TXT</span>
      </div>

      <div
        class="upload-zone"
        :class="{ 'drag-over': isDragOver, 'has-files': files.length > 0 }"
        @dragover.prevent="handleDragOver"
        @dragleave.prevent="handleDragLeave"
        @drop.prevent="handleDrop"
        @click="triggerFileInput"
      >
        <input
          ref="fileInput"
          type="file"
          multiple
          accept=".pdf,.md,.txt"
          @change="handleFileSelect"
          style="display: none"
          :disabled="loading"
        />

        <div v-if="files.length === 0" class="upload-placeholder">
          <div class="upload-icon">↑</div>
          <div class="upload-title">Drop Files to Upload</div>
          <div class="upload-hint">or click to browse the file system</div>
        </div>

        <div v-else class="file-list">
          <div v-for="(file, index) in files" :key="index" class="file-item">
            <span class="file-icon">📄</span>
            <span class="file-name">{{ file.name }}</span>
            <button @click.stop="removeFile(index)" class="remove-btn">×</button>
          </div>
        </div>
      </div>
    </div>

    <!-- URL Input Section -->
    <div class="console-section url-section">
      <div class="console-header">
        <span class="console-label">01b / URL Import</span>
        <span class="console-meta">Paste article or report URL</span>
      </div>
      <div class="url-input-row">
        <input
          v-model="urlInput"
          class="url-input"
          type="url"
          placeholder="https://example.com/article"
          :disabled="loading || urlFetching"
          @keydown.enter.prevent="fetchUrlDoc"
        />
        <button
          class="url-fetch-btn"
          @click="fetchUrlDoc"
          :disabled="!urlInput.trim() || loading || urlFetching"
        >
          <span v-if="urlFetching">...</span>
          <span v-else>Fetch →</span>
        </button>
      </div>
      <div v-if="urlError" class="url-error">{{ urlError }}</div>
      <div v-if="urlDocs.length > 0" class="url-doc-list">
        <div v-for="(doc, index) in urlDocs" :key="index" class="url-doc-item">
          <span class="url-doc-icon">◈</span>
          <div class="url-doc-info">
            <div class="url-doc-title">{{ doc.title }}</div>
            <div class="url-doc-meta">{{ doc.char_count.toLocaleString() }} chars · {{ doc.url }}</div>
          </div>
          <button @click.stop="removeUrlDoc(index)" class="remove-btn">×</button>
        </div>
      </div>
    </div>

    <!-- Divider -->
    <div class="console-divider">
      <span>Input Parameters</span>
    </div>

    <!-- Simulation Prompt -->
    <div class="console-section">
      <div class="console-header">
        <span class="console-label">>_ 02 / Simulation Prompt</span>
      </div>
      <div class="input-wrapper">
        <textarea
          v-model="formData.simulationRequirement"
          class="code-input"
          placeholder="// Enter your simulation or prediction requirements in natural language (e.g., If a university announces the revocation of a disciplinary action against a student, what public opinion trends will emerge?)"
          rows="6"
          :disabled="loading"
        ></textarea>
        <div class="model-badge">Engine: MiroShark-V1.0</div>
      </div>
    </div>

    <!-- Launch Button -->
    <div class="console-section btn-section">
      <button
        class="start-engine-btn"
        @click="startSimulation"
        :disabled="!canSubmit || loading"
      >
        <span v-if="!loading">Launch Simulation</span>
        <span v-else>Initializing...</span>
        <span class="btn-arrow">→</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { fetchUrl } from '../api/graph'

const router = useRouter()

const formData = ref({ simulationRequirement: '' })
const files = ref([])
const urlInput = ref('')
const urlDocs = ref([])   // [{title, url, text, char_count}]
const urlFetching = ref(false)
const urlError = ref('')
const loading = ref(false)
const isDragOver = ref(false)
const fileInput = ref(null)

// Form is submittable when there's a prompt and at least one content source
const canSubmit = computed(() =>
  formData.value.simulationRequirement.trim() !== '' &&
  (files.value.length > 0 || urlDocs.value.length > 0)
)

const triggerFileInput = () => {
  if (!loading.value) fileInput.value?.click()
}

const handleFileSelect = (event) => {
  addFiles(Array.from(event.target.files))
}

const handleDragOver = () => {
  if (!loading.value) isDragOver.value = true
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleDrop = (e) => {
  isDragOver.value = false
  if (loading.value) return
  addFiles(Array.from(e.dataTransfer.files))
}

// Only .pdf, .md, .txt accepted
const addFiles = (newFiles) => {
  const valid = newFiles.filter(f => ['pdf', 'md', 'txt'].includes(f.name.split('.').pop().toLowerCase()))
  files.value.push(...valid)
}

const removeFile = (index) => {
  files.value.splice(index, 1)
}

const fetchUrlDoc = async () => {
  const url = urlInput.value.trim()
  if (!url || urlFetching.value) return
  if (urlDocs.value.some(d => d.url === url)) {
    urlError.value = 'This URL has already been added.'
    return
  }
  urlFetching.value = true
  urlError.value = ''
  try {
    const res = await fetchUrl(url)
    if (res.success) {
      urlDocs.value.push(res.data)
      urlInput.value = ''
    } else {
      urlError.value = res.error || 'Failed to fetch URL.'
    }
  } catch (err) {
    urlError.value = err.message || 'Failed to fetch URL.'
  } finally {
    urlFetching.value = false
  }
}

const removeUrlDoc = (index) => {
  urlDocs.value.splice(index, 1)
}

// Navigate immediately — API calls happen on the Process page
const startSimulation = () => {
  if (!canSubmit.value || loading.value) return
  import('../store/pendingUpload.js').then(({ setPendingUpload }) => {
    setPendingUpload(files.value, formData.value.simulationRequirement, urlDocs.value)
    router.push({ name: 'Process', params: { projectId: 'new' } })
  })
}
</script>

<style scoped>
/* Corner markers on the console box */
.console-box {
  border: var(--border-medium);
  padding: var(--space-xs);
  position: relative;
}

.console-box::before,
.console-box::after {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  pointer-events: none;
}

.console-box::before {
  top: -2px; right: -2px;
  border-top: 3px solid var(--color-orange);
  border-right: 3px solid var(--color-orange);
}

.console-box::after {
  bottom: -2px; left: -2px;
  border-bottom: 3px solid var(--color-green);
  border-left: 3px solid var(--color-green);
}

.console-section { padding: var(--space-md); }
.console-section.btn-section { padding-top: 0; }

.console-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--space-sm);
  font-family: var(--font-mono);
  font-size: 13px;
  color: rgba(10,10,10,0.4);
  letter-spacing: 1px;
}

.console-label { text-transform: uppercase; }
.console-meta { font-size: 11px; }

/* ── Upload Zone ── */
.upload-zone {
  border: 2px dashed rgba(10,10,10,0.12);
  height: 200px;
  overflow-y: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: var(--transition-medium);
  background: var(--color-gray);
}

.upload-zone.has-files { align-items: flex-start; }
.upload-zone:hover { border-color: var(--color-orange); background: var(--background); }
.upload-zone.drag-over { border-color: var(--color-green); background: rgba(67,193,101,0.05); }

.upload-placeholder { text-align: center; }

.upload-icon {
  width: var(--space-lg);
  height: var(--space-lg);
  border: var(--border-medium);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto var(--space-sm);
  color: var(--color-orange);
  font-size: 1.2rem;
}

.upload-title { font-family: var(--font-display); font-size: 18px; margin-bottom: var(--space-xs); }
.upload-hint { font-family: var(--font-mono); font-size: 13px; color: rgba(10,10,10,0.35); }

/* ── File List ── */
.file-list {
  width: 100%;
  padding: var(--space-sm);
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.file-item {
  display: flex;
  align-items: center;
  background: var(--background);
  padding: var(--space-xs) var(--space-sm);
  border: var(--border-light);
  font-family: var(--font-mono);
  font-size: 14px;
}

.file-name { flex: 1; margin: 0 var(--space-sm); }

.remove-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  color: rgba(10,10,10,0.35);
  transition: var(--transition-fast);
}

.remove-btn:hover { color: var(--color-red); }

/* ── Console Divider ── */
.console-divider {
  display: flex;
  align-items: center;
  margin: var(--space-sm) 0;
}

.console-divider::before,
.console-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(10,10,10,0.08);
}

.console-divider span {
  padding: 0 var(--space-sm);
  font-family: var(--font-mono);
  font-size: 11px;
  color: rgba(10,10,10,0.25);
  letter-spacing: 3px;
  text-transform: uppercase;
}

/* ── Text Input ── */
.input-wrapper {
  position: relative;
  border: var(--border-light);
  background: var(--color-gray);
  transition: var(--transition-fast);
}

.input-wrapper:focus-within { border-color: var(--color-orange); }

.code-input {
  width: 100%;
  border: none;
  background: transparent;
  padding: var(--space-md);
  font-family: var(--font-mono);
  font-size: 15px;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  min-height: 150px;
  color: var(--foreground);
}

.code-input::placeholder { color: rgba(10,10,10,0.35); }

.model-badge {
  position: absolute;
  bottom: var(--space-xs);
  right: var(--space-sm);
  font-family: var(--font-mono);
  font-size: 11px;
  color: rgba(10,10,10,0.25);
  letter-spacing: 1px;
}

/* ── Launch Button ── */
.start-engine-btn {
  width: 100%;
  background: var(--color-black);
  color: var(--color-white);
  border: 2px solid var(--color-black);
  padding: 20px var(--space-lg);
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: all 0.15s ease;
  letter-spacing: 3px;
  text-transform: uppercase;
  position: relative;
  overflow: hidden;
}

.start-engine-btn:not(:disabled) { animation: btn-pulse 2s ease-in-out infinite; }
.start-engine-btn:hover:not(:disabled) { background: var(--color-orange); border-color: var(--color-orange); }
.start-engine-btn:active:not(:disabled) { opacity: 0.9; }
.start-engine-btn:disabled { background: var(--color-gray); color: rgba(10,10,10,0.35); cursor: not-allowed; border-color: rgba(10,10,10,0.08); }

@keyframes btn-pulse {
  0%, 100% { border-color: var(--color-black); }
  50% { border-color: var(--color-orange); }
}

/* ── URL Import Section ── */
.url-section { padding-top: 0; }

.url-input-row { display: flex; gap: var(--space-xs); }

.url-input {
  flex: 1;
  border: var(--border-light);
  background: var(--color-gray);
  padding: var(--space-xs) var(--space-sm);
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--foreground);
  outline: none;
  transition: var(--transition-fast);
  min-width: 0;
}

.url-input:focus { border-color: var(--color-orange); background: var(--background); }
.url-input::placeholder { color: rgba(10,10,10,0.3); }
.url-input:disabled { opacity: 0.5; cursor: not-allowed; }

.url-fetch-btn {
  background: var(--color-black);
  color: var(--color-white);
  border: 2px solid var(--color-black);
  padding: var(--space-xs) var(--space-sm);
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 1px;
  cursor: pointer;
  transition: var(--transition-fast);
  white-space: nowrap;
}

.url-fetch-btn:hover:not(:disabled) { background: var(--color-orange); border-color: var(--color-orange); }
.url-fetch-btn:disabled { opacity: 0.35; cursor: not-allowed; }

.url-error { margin-top: var(--space-xs); font-family: var(--font-mono); font-size: 12px; color: var(--color-red); }

.url-doc-list { margin-top: var(--space-xs); display: flex; flex-direction: column; gap: var(--space-xs); }

.url-doc-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-xs);
  background: var(--background);
  padding: var(--space-xs) var(--space-sm);
  border: var(--border-light);
  border-left: 3px solid var(--color-green);
}

.url-doc-icon { color: var(--color-green); font-size: 14px; margin-top: 1px; flex-shrink: 0; }
.url-doc-info { flex: 1; min-width: 0; }

.url-doc-title {
  font-family: var(--font-display);
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.url-doc-meta {
  font-family: var(--font-mono);
  font-size: 11px;
  color: rgba(10,10,10,0.35);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
