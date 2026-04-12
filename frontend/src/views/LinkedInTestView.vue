<template>
  <div class="li-test-page">
    <header class="li-header">
      <div class="brand" @click="router.push('/')">PROSPECT-SIM</div>
      <span class="page-tag">LinkedIn Variant Test</span>
      <button v-if="results" class="download-btn" @click="downloadResults">↓ Export JSON</button>
      <div v-else></div>
    </header>

    <!-- Setup Form -->
    <div v-if="!results && !loading" class="setup-panel">
      <h2 class="setup-title">Test LinkedIn Outreach Copy</h2>
      <p class="setup-desc">
        Run connection request variants against synthetic B2B decision-maker personas before touching real prospects.
      </p>

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
          placeholder="E.g.: Test personalised vs. value-prop approach for VP Engineering personas at Series B startups." />
      </div>

      <div class="form-row form-row-inline">
        <label class="form-label">Run Mode</label>
        <div class="toggle-group">
          <button class="toggle-btn" :class="{ active: !form.parallel }" @click="form.parallel = false">Sequential</button>
          <button class="toggle-btn" :class="{ active: form.parallel }" @click="form.parallel = true">Parallel</button>
        </div>
        <span class="mode-hint">{{ form.parallel ? 'Faster, more LLM calls' : 'Slower, cheaper' }}</span>
      </div>

      <!-- Variant Cards -->
      <div class="variants-section">
        <div class="variants-header">
          <span class="variants-title">Connection Request Variants</span>
          <button class="add-variant-btn" @click="addVariant" :disabled="form.variants.length >= 6">+ Add Variant</button>
        </div>

        <div v-for="(variant, idx) in form.variants" :key="idx" class="variant-card">
          <div class="variant-card-header">
            <span class="variant-label">Variant {{ String.fromCharCode(65 + idx) }}</span>
            <select class="approach-select" v-model="variant.approach_type">
              <option value="personalized">Personalized</option>
              <option value="value_prop">Value Proposition</option>
              <option value="mutual_interest">Mutual Interest</option>
              <option value="direct">Direct Ask</option>
              <option value="question_based">Question-Based</option>
            </select>
            <button v-if="form.variants.length > 2" class="remove-btn" @click="removeVariant(idx)">✕</button>
          </div>

          <!-- Connection note: LinkedIn hard limit of 300 chars -->
          <div class="field-label-row">
            <label class="field-label">Connection Note</label>
            <span class="char-count" :class="{ warn: variant.connection_note.length > 280, error: variant.connection_note.length > 300 }">
              {{ variant.connection_note.length }}/300
            </span>
          </div>
          <textarea
            class="note-textarea"
            v-model="variant.connection_note"
            maxlength="300"
            placeholder="Hi [Name], I noticed you're scaling your engineering team — we've helped 3 similar CTOs reduce time-to-hire by 40%…"
            rows="3"
          />

          <!-- Opening message (sent after connection is accepted) -->
          <div class="field-label-row" style="margin-top:10px">
            <label class="field-label">Opening Message</label>
            <span class="word-count-label" :class="{ warn: wordCount(variant.opening_message) > 100 }">
              {{ wordCount(variant.opening_message) }} words
            </span>
          </div>
          <textarea
            class="body-textarea"
            v-model="variant.opening_message"
            placeholder="Thanks for connecting! [personalized opener]. I wanted to share something that's been useful for teams like yours…"
            rows="4"
          />
        </div>
      </div>

      <button class="run-btn" :disabled="!canRun" @click="runLinkedInTest">Run LinkedIn Test</button>
      <div v-if="error" class="li-error">{{ error }}</div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="li-loading">
      <div v-if="!results" class="loading-spinner-wrap">
        <div class="loading-ring"></div>
        <div class="loading-text">{{ loadingStatus || 'Setting up…' }}</div>
      </div>
      <div v-else class="loading-with-feed">
        <div class="loading-header-row">
          <div class="loading-ring small"></div>
          <span class="loading-status-text">{{ loadingStatus }}</span>
        </div>
        <!-- Live action feed — polls linkedin-events -->
        <div v-if="feedEvents.length > 0" class="action-feed">
          <div class="feed-header">Live Actions</div>
          <div v-for="ev in feedEvents" :key="ev.id" class="feed-event">
            <span class="feed-icon">{{ eventIcon(ev.event_type) }}</span>
            <span class="feed-label">{{ ev.variant_label }}</span>
            <span class="feed-action">{{ formatEvent(ev.event_type) }}</span>
            <span v-if="ev.notes" class="feed-notes">— {{ ev.notes }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Results Panel -->
    <div v-if="results && !loading" class="results-panel">
      <div class="results-header">
        <h2 class="results-title">LinkedIn Variant Test Results</h2>
        <div class="results-meta">
          {{ results.total_variants }} variants · {{ results.run_mode }} · {{ results.num_rounds }} rounds
        </div>
      </div>

      <!-- Simulation Status Table -->
      <div class="ranking-section">
        <h3 class="section-title">Simulations</h3>
        <table class="ranking-table">
          <thead>
            <tr>
              <th>#</th><th>Variant</th><th>Approach</th><th>Sim ID</th><th>Status</th><th>Progress</th><th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(run, idx) in results.variant_run_ids" :key="run.variant_id"
              :class="{ 'row-winner': idx === 0 && allCompleted }">
              <td class="rank-num">{{ idx + 1 }}</td>
              <td class="variant-name">
                <span v-if="idx === 0 && allCompleted" class="winner-star">★</span>
                {{ run.variant_label }}
              </td>
              <td>{{ getApproachType(run.variant_id) }}</td>
              <td class="sim-id-cell">{{ shortId(run.simulation_id) }}</td>
              <td><span class="status-badge" :class="run.status">{{ run.status }}</span></td>
              <td class="progress-cell">{{ run.progress || '—' }}</td>
              <td><button class="view-btn" @click="viewSimulation(run.simulation_id)">View →</button></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Variant Performance — appears as soon as results are available -->
      <div v-if="variantResults" class="perf-section">
        <h3 class="section-title">Performance Results</h3>

        <!-- Winner callout -->
        <div class="winner-banner">
          <div class="winner-crown">★ Winner</div>
          <div class="winner-name">{{ variantResults.winner.variant_label }}</div>
          <div class="winner-meta">
            {{ variantResults.winner.approach_type }} · composite {{ variantResults.winner.composite_score.toFixed(2) }}
          </div>
          <div v-if="variantResults.runner_up_delta" class="winner-delta">
            +{{ (variantResults.runner_up_delta.reply_rate_diff * 100).toFixed(1) }}% reply rate vs.
            {{ variantResults.runner_up_delta.label }}
          </div>
        </div>

        <!-- Stats table -->
        <table class="perf-table">
          <thead>
            <tr>
              <th>Variant</th><th>Approach</th><th>Agents</th>
              <th>Accept %</th><th>View %</th><th>Reply %</th><th>Score</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(v, idx) in variantResults.variants" :key="v.variant_label"
              :class="{ 'perf-winner': idx === 0 }">
              <td class="perf-variant">{{ v.variant_label }}</td>
              <td class="perf-approach">{{ v.approach_type }}</td>
              <td>{{ v.total_agents }}</td>
              <td>{{ (v.accept_rate * 100).toFixed(1) }}%</td>
              <td>{{ (v.view_rate * 100).toFixed(1) }}%</td>
              <td class="perf-reply">{{ (v.reply_rate * 100).toFixed(1) }}%</td>
              <td class="perf-score">{{ v.composite_score.toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>

        <!-- Approach-type ranking -->
        <div v-if="variantResults.approach_types?.length > 0" class="approach-ranking">
          <div class="approach-title">Approach Type Ranking</div>
          <div v-for="at in variantResults.approach_types" :key="at.approach_type" class="approach-row">
            <span class="approach-name">{{ at.approach_type }}</span>
            <span class="approach-stat">{{ (at.avg_reply_rate * 100).toFixed(1) }}% reply</span>
            <span class="approach-stat-sec">{{ (at.avg_accept_rate * 100).toFixed(1) }}% accept</span>
            <span class="approach-count">n={{ at.count }}</span>
          </div>
        </div>

        <!-- Dropout funnel -->
        <div v-if="Object.keys(variantResults.dropouts || {}).length > 0" class="dropout-section">
          <div class="dropout-title">Dropout Funnel</div>
          <div v-for="(dropouts, variantLabel) in variantResults.dropouts" :key="variantLabel" class="dropout-group">
            <div class="dropout-variant-label">{{ variantLabel }}</div>
            <div v-for="d in dropouts" :key="d.dropout_point" class="dropout-row">
              <span class="dropout-point">{{ d.dropout_point }}</span>
              <span class="dropout-bar-wrap">
                <span class="dropout-bar"
                  :style="{ width: Math.min(100, d.count * 20) + '%' }"></span>
              </span>
              <span class="dropout-count">{{ d.count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- LLM Report -->
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
          <div class="report-progress-bar">
            <div class="report-progress-fill" :style="{ width: reportProgress + '%' }"></div>
          </div>
        </div>
        <div v-if="reportError" class="li-error">{{ reportError }}</div>

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

export default {
  name: 'LinkedInTestView',

  setup() {
    const router = useRouter()
    const projects = ref([])
    const loading = ref(false)
    const loadingStatus = ref('')
    const error = ref('')
    const results = ref(null)

    // Live action feed events (polled from /linkedin-events during simulation)
    const feedEvents = ref([])
    let feedPollTimer = null
    let feedNextId = 0
    let feedSimId = ''

    // Structured variant metrics (loaded after any sim completes — no LLM required)
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
        { id: 1, label: 'Variant A', approach_type: 'personalized',  connection_note: '', opening_message: '' },
        { id: 2, label: 'Variant B', approach_type: 'value_prop',    connection_note: '', opening_message: '' },
      ],
    })

    const canRun = computed(() =>
      !!form.value.projectId &&
      form.value.variants.every((v) =>
        v.connection_note.trim() &&
        v.connection_note.length <= 300 &&
        v.opening_message.trim()
      )
    )

    // First simulation ID — used for results lookup
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
      form.value.variants.push({
        id: next,
        label: `Variant ${String.fromCharCode(64 + next)}`,
        approach_type: 'direct',
        connection_note: '',
        opening_message: '',
      })
    }

    function removeVariant(idx) {
      form.value.variants.splice(idx, 1)
      form.value.variants.forEach((v, i) => {
        v.id = i + 1
        v.label = `Variant ${String.fromCharCode(65 + i)}`
      })
    }

    function getApproachType(variantId) {
      return form.value.variants.find((x) => x.id === variantId)?.approach_type || '—'
    }

    function shortId(id) { return id ? id.slice(-8) : '—' }

    // Map event_type to a short readable label for the live feed
    function formatEvent(eventType) {
      const labels = {
        accept_connection: 'accepted connection',
        view_profile:      'viewed profile',
        reply_message:     'replied',
        ignore_request:    'ignored',
        check_profile:     'checked profile',
        do_nothing:        'no action',
      }
      return labels[eventType] || eventType
    }

    function eventIcon(eventType) {
      const icons = {
        accept_connection: '✓',
        view_profile:      '👁',
        reply_message:     '↩',
        ignore_request:    '✗',
        check_profile:     '◉',
        do_nothing:        '·',
      }
      return icons[eventType] || '·'
    }

    async function loadProjects() {
      try {
        const data = await fetch('/api/simulation/projects').then((r) => r.json())
        if (data.success) projects.value = data.projects || []
      } catch (e) { console.warn('Could not load projects:', e) }
    }

    /** Start polling /linkedin-events for the live action feed. */
    function startFeedPoll(simId) {
      feedSimId = simId
      feedNextId = 0
      feedEvents.value = []
      feedPollTimer = setInterval(async () => {
        try {
          const data = await fetch(
            `/api/simulation/${feedSimId}/linkedin-events?since_id=${feedNextId}`
          ).then((r) => r.json())
          if (data.success && data.data?.events?.length) {
            // Prepend newest events so the feed shows most recent at top (cap at 40)
            feedEvents.value = [...data.data.events.reverse(), ...feedEvents.value].slice(0, 40)
            feedNextId = data.data.next_id
          }
        } catch (_) { /* non-fatal, keep polling */ }
      }, 3000)
    }

    function stopFeedPoll() {
      if (feedPollTimer) { clearInterval(feedPollTimer); feedPollTimer = null }
    }

    /** Fetch structured variant metrics from SQLite. */
    async function fetchVariantResults(simId) {
      if (variantResults.value) return
      variantResultsLoading.value = true
      variantResultsError.value = ''
      try {
        const data = await fetch(`/api/simulation/${simId}/linkedin-variant-results`).then((r) => r.json())
        if (!data.success) throw new Error(data.error || 'Failed to load results')
        variantResults.value = data.data
      } catch (e) {
        variantResultsError.value = e.message
      } finally {
        variantResultsLoading.value = false
      }
    }

    async function runLinkedInTest() {
      if (!canRun.value) return
      loading.value = true
      error.value = ''
      results.value = null
      variantResults.value = null
      feedEvents.value = []
      loadingStatus.value = 'Creating simulations…'

      try {
        const resp = await fetch('/api/simulation/run-linkedin-test', {
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
        if (!data.success) throw new Error(data.error || 'LinkedIn test failed')

        results.value = data
        loadingStatus.value = 'Preparing agent profiles…'

        // Start live feed for the first simulation
        const firstSim = data.variant_run_ids?.[0]?.simulation_id
        if (firstSim) startFeedPoll(firstSim)

        const variantRuns = data.variant_run_ids || []
        await Promise.all(variantRuns.map((run) => orchestrateSim(run, data.num_rounds)))

        results.value = { ...results.value }
        loadingStatus.value = 'All simulations complete'
      } catch (e) {
        error.value = e.message || 'Unexpected error'
      } finally {
        loading.value = false
        stopFeedPoll()
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

      // Poll prepare phase
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
      }

      // Start simulation
      setRunStatus('starting')
      loadingStatus.value = 'Running agents…'
      const startData = await fetch('/api/simulation/start', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          simulation_id,
          platform: 'linkedin_outreach',
          max_rounds: numRounds || 8,
        }),
      }).then((r) => r.json())

      if (!startData.success) {
        setRunStatus('failed')
        return
      }

      // Poll run status until complete
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

      // Fetch structured metrics immediately — no LLM needed
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
      a.href = url; a.download = `linkedin-test-${Date.now()}.json`; a.click()
      URL.revokeObjectURL(url)
    }

    function resetForm() {
      results.value = null; error.value = ''
      variantResults.value = null; variantResultsError.value = ''; variantResultsLoading.value = false
      report.value = null; reportError.value = ''; reportLoading.value = false
      feedEvents.value = []; feedNextId = 0
      stopFeedPoll()
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
          if (data.data.status === 'completed') { clearInterval(reportPollTimer); fetchReport(reportId) }
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

    onUnmounted(() => {
      stopFeedPoll()
      if (reportPollTimer) clearInterval(reportPollTimer)
    })
    onMounted(() => { loadProjects() })

    return {
      router, projects, loading, loadingStatus, error, results,
      feedEvents, variantResults, variantResultsLoading, variantResultsError,
      form, canRun, firstSimId, allCompleted,
      wordCount, addVariant, removeVariant, getApproachType, shortId,
      formatEvent, eventIcon,
      runLinkedInTest, viewSimulation, downloadResults, resetForm,
      report, reportLoading, reportError, reportStatus, reportProgress, generateReport,
    }
  },
}
</script>

<style scoped>
.li-test-page {
  min-height: 100vh;
  background: #0a0a0f;
  color: #e4e4e9;
  font-family: 'Inter', 'SF Pro', system-ui, sans-serif;
}

/* Header — same pattern as VariantTestView but tinted blue for LinkedIn brand feel */
.li-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 32px; height: 56px;
  border-bottom: 1px solid #1e1e2e; background: #0d0d14;
}
.brand { font-size: 13px; font-weight: 700; letter-spacing: 0.12em; cursor: pointer; color: #60a5fa; }
.page-tag { font-size: 11px; background: #0a1220; color: #60a5fa; padding: 3px 10px; border-radius: 4px; letter-spacing: 0.08em; text-transform: uppercase; }
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
.toggle-btn.active { background: #0a1220; border-color: #60a5fa; color: #60a5fa; }
.mode-hint { font-size: 12px; color: #4b4b60; }

/* Variants */
.variants-section { margin-bottom: 28px; }
.variants-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.variants-title { font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #8b8ba0; }
.add-variant-btn { background: transparent; border: 1px dashed #2e2e42; color: #6b6b82; padding: 5px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; }
.add-variant-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.variant-card { background: #0d0d14; border: 1px solid #1e1e2e; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
.variant-card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.variant-label { font-size: 13px; font-weight: 600; color: #60a5fa; min-width: 80px; }
.approach-select { background: #111118; border: 1px solid #1e1e2e; color: #a0a0b4; padding: 4px 8px; border-radius: 4px; font-size: 12px; flex: 1; }
.remove-btn { background: transparent; border: none; color: #4b4b60; cursor: pointer; font-size: 14px; padding: 4px; margin-left: auto; }

.field-label-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.field-label { font-size: 11px; color: #6b6b82; text-transform: uppercase; letter-spacing: 0.06em; }
.char-count { font-size: 11px; color: #4b4b60; }
.char-count.warn { color: #f59e0b; }
.char-count.error { color: #f87171; }
.word-count-label { font-size: 11px; color: #4b4b60; }
.word-count-label.warn { color: #f59e0b; }

.note-textarea, .body-textarea {
  width: 100%; background: #111118; border: 1px solid #1e1e2e;
  color: #e4e4e9; padding: 8px 12px; border-radius: 4px;
  font-size: 13px; line-height: 1.6; resize: vertical; box-sizing: border-box;
}

.run-btn { width: 100%; background: #2563eb; color: #fff; border: none; padding: 14px; border-radius: 6px; font-size: 15px; font-weight: 600; cursor: pointer; letter-spacing: 0.04em; }
.run-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.li-error { margin-top: 12px; color: #f87171; font-size: 13px; padding: 10px; background: #1a0a0a; border-radius: 4px; }

/* Loading */
.li-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 60vh; gap: 16px; }
.loading-spinner-wrap { display: flex; flex-direction: column; align-items: center; gap: 16px; }
.loading-with-feed { width: 100%; max-width: 720px; padding: 32px 24px; display: flex; flex-direction: column; gap: 16px; }
.loading-header-row { display: flex; align-items: center; gap: 10px; }
.loading-status-text { font-size: 13px; color: #6b6b82; }
.loading-ring { width: 40px; height: 40px; border: 3px solid #1e1e2e; border-top-color: #60a5fa; border-radius: 50%; animation: spin 1s linear infinite; }
.loading-ring.small { width: 20px; height: 20px; border-width: 2px; flex-shrink: 0; }
.loading-text { font-size: 16px; color: #a0a0b4; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Live action feed */
.action-feed { background: #0d0d14; border: 1px solid #1e1e2e; border-radius: 8px; overflow: hidden; }
.feed-header { font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: #4b4b60; padding: 8px 14px; border-bottom: 1px solid #111118; }
.feed-event { display: flex; align-items: center; gap: 8px; padding: 7px 14px; border-bottom: 1px solid #0d0d14; font-size: 12px; }
.feed-event:last-child { border-bottom: none; }
.feed-icon { width: 16px; text-align: center; font-size: 13px; }
.feed-label { color: #60a5fa; min-width: 90px; }
.feed-action { color: #a0a0b4; }
.feed-notes { color: #6b6b82; font-style: italic; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }

/* Results */
.results-panel { max-width: 900px; margin: 40px auto; padding: 0 24px; }
.results-header { margin-bottom: 32px; }
.results-title { font-size: 22px; font-weight: 600; }
.results-meta { font-size: 13px; color: #6b6b82; margin-top: 4px; }
.section-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #6b6b82; margin: 0 0 16px; }

.ranking-section, .perf-section, .report-section {
  background: #0d0d14; border: 1px solid #1e1e2e; border-radius: 8px; padding: 24px; margin-bottom: 24px;
}
.report-section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }

/* Simulation table */
.ranking-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.ranking-table th { text-align: left; padding: 8px 12px; border-bottom: 1px solid #1e1e2e; color: #6b6b82; font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; }
.ranking-table td { padding: 10px 12px; border-bottom: 1px solid #111118; }
.row-winner td { background: #0a1220; }
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
.view-btn { background: transparent; border: 1px solid #1e1e2e; color: #60a5fa; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 12px; }

/* Winner banner */
.winner-banner {
  background: #0a1220; border: 1px solid #1d4ed8; border-radius: 6px;
  padding: 16px 20px; margin-bottom: 24px;
}
.winner-crown { font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #f59e0b; font-weight: 700; margin-bottom: 6px; }
.winner-name { font-size: 18px; font-weight: 600; color: #60a5fa; margin-bottom: 4px; }
.winner-meta { font-size: 12px; color: #6b6b82; }
.winner-delta { font-size: 12px; color: #34d399; margin-top: 4px; }

/* Perf table */
.perf-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 24px; }
.perf-table th { text-align: left; padding: 8px 12px; border-bottom: 1px solid #1e1e2e; color: #6b6b82; font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; }
.perf-table td { padding: 10px 12px; border-bottom: 1px solid #111118; }
.perf-winner td { background: #0a1220; }
.perf-variant { font-weight: 500; }
.perf-approach { color: #6b6b82; }
.perf-reply { color: #34d399; font-weight: 500; }
.perf-score { color: #60a5fa; font-family: monospace; font-weight: 600; }

/* Approach ranking */
.approach-ranking { margin-bottom: 24px; }
.approach-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #6b6b82; margin-bottom: 12px; }
.approach-row { display: flex; align-items: center; gap: 12px; padding: 7px 0; border-bottom: 1px solid #111118; font-size: 12px; }
.approach-name { min-width: 160px; color: #a0a0b4; }
.approach-stat { color: #34d399; min-width: 80px; font-family: monospace; }
.approach-stat-sec { color: #60a5fa; min-width: 80px; font-family: monospace; }
.approach-count { color: #4b4b60; margin-left: auto; }

/* Dropout funnel */
.dropout-section { }
.dropout-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #6b6b82; margin-bottom: 12px; }
.dropout-group { margin-bottom: 16px; }
.dropout-variant-label { font-size: 12px; font-weight: 600; color: #a0a0b4; margin-bottom: 6px; }
.dropout-row { display: flex; align-items: center; gap: 10px; padding: 4px 0; font-size: 12px; }
.dropout-point { min-width: 140px; color: #6b6b82; }
.dropout-bar-wrap { flex: 1; height: 6px; background: #1e1e2e; border-radius: 3px; overflow: hidden; }
.dropout-bar { display: block; height: 100%; background: #f87171; border-radius: 3px; transition: width 0.4s ease; }
.dropout-count { width: 24px; text-align: right; color: #4b4b60; }

/* LLM report */
.generate-report-btn { background: #2563eb; color: #fff; border: none; padding: 8px 18px; border-radius: 5px; font-size: 13px; font-weight: 600; cursor: pointer; }
.generate-report-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.report-loading { display: flex; align-items: center; gap: 12px; padding: 12px 0; flex-wrap: wrap; }
.report-loading-text { font-size: 13px; color: #6b6b82; }
.report-progress-bar { width: 100%; height: 3px; background: #1e1e2e; border-radius: 2px; overflow: hidden; margin-top: 8px; }
.report-progress-fill { height: 100%; background: #2563eb; transition: width 0.4s ease; }
.report-content { display: flex; flex-direction: column; gap: 16px; }
.report-summary { font-size: 14px; color: #93c5fd; line-height: 1.6; padding: 16px; background: #0a1220; border: 1px solid #1d4ed8; border-radius: 6px; }
.report-body-section { border-top: 1px solid #111118; padding-top: 16px; }
.subsection-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #4b4b60; margin: 0 0 8px; }
.section-body { font-size: 13px; line-height: 1.7; color: #a0a0b4; white-space: pre-wrap; }

.results-actions { display: flex; justify-content: flex-end; margin-top: 8px; }
.restart-btn { background: #111118; border: 1px solid #1e1e2e; color: #a0a0b4; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 13px; }
</style>
