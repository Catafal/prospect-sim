<template>
  <div class="variant-test-page">
    <header class="vt-header">
      <div class="brand" @click="router.push('/')">PROSPECT-SIM</div>
      <span class="page-tag">Email Variant Test</span>
      <button v-if="results" class="download-btn" @click="downloadResults">↓ Export JSON</button>
      <div v-else></div>
    </header>

    <!-- Setup Form -->
    <div v-if="!results && !loading" class="setup-panel">
      <h2 class="setup-title">Test Cold Email Variants</h2>
      <p class="setup-desc">Run email copy against synthetic B2B decision-maker personas before touching real leads.</p>

      <div class="form-row">
        <label class="form-label">ICP Project</label>
        <select class="form-select" v-model="form.projectId">
          <option value="">Select project…</option>
          <option v-for="p in projects" :key="p.project_id" :value="p.project_id">
            {{ p.name }} — {{ p.status }}
          </option>
        </select>
      </div>

      <div class="form-row">
        <label class="form-label">Simulation Goal (optional)</label>
        <textarea class="form-textarea" v-model="form.simulationRequirement" rows="2"
          placeholder="E.g.: Test timeline vs. problem hook for HR Directors at Spanish scale-ups." />
      </div>

      <div class="form-row form-row-inline">
        <label class="form-label">Run Mode</label>
        <div class="toggle-group">
          <button class="toggle-btn" :class="{ active: !form.parallel }" @click="form.parallel = false">Sequential</button>
          <button class="toggle-btn" :class="{ active: form.parallel }" @click="form.parallel = true">Parallel</button>
        </div>
        <span class="mode-hint">{{ form.parallel ? 'Faster, more LLM calls' : 'Slower, cheaper' }}</span>
      </div>

      <div class="variants-section">
        <div class="variants-header">
          <span class="variants-title">Email Variants</span>
          <button class="add-variant-btn" @click="addVariant" :disabled="form.variants.length >= 6">+ Add Variant</button>
        </div>
        <div v-for="(variant, idx) in form.variants" :key="idx" class="variant-card">
          <div class="variant-card-header">
            <span class="variant-label">Variant {{ String.fromCharCode(65 + idx) }}</span>
            <select class="hook-select" v-model="variant.hook_type">
              <option value="problem">Problem Hook</option>
              <option value="timeline">Timeline Hook</option>
              <option value="numbers">Numbers Hook</option>
              <option value="social_proof">Social Proof Hook</option>
              <option value="curiosity">Curiosity Hook</option>
            </select>
            <button v-if="form.variants.length > 2" class="remove-btn" @click="removeVariant(idx)">✕</button>
          </div>
          <input class="subject-input" v-model="variant.subject_line"
            placeholder="Subject line (max 60 chars)" maxlength="80" />
          <textarea class="body-textarea" v-model="variant.body"
            placeholder="Email body (≤150 words recommended)" rows="5" />
          <div class="word-count" :class="{ warn: wordCount(variant.body) > 150 }">
            {{ wordCount(variant.body) }} words
          </div>
        </div>
      </div>

      <button class="run-btn" :disabled="!canRun" @click="runVariantTest">Run Variant Test</button>
      <div v-if="error" class="vt-error">{{ error }}</div>
    </div>

    <!-- Loading State — shows action feed as soon as simulation starts -->
    <div v-if="loading" class="vt-loading">
      <div v-if="!results" class="loading-spinner-wrap">
        <div class="loading-ring"></div>
        <div class="loading-text">{{ loadingStatus || 'Setting up…' }}</div>
      </div>
      <div v-else class="loading-with-feed">
        <div class="loading-header-row">
          <div class="loading-ring small"></div>
          <span class="loading-status-text">{{ loadingStatus }}</span>
        </div>
        <EmailActionFeed
          v-if="firstSimId"
          :simulationId="firstSimId"
          :active="loading"
        />
      </div>
    </div>

    <!-- Results -->
    <div v-if="results && !loading" class="results-panel">
      <div class="results-header">
        <h2 class="results-title">Variant Test Results</h2>
        <div class="results-meta">
          {{ results.total_variants }} variants · {{ results.run_mode }} · {{ results.num_rounds }} rounds
        </div>
      </div>

      <!-- Simulation status table -->
      <div class="ranking-section">
        <h3 class="section-title">Simulations</h3>
        <table class="ranking-table">
          <thead>
            <tr><th>#</th><th>Variant</th><th>Hook</th><th>Sim ID</th><th>Status</th><th>Progress</th><th></th></tr>
          </thead>
          <tbody>
            <tr v-for="(run, idx) in results.variant_run_ids" :key="run.variant_id"
              :class="{ 'row-winner': idx === 0 && allCompleted }">
              <td class="rank-num">{{ idx + 1 }}</td>
              <td class="variant-name"><span v-if="idx === 0 && allCompleted" class="winner-star">★</span>{{ run.variant_label }}</td>
              <td>{{ getHookType(run.variant_id) }}</td>
              <td class="sim-id-cell">{{ shortId(run.simulation_id) }}</td>
              <td><span class="status-badge" :class="run.status">{{ run.status }}</span></td>
              <td class="progress-cell">{{ run.progress || '—' }}</td>
              <td><button class="view-btn" @click="viewSimulation(run.simulation_id)">View →</button></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Agent personas panel — visible after prepare completes -->
      <div v-if="personas.length > 0" class="personas-section">
        <h3 class="section-title">Test Audience — {{ personas.length }} B2B personas</h3>
        <div class="personas-grid">
          <EmailPersonaCard v-for="p in personas" :key="p.user_id || p.user_name" :profile="p" />
        </div>
      </div>

      <!-- Variant performance — appears as soon as any sim completes -->
      <div v-if="variantResults || variantResultsLoading || variantResultsError" class="perf-section">
        <div class="perf-section-header">
          <h3 class="section-title">Performance Results</h3>
        </div>
        <EmailVariantReport
          :variantResults="variantResults"
          :loading="variantResultsLoading"
          :error="variantResultsError"
        />
      </div>

      <!-- LLM Analysis Report -->
      <div class="report-section">
        <div class="report-section-header">
          <h3 class="section-title">AI Analysis Report</h3>
          <button v-if="!report && !reportLoading" class="generate-report-btn"
            :disabled="!allCompleted"
            :title="allCompleted ? '' : 'Waiting for all simulations to complete…'"
            @click="generateReport">
            {{ allCompleted ? 'Generate Report' : 'Waiting for simulations…' }}
          </button>
        </div>

        <div v-if="reportLoading" class="report-loading">
          <div class="loading-ring small"></div>
          <span class="report-loading-text">{{ reportStatus }}…</span>
          <div class="report-progress-bar"><div class="report-progress-fill" :style="{ width: reportProgress + '%' }"></div></div>
        </div>
        <div v-if="reportError" class="vt-error">{{ reportError }}</div>

        <!-- LLM report narrative sections (outline only, no raw variant table — use EmailVariantReport above) -->
        <div v-if="report && report.outline" class="report-content">
          <div class="report-summary">{{ report.outline.summary }}</div>
          <div v-for="section in report.outline.sections" :key="section.title" class="report-body-section">
            <h4 class="subsection-title">{{ section.title }}</h4>
            <div class="section-body">{{ section.content }}</div>
          </div>
        </div>
      </div>

      <div class="results-actions">
        <button class="restart-btn" @click="resetForm">Run Another Test</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import EmailPersonaCard from '../components/EmailPersonaCard.vue'
import EmailActionFeed from '../components/EmailActionFeed.vue'
import EmailVariantReport from '../components/EmailVariantReport.vue'

export default {
  name: 'VariantTestView',
  components: { EmailPersonaCard, EmailActionFeed, EmailVariantReport },

  setup() {
    const router = useRouter()
    const projects = ref([])
    const loading = ref(false)
    const loadingStatus = ref('')
    const error = ref('')
    const results = ref(null)

    // Agent personas (loaded after prepare)
    const personas = ref([])

    // Structured variant metrics (loaded after sim completes — no LLM required)
    const variantResults = ref(null)
    const variantResultsLoading = ref(false)
    const variantResultsError = ref('')

    // LLM report generation state
    const report = ref(null)
    const reportLoading = ref(false)
    const reportError = ref('')
    const reportStatus = ref('')
    const reportProgress = ref(0)
    let reportPollTimer = null

    const form = ref({
      projectId: '',
      simulationRequirement: '',
      parallel: false,
      variants: [
        { id: 1, label: 'Variant A', hook_type: 'problem',  subject_line: '', body: '' },
        { id: 2, label: 'Variant B', hook_type: 'timeline', subject_line: '', body: '' },
      ],
    })

    const canRun = computed(() =>
      !!form.value.projectId &&
      form.value.variants.every((v) => v.subject_line.trim() && v.body.trim())
    )

    // First simulation ID — used for live feed and variant-results lookup
    const firstSimId = computed(() => results.value?.variant_run_ids?.[0]?.simulation_id || '')

    const allCompleted = computed(() => {
      const runs = results.value?.variant_run_ids
      return runs?.length > 0 && runs.every((r) => r.status === 'completed')
    })

    function wordCount(text) {
      return text.trim().split(/\s+/).filter(Boolean).length
    }

    function addVariant() {
      const next = form.value.variants.length + 1
      form.value.variants.push({ id: next, label: `Variant ${String.fromCharCode(64 + next)}`, hook_type: 'curiosity', subject_line: '', body: '' })
    }

    function removeVariant(idx) {
      form.value.variants.splice(idx, 1)
      form.value.variants.forEach((v, i) => { v.id = i + 1; v.label = `Variant ${String.fromCharCode(65 + i)}` })
    }

    function getHookType(variantId) {
      return form.value.variants.find((x) => x.id === variantId)?.hook_type || '—'
    }

    function shortId(id) { return id ? id.slice(-8) : '—' }

    async function loadProjects() {
      try {
        const data = await fetch('/api/simulation/projects').then((r) => r.json())
        if (data.success) projects.value = data.projects || []
      } catch (e) { console.warn('Could not load projects:', e) }
    }

    /** Fetch agent personas for this simulation (called after prepare completes). */
    async function fetchPersonas(simId) {
      try {
        const data = await fetch(
          `/api/simulation/${simId}/profiles/realtime?platform=email_inbox`
        ).then((r) => r.json())
        if (data.success && data.data?.profiles?.length) {
          personas.value = data.data.profiles
        }
      } catch (e) { console.warn('Could not load personas:', e) }
    }

    /** Fetch structured variant metrics from SQLite (called when any sim completes). */
    async function fetchVariantResults(simId) {
      if (variantResults.value) return   // Already loaded
      variantResultsLoading.value = true
      variantResultsError.value = ''
      try {
        const data = await fetch(`/api/simulation/${simId}/variant-results`).then((r) => r.json())
        if (!data.success) throw new Error(data.error || 'Failed to load results')
        variantResults.value = data.data   // May be null if no DB data yet
      } catch (e) {
        variantResultsError.value = e.message
      } finally {
        variantResultsLoading.value = false
      }
    }

    async function runVariantTest() {
      if (!canRun.value) return
      loading.value = true
      error.value = ''
      results.value = null
      personas.value = []
      variantResults.value = null
      loadingStatus.value = 'Creating simulations…'

      try {
        const resp = await fetch('/api/simulation/run-variant-test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            project_id: form.value.projectId,
            variants: form.value.variants,
            simulation_requirement: form.value.simulationRequirement,
            parallel: form.value.parallel,
            num_rounds: 8,
          }),
        })
        const data = await resp.json()
        if (!data.success) throw new Error(data.error || 'Variant test failed')

        results.value = data
        loadingStatus.value = 'Preparing agent profiles…'

        const variantRuns = data.variant_run_ids || []
        await Promise.all(variantRuns.map((run) => orchestrateSim(run, data.num_rounds)))

        results.value = { ...results.value }
        loadingStatus.value = 'All simulations complete'
      } catch (e) {
        error.value = e.message || 'Unexpected error'
      } finally {
        loading.value = false
      }
    }

    /** Orchestrate one simulation: prepare → start → run → fetch results. */
    async function orchestrateSim(run, numRounds) {
      const { simulation_id, prepare_task_id } = run
      if (!simulation_id) return

      function setRunStatus(status) {
        if (!results.value) return
        const idx = results.value.variant_run_ids.findIndex((r) => r.simulation_id === simulation_id)
        if (idx !== -1) results.value.variant_run_ids[idx].status = status
      }

      // Poll prepare
      if (prepare_task_id) {
        setRunStatus('preparing')
        await pollUntilDone(
          () => fetch('/api/simulation/prepare/status', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_id: prepare_task_id }),
          }).then((r) => r.json()),
          (d) => d?.data?.status === 'completed',
          (d) => d?.data?.status === 'failed',
          3000,
        )
        // Load personas as soon as profiles are ready
        fetchPersonas(simulation_id)
      }

      // Start simulation
      setRunStatus('starting')
      loadingStatus.value = 'Running agents…'
      const startData = await fetch('/api/simulation/start', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ simulation_id, platform: 'email_inbox', max_rounds: numRounds || 8 }),
      }).then((r) => r.json())

      if (!startData.success) {
        setRunStatus('failed')
        return
      }

      // Poll run status
      setRunStatus('running')
      await pollUntilDone(
        () => fetch(`/api/simulation/${simulation_id}/run-status`).then((r) => r.json()),
        (d) => ['completed', 'stopped'].includes(d?.data?.runner_status),
        (d) => d?.data?.runner_status === 'failed',
        4000,
        (d) => {
          const current = d?.data?.current_round ?? 0
          const total = d?.data?.total_rounds ?? '?'
          const idx = results.value?.variant_run_ids?.findIndex((r) => r.simulation_id === simulation_id)
          if (idx !== -1 && results.value) {
            results.value.variant_run_ids[idx].progress = `round ${current}/${total}`
          }
        },
      )
      setRunStatus('completed')

      // Fetch structured metrics immediately — no LLM report needed
      fetchVariantResults(simulation_id)
    }

    /** Generic polling helper — resolves when isDone or isFailed fires. */
    async function pollUntilDone(fetchFn, isDone, isFailed, intervalMs = 3000, onTick = null) {
      while (true) {
        await new Promise((resolve) => setTimeout(resolve, intervalMs))
        try {
          const result = await fetchFn()
          if (onTick) onTick(result)
          if (isDone(result)) return
          if (isFailed(result)) return
        } catch (_) { /* non-fatal, keep polling */ }
      }
    }

    function viewSimulation(simulationId) { router.push(`/simulation/${simulationId}`) }

    function downloadResults() {
      if (!results.value) return
      const blob = new Blob([JSON.stringify(results.value, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = `variant-test-${Date.now()}.json`; a.click()
      URL.revokeObjectURL(url)
    }

    function resetForm() {
      results.value = null; error.value = ''
      personas.value = []; variantResults.value = null
      variantResultsError.value = ''; variantResultsLoading.value = false
      report.value = null; reportError.value = ''; reportLoading.value = false
      if (reportPollTimer) { clearInterval(reportPollTimer); reportPollTimer = null }
    }

    async function generateReport() {
      if (!results.value?.variant_run_ids?.length) return
      reportLoading.value = true; reportError.value = ''
      reportStatus.value = 'Requesting report generation'; reportProgress.value = 5

      const simId = results.value.variant_run_ids[0].simulation_id
      try {
        const data = await fetch('/api/report/generate', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ simulation_id: simId }),
        }).then((r) => r.json())
        if (!data.success) throw new Error(data.error || 'Report generation failed')

        const { report_id, task_id, already_generated } = data.data
        if (already_generated) { await fetchReport(report_id); return }
        pollReport(task_id, report_id)
      } catch (e) {
        reportError.value = e.message || 'Unexpected error'; reportLoading.value = false
      }
    }

    function pollReport(taskId, reportId) {
      reportPollTimer = setInterval(async () => {
        try {
          const data = await fetch('/api/report/generate/status', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_id: taskId }),
          }).then((r) => r.json())
          if (!data.success) return
          reportStatus.value = data.data.message || data.data.status
          reportProgress.value = data.data.progress || 0
          if (data.data.status === 'completed') { clearInterval(reportPollTimer); await fetchReport(reportId) }
          else if (data.data.status === 'failed') { clearInterval(reportPollTimer); reportError.value = data.data.message || 'Failed'; reportLoading.value = false }
        } catch (_) { /* keep polling */ }
      }, 3000)
    }

    async function fetchReport(reportId) {
      try {
        const data = await fetch(`/api/report/${reportId}`).then((r) => r.json())
        if (!data.success) throw new Error(data.error || 'Failed to fetch report')
        report.value = data.data
      } catch (e) { reportError.value = e.message } finally { reportLoading.value = false }
    }

    onUnmounted(() => { if (reportPollTimer) clearInterval(reportPollTimer) })
    onMounted(() => { loadProjects() })

    return {
      router, projects, loading, loadingStatus, error, results,
      personas, variantResults, variantResultsLoading, variantResultsError,
      form, canRun, firstSimId, allCompleted,
      wordCount, addVariant, removeVariant, getHookType, shortId,
      runVariantTest, viewSimulation, downloadResults, resetForm,
      report, reportLoading, reportError, reportStatus, reportProgress, generateReport,
    }
  },
}
</script>

<style scoped>
.variant-test-page {
  min-height: 100vh;
  background: #0a0a0f;
  color: #e4e4e9;
  font-family: 'Inter', 'SF Pro', system-ui, sans-serif;
}

.vt-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  height: 56px;
  border-bottom: 1px solid #1e1e2e;
  background: #0d0d14;
}

.brand { font-size: 13px; font-weight: 700; letter-spacing: 0.12em; cursor: pointer; color: #a78bfa; }
.page-tag { font-size: 11px; background: #1e1e2e; color: #a78bfa; padding: 3px 10px; border-radius: 4px; letter-spacing: 0.08em; text-transform: uppercase; }
.download-btn { background: #1e1e2e; border: 1px solid #2e2e42; color: #a0a0b4; padding: 6px 14px; border-radius: 4px; cursor: pointer; font-size: 12px; }

/* Setup panel */
.setup-panel { max-width: 800px; margin: 40px auto; padding: 0 24px; }
.setup-title { font-size: 22px; font-weight: 600; margin-bottom: 8px; }
.setup-desc { color: #6b6b82; font-size: 14px; margin-bottom: 32px; }
.form-row { margin-bottom: 20px; }
.form-row-inline { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.form-label { display: block; font-size: 12px; color: #6b6b82; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }
.form-select, .form-textarea { width: 100%; background: #111118; border: 1px solid #1e1e2e; color: #e4e4e9; padding: 10px 12px; border-radius: 6px; font-size: 14px; resize: vertical; }
.toggle-group { display: flex; gap: 4px; }
.toggle-btn { background: #111118; border: 1px solid #1e1e2e; color: #6b6b82; padding: 6px 14px; border-radius: 4px; cursor: pointer; font-size: 12px; }
.toggle-btn.active { background: #1e1e36; border-color: #a78bfa; color: #a78bfa; }
.mode-hint { font-size: 12px; color: #4b4b60; }

/* Variants */
.variants-section { margin-bottom: 28px; }
.variants-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.variants-title { font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #8b8ba0; }
.add-variant-btn { background: transparent; border: 1px dashed #2e2e42; color: #6b6b82; padding: 5px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; }
.add-variant-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.variant-card { background: #0d0d14; border: 1px solid #1e1e2e; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
.variant-card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.variant-label { font-size: 13px; font-weight: 600; color: #a78bfa; min-width: 80px; }
.hook-select { background: #111118; border: 1px solid #1e1e2e; color: #a0a0b4; padding: 4px 8px; border-radius: 4px; font-size: 12px; flex: 1; }
.remove-btn { background: transparent; border: none; color: #4b4b60; cursor: pointer; font-size: 14px; padding: 4px; margin-left: auto; }
.subject-input { width: 100%; background: #111118; border: 1px solid #1e1e2e; color: #e4e4e9; padding: 8px 12px; border-radius: 4px; font-size: 14px; margin-bottom: 8px; box-sizing: border-box; }
.body-textarea { width: 100%; background: #111118; border: 1px solid #1e1e2e; color: #e4e4e9; padding: 8px 12px; border-radius: 4px; font-size: 13px; line-height: 1.6; resize: vertical; box-sizing: border-box; }
.word-count { font-size: 11px; color: #4b4b60; text-align: right; margin-top: 4px; }
.word-count.warn { color: #f59e0b; }
.run-btn { width: 100%; background: #a78bfa; color: #0a0a0f; border: none; padding: 14px; border-radius: 6px; font-size: 15px; font-weight: 600; cursor: pointer; letter-spacing: 0.04em; }
.run-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.vt-error { margin-top: 12px; color: #f87171; font-size: 13px; padding: 10px; background: #1a0a0a; border-radius: 4px; }

/* Loading */
.vt-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 60vh; gap: 16px; }
.loading-spinner-wrap { display: flex; flex-direction: column; align-items: center; gap: 16px; }
.loading-with-feed { width: 100%; max-width: 720px; padding: 32px 24px; display: flex; flex-direction: column; gap: 16px; }
.loading-header-row { display: flex; align-items: center; gap: 10px; }
.loading-status-text { font-size: 13px; color: #6b6b82; }
.loading-ring { width: 40px; height: 40px; border: 3px solid #1e1e2e; border-top-color: #a78bfa; border-radius: 50%; animation: spin 1s linear infinite; }
.loading-ring.small { width: 20px; height: 20px; border-width: 2px; flex-shrink: 0; }
.loading-text { font-size: 16px; color: #a0a0b4; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Results */
.results-panel { max-width: 900px; margin: 40px auto; padding: 0 24px; }
.results-header { margin-bottom: 32px; }
.results-title { font-size: 22px; font-weight: 600; }
.results-meta { font-size: 13px; color: #6b6b82; margin-top: 4px; }

.section-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #6b6b82; margin: 0 0 16px; }

.ranking-section, .perf-section, .report-section { background: #0d0d14; border: 1px solid #1e1e2e; border-radius: 8px; padding: 24px; margin-bottom: 24px; }
.perf-section-header, .report-section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }

/* Ranking table */
.ranking-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.ranking-table th { text-align: left; padding: 8px 12px; border-bottom: 1px solid #1e1e2e; color: #6b6b82; font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; }
.ranking-table td { padding: 10px 12px; border-bottom: 1px solid #111118; }
.row-winner td { background: #0f0f1a; }
.rank-num { color: #4b4b60; width: 32px; }
.winner-star { color: #f59e0b; margin-right: 6px; }
.variant-name { font-weight: 500; }
.sim-id-cell { font-family: monospace; color: #6b6b82; font-size: 12px; }
.progress-cell { color: #6b6b82; font-size: 12px; }
.status-badge { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 11px; background: #1e1e2e; color: #6b6b82; }
.status-badge.preparing { color: #60a5fa; background: #0a1220; }
.status-badge.running { color: #34d399; background: #0a1a12; }
.status-badge.completed { color: #34d399; background: #0a1a12; }
.status-badge.failed { color: #f87171; background: #1a0a0a; }
.view-btn { background: transparent; border: 1px solid #1e1e2e; color: #a78bfa; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 12px; }

/* Personas grid */
.personas-section { background: #0d0d14; border: 1px solid #1e1e2e; border-radius: 8px; padding: 24px; margin-bottom: 24px; }
.personas-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }

/* LLM report */
.generate-report-btn { background: #a78bfa; color: #0a0a0f; border: none; padding: 8px 18px; border-radius: 5px; font-size: 13px; font-weight: 600; cursor: pointer; }
.generate-report-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.report-loading { display: flex; align-items: center; gap: 12px; padding: 12px 0; flex-wrap: wrap; }
.report-loading-text { font-size: 13px; color: #6b6b82; }
.report-progress-bar { width: 100%; height: 3px; background: #1e1e2e; border-radius: 2px; overflow: hidden; margin-top: 8px; }
.report-progress-fill { height: 100%; background: #a78bfa; transition: width 0.4s ease; }
.report-content { display: flex; flex-direction: column; gap: 16px; }
.report-summary { font-size: 14px; color: #c4b5fd; line-height: 1.6; padding: 16px; background: #12121f; border: 1px solid #3b2a6b; border-radius: 6px; }
.report-body-section { border-top: 1px solid #111118; padding-top: 16px; }
.subsection-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #4b4b60; margin: 0 0 8px; }
.section-body { font-size: 13px; line-height: 1.7; color: #a0a0b4; white-space: pre-wrap; }

.results-actions { display: flex; justify-content: flex-end; margin-top: 8px; }
.restart-btn { background: #111118; border: 1px solid #1e1e2e; color: #a0a0b4; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 13px; }
</style>
