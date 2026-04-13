<template>
  <div class="home-container">
    <!-- Top Navigation Bar -->
    <nav class="navbar">
      <div class="nav-brand">MIROSHARK</div>
      <div class="nav-links">
        <a href="https://github.com/aaronjmars/MiroShark" target="_blank" class="github-link">
          GitHub <span class="arrow">↗</span>
        </a>
        <button class="settings-btn" @click="settingsOpen = true" title="Settings">
          ⚙
        </button>
      </div>
    </nav>

    <SettingsPanel :open="settingsOpen" @close="settingsOpen = false" />

    <div class="main-content">
      <!-- Upper Section: Hero Area -->
      <section class="hero-section">
        <div class="tag-row">
          <span class="orange-tag">A Concise & Universal Swarm Intelligence Engine</span>
        </div>

        <h1 class="main-title">
          <span class="gradient-text">Simulate the Future Instantly</span>
        </h1>

        <div class="hero-desc">
          <p>
            Upload any document. <span class="highlight-bold">MiroShark</span> extracts the key players, generates <span class="highlight-orange">hundreds of AI agents</span> with unique personas, and simulates how they'd react on Twitter and Reddit. Watch opinions form, arguments spread, and narratives evolve.
          </p>
          <p class="slogan-text">
            Don't predict the future. Simulate it<span class="blinking-cursor">_</span>
          </p>
        </div>

        <div class="decoration-square"></div>

        <button class="scroll-down-btn" @click="scrollToBottom">
          ↓
        </button>
      </section>

      <!-- Lower Section: Two-Column Layout -->
      <section class="dashboard-section">
        <!-- Left Column: Status & Steps -->
        <div class="left-panel">
          <div class="panel-header">
            <span class="status-dot">■</span> System Status
          </div>

          <h2 class="section-title">Ready</h2>
          <p class="section-desc">
            Prediction engine on standby. Upload documents to initialize the simulation sequence.
          </p>

          <!-- Simulation Steps Overview -->
          <div class="steps-container">
            <div class="steps-header">
              <span class="diamond-icon">◇</span> Workflow Sequence
            </div>
            <div class="workflow-list">
              <div class="workflow-item">
                <span class="step-num">01</span>
                <div class="step-info">
                  <div class="step-title">Graph Construction</div>
                  <div class="step-desc">Reality seed extraction & Individual/group memory injection & GraphRAG construction</div>
                </div>
              </div>
              <div class="workflow-item">
                <span class="step-num">02</span>
                <div class="step-info">
                  <div class="step-title">Agent Setup</div>
                  <div class="step-desc">Entity-relation extraction & Persona generation & Environment config Agent injects simulation parameters</div>
                </div>
              </div>
              <div class="workflow-item">
                <span class="step-num">03</span>
                <div class="step-info">
                  <div class="step-title">Start Simulation</div>
                  <div class="step-desc">Dual-platform parallel simulation & Automatic prediction requirement parsing & Dynamic temporal memory updates</div>
                </div>
              </div>
              <div class="workflow-item">
                <span class="step-num">04</span>
                <div class="step-info">
                  <div class="step-title">Report Generation</div>
                  <div class="step-desc">ReportAgent has a rich toolset for in-depth interaction with the post-simulation environment</div>
                </div>
              </div>
              <div class="workflow-item">
                <span class="step-num">05</span>
                <div class="step-info">
                  <div class="step-title">Deep Interaction</div>
                  <div class="step-desc">Chat with any agent in the simulated world & Converse with the ReportAgent</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column: Platform Selector → Simulation Console -->
        <div class="right-panel">
          <!-- State 0: platform picker (default) -->
          <PlatformSelectorPanel
            v-show="selectedPlatform === null"
            @select="handlePlatformSelect"
          />

          <!-- State 1: simulation console — v-show preserves form state when user returns to selector -->
          <div v-show="selectedPlatform !== null" class="console-wrapper">
            <button class="back-to-platforms" @click="selectedPlatform = null">← platforms</button>
            <SimConsolePanel />
          </div>
        </div>
      </section>

      <!-- Quick Start Templates -->
      <TemplateGallery />

      <!-- History Project Database -->
      <HistoryDatabase />

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import HistoryDatabase from '../components/HistoryDatabase.vue'
import TemplateGallery from '../components/TemplateGallery.vue'
import SettingsPanel from '../components/SettingsPanel.vue'
import PlatformSelectorPanel from '../components/PlatformSelectorPanel.vue'
import SimConsolePanel from '../components/SimConsolePanel.vue'

const router = useRouter()
const settingsOpen = ref(false)

// null = platform selector visible; 'social' = console visible
const selectedPlatform = ref(null)

function handlePlatformSelect(id) {
  if (id === 'email') {
    router.push('/variant-test')
    return
  }
  if (id === 'linkedin') {
    router.push('/linkedin-test')
    return
  }
  // 'social' — show the simulation console
  selectedPlatform.value = id
}

const scrollToBottom = () => {
  window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════
   HOME — Hyperstitions Design System applied
   Console-box CSS lives in SimConsolePanel.vue (scoped)
   ═══════════════════════════════════════════════════════════ */

.home-container {
  min-height: 100vh;
  background: var(--background);
  font-family: var(--font-display);
  color: var(--foreground);
}

/* ── Top Navigation ── */
.navbar {
  height: var(--space-xl);
  background: var(--color-black);
  color: var(--color-white);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 var(--space-lg);
}

.nav-brand {
  font-family: var(--font-mono);
  font-weight: 700;
  letter-spacing: 3px;
  font-size: 14px;
  text-transform: uppercase;
}

.nav-links {
  display: flex;
  align-items: center;
}

.github-link {
  color: var(--color-white);
  text-decoration: none;
  font-family: var(--font-mono);
  font-size: 13px;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  transition: var(--transition-fast);
  opacity: 0.6;
}

.github-link:hover { opacity: 1; }

.arrow { font-family: sans-serif; }

.settings-btn {
  background: none;
  border: none;
  color: rgba(250,250,250,0.5);
  font-size: 18px;
  cursor: pointer;
  padding: 0 0 0 var(--space-md);
  line-height: 1;
  transition: var(--transition-fast);
}

.settings-btn:hover { color: var(--color-orange); }

/* ── Main Content ── */
.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--space-2xl) var(--space-lg);
}

/* ── Hero Section ── */
.hero-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  margin-bottom: var(--space-2xl);
  position: relative;
}

.tag-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
  font-family: var(--font-mono);
  font-size: 13px;
}

.orange-tag {
  background: var(--color-orange);
  color: var(--color-white);
  padding: 4px var(--space-sm);
  font-weight: 700;
  letter-spacing: 3px;
  font-size: 11px;
  text-transform: uppercase;
  font-family: var(--font-mono);
}

.main-title {
  font-family: var(--font-display);
  font-size: 50px;
  line-height: 1.25;
  font-weight: 400;
  margin: 0 0 var(--space-lg) 0;
  letter-spacing: -1px;
  color: var(--foreground);
}

.gradient-text {
  color: var(--color-orange);
  -webkit-text-fill-color: var(--color-orange);
  display: inline;
}

.hero-desc {
  font-family: var(--font-display);
  font-size: 22px;
  line-height: 1.5;
  color: rgba(10,10,10,0.7);
  max-width: 640px;
  margin-bottom: var(--space-xl);
}

.hero-desc p { margin-bottom: var(--space-md); }

.highlight-bold { color: var(--foreground); font-weight: 400; }

.highlight-orange {
  color: var(--color-orange);
  font-family: var(--font-mono);
  font-size: 0.85em;
}

.slogan-text {
  font-family: var(--font-display);
  font-size: 25px;
  line-height: 1.5;
  color: var(--foreground);
  border-left: var(--border-orange);
  padding-left: var(--space-md);
  margin-top: var(--space-md);
}

.blinking-cursor {
  color: var(--color-green);
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.decoration-square {
  width: var(--space-sm);
  height: var(--space-sm);
  background: var(--color-green);
  margin-top: var(--space-md);
}

.scroll-down-btn {
  margin-top: var(--space-md);
  width: var(--space-lg);
  height: var(--space-lg);
  border: var(--border-medium);
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--color-orange);
  font-size: 1.2rem;
  transition: var(--transition-fast);
}

.scroll-down-btn:hover { border-color: var(--color-orange); }

/* ── Warning Stripe Divider ── */
.dashboard-section::before {
  content: '';
  display: block;
  height: 7px;
  background: repeating-linear-gradient(
    -45deg,
    var(--color-orange),
    var(--color-orange) 11px,
    var(--background) 11px,
    var(--background) 22px
  );
  margin-bottom: var(--space-xl);
}

/* ── Dashboard Section ── */
.dashboard-section {
  display: flex;
  gap: var(--space-xl);
  padding-top: 0;
  align-items: flex-start;
}

.dashboard-section .left-panel,
.dashboard-section .right-panel {
  display: flex;
  flex-direction: column;
}

/* ── Left Panel ── */
.left-panel { flex: 0.8; }

.panel-header {
  font-family: var(--font-mono);
  font-size: 14px;
  color: rgba(10,10,10,0.4);
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  margin-bottom: var(--space-md);
  letter-spacing: 3px;
  text-transform: uppercase;
}

.status-dot { color: var(--color-green); font-size: 0.8rem; }

.section-title {
  font-family: var(--font-display);
  font-size: 34px;
  font-weight: 400;
  margin: 0 0 var(--space-sm) 0;
}

.section-desc {
  color: rgba(10,10,10,0.5);
  font-family: var(--font-display);
  font-size: 22px;
  margin-bottom: var(--space-md);
  line-height: 1.5;
}

/* ── Workflow Steps ── */
.steps-container {
  border: var(--border-light);
  padding: var(--space-lg);
  position: relative;
}

.steps-container::before,
.steps-container::after {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  pointer-events: none;
}

.steps-container::before {
  top: 12px; left: 12px;
  border-top: 3px solid var(--color-orange);
  border-left: 3px solid var(--color-orange);
}

.steps-container::after {
  bottom: 12px; right: 12px;
  border-bottom: 3px solid var(--color-green);
  border-right: 3px solid var(--color-green);
}

.steps-header {
  font-family: var(--font-mono);
  font-size: 14px;
  color: rgba(10,10,10,0.4);
  margin-bottom: var(--space-md);
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  letter-spacing: 3px;
  text-transform: uppercase;
}

.diamond-icon { color: var(--color-orange); font-size: 1.2rem; }

.workflow-list { display: flex; flex-direction: column; gap: var(--space-md); }

.workflow-item { display: flex; align-items: flex-start; gap: var(--space-md); }

.step-num {
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 15px;
  color: var(--color-orange);
  opacity: 0.5;
}

.step-info { flex: 1; }

.step-title { font-family: var(--font-display); font-size: 22px; margin-bottom: 4px; }

.step-desc {
  font-family: var(--font-mono);
  font-size: 13px;
  color: rgba(10,10,10,0.4);
  line-height: 1.6;
}

/* ── Right Panel ── */
.right-panel { flex: 1.2; }

/* Wrapper for the back-link + console */
.console-wrapper {
  display: flex;
  flex-direction: column;
}

/* Back navigation — dark text on light background (opposite of dark-theme back buttons) */
.back-to-platforms {
  background: none;
  border: none;
  cursor: pointer;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  color: rgba(10,10,10,0.4);
  letter-spacing: 2px;
  text-transform: uppercase;
  padding: 0 0 var(--space-sm) 0;
  text-align: left;
  transition: var(--transition-fast);
}

.back-to-platforms:hover { color: var(--color-orange); }

/* ── Responsive ── */
@media (max-width: 1024px) {
  .dashboard-section { flex-direction: column; }
  .main-title { font-size: 34px; }
}
</style>
