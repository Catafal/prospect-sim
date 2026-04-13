<template>
  <div class="platform-selector">
    <div class="selector-header">
      <span class="diamond-icon">◇</span> Choose Simulation Mode
    </div>

    <div class="platform-cards">
      <div
        v-for="p in PLATFORMS"
        :key="p.id"
        class="platform-card"
        :class="{ disabled: p.disabled }"
        @click="!p.disabled && emit('select', p.id)"
      >
        <div class="card-icon">{{ p.icon }}</div>
        <div class="card-body">
          <div class="card-label">{{ p.label }}</div>
          <div class="card-sub">{{ p.sub }}</div>
        </div>
        <div v-if="p.disabled" class="coming-soon-badge">SOON</div>
        <div v-else class="card-arrow">→</div>
      </div>
    </div>
  </div>
</template>

<script setup>
// PLATFORMS is module-level (not in setup) — static data, no reactivity needed.
// disabled:true is the single source of truth for whether a platform is interactive.
// To enable LinkedIn: set disabled:false here only.
const PLATFORMS = [
  {
    id: 'social',
    icon: '◈',
    label: 'Social Simulation',
    sub: 'Twitter + Reddit',
    disabled: false,
  },
  {
    id: 'email',
    icon: '✉',
    label: 'Email Variant Test',
    sub: 'Cold email copy testing',
    disabled: false,
  },
  {
    id: 'linkedin',
    icon: 'in',
    label: 'LinkedIn Outreach',
    sub: 'B2B prospecting',
    disabled: false,
  },
]

const emit = defineEmits(['select'])
</script>

<style scoped>
.platform-selector {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

/* Header matches .steps-header pattern from Home.vue */
.selector-header {
  font-family: var(--font-mono);
  font-size: 14px;
  color: rgba(10, 10, 10, 0.4);
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  letter-spacing: 3px;
  text-transform: uppercase;
}

.diamond-icon {
  color: var(--color-orange);
  font-size: 1.2rem;
}

.platform-cards {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

/* Active card — matches .metric-card hover pattern from Home.vue */
.platform-card {
  border: var(--border-medium);
  padding: var(--space-md) var(--space-lg);
  display: flex;
  align-items: center;
  gap: var(--space-md);
  cursor: pointer;
  transition: var(--transition-fast);
  background: var(--background);
  position: relative;
}

.platform-card:not(.disabled):hover {
  border-color: var(--color-orange);
}

/* Disabled state — pointer-events blocks click; cursor and opacity signal non-interactive */
.platform-card.disabled {
  opacity: 0.35;
  cursor: not-allowed;
  pointer-events: none;
}

.card-icon {
  font-family: var(--font-mono);
  font-size: 22px;
  color: var(--color-orange);
  width: 32px;
  flex-shrink: 0;
  text-align: center;
}

.card-body {
  flex: 1;
}

.card-label {
  font-family: var(--font-display);
  font-size: 22px;
  color: var(--foreground);
  margin-bottom: 2px;
}

.card-sub {
  font-family: var(--font-mono);
  font-size: 12px;
  color: rgba(10, 10, 10, 0.4);
  letter-spacing: 1px;
}

.card-arrow {
  font-family: var(--font-mono);
  font-size: 18px;
  color: rgba(10, 10, 10, 0.2);
  transition: var(--transition-fast);
}

.platform-card:not(.disabled):hover .card-arrow {
  color: var(--color-orange);
}

/* Coming-soon badge — mono tag matching other meta labels */
.coming-soon-badge {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  color: rgba(10, 10, 10, 0.4);
  letter-spacing: 2px;
  border: 1px solid rgba(10, 10, 10, 0.15);
  padding: 2px 6px;
}
</style>
