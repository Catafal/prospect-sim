<template>
  <div class="persona-card">
    <div class="persona-header">
      <div class="persona-name">{{ profile.name || profile.user_name }}</div>
      <span v-if="profile.budget_authority" class="budget-badge">BUDGET ✓</span>
    </div>

    <div class="persona-role">{{ roleExcerpt }}</div>

    <!-- Skepticism bar: green <0.4, amber 0.4-0.7, red >0.7 -->
    <div class="persona-row">
      <span class="persona-label">Skepticism</span>
      <div class="skepticism-bar-wrap">
        <div
          class="skepticism-bar-fill"
          :style="{ width: skepticismPct + '%' }"
          :class="skepticismClass"
        ></div>
      </div>
      <span class="skepticism-score">{{ scoreLabel }}</span>
    </div>

    <div class="persona-row">
      <span class="persona-label">Inbox</span>
      <span class="persona-value">{{ formatInboxHabit }}</span>
    </div>

    <div class="persona-row">
      <span class="persona-label">Style</span>
      <span class="persona-value">{{ formatDecisionStyle }}</span>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'EmailPersonaCard',
  props: {
    profile: {
      type: Object,
      required: true,
    },
  },
  setup(props) {
    // Truncate bio/persona to a role-style excerpt
    const roleExcerpt = computed(() => {
      const text = props.profile.bio || props.profile.persona || ''
      return text.length > 60 ? text.slice(0, 57) + '…' : text
    })

    const skepticismPct = computed(() =>
      Math.round((props.profile.cold_email_skepticism ?? 0.5) * 100)
    )

    // Bar color tier based on skepticism level
    const skepticismClass = computed(() => {
      const s = props.profile.cold_email_skepticism ?? 0.5
      if (s < 0.4) return 'low'
      if (s < 0.7) return 'mid'
      return 'high'
    })

    const scoreLabel = computed(() =>
      (props.profile.cold_email_skepticism ?? 0.5).toFixed(2)
    )

    // Human-readable inbox habit labels
    const formatInboxHabit = computed(() => {
      const map = {
        batch_processor: 'Batch processor',
        morning_scanner: 'Morning scanner',
        responsive: 'Responsive',
        real_time: 'Real-time',
      }
      return map[props.profile.inbox_habit] || props.profile.inbox_habit || '—'
    })

    // Human-readable decision style labels
    const formatDecisionStyle = computed(() => {
      const map = {
        roi_driven: 'ROI-driven',
        risk_averse: 'Risk-averse',
        early_adopter: 'Early adopter',
        social_proof: 'Social proof',
        consensus: 'Consensus',
      }
      return map[props.profile.decision_style] || props.profile.decision_style || '—'
    })

    return { roleExcerpt, skepticismPct, skepticismClass, scoreLabel, formatInboxHabit, formatDecisionStyle }
  },
}
</script>

<style scoped>
.persona-card {
  background: #111118;
  border: 1px solid #1e1e2e;
  border-radius: 8px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 12px;
}

.persona-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.persona-name {
  font-size: 13px;
  font-weight: 600;
  color: #e4e4e9;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.budget-badge {
  font-size: 10px;
  background: #1a2a1a;
  color: #4ade80;
  border: 1px solid #2a4a2a;
  padding: 2px 6px;
  border-radius: 3px;
  white-space: nowrap;
  flex-shrink: 0;
}

.persona-role {
  color: #6b6b82;
  font-size: 11px;
  line-height: 1.4;
  min-height: 16px;
}

.persona-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.persona-label {
  color: #4b4b60;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  width: 62px;
  flex-shrink: 0;
}

.persona-value {
  color: #a0a0b4;
  font-size: 11px;
}

/* Skepticism bar */
.skepticism-bar-wrap {
  flex: 1;
  height: 4px;
  background: #1e1e2e;
  border-radius: 2px;
  overflow: hidden;
}

.skepticism-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.skepticism-bar-fill.low  { background: #4ade80; }
.skepticism-bar-fill.mid  { background: #f59e0b; }
.skepticism-bar-fill.high { background: #f87171; }

.skepticism-score {
  color: #6b6b82;
  font-size: 10px;
  width: 28px;
  text-align: right;
  flex-shrink: 0;
}
</style>
