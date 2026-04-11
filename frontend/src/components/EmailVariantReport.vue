<template>
  <div class="variant-report">
    <!-- Loading state -->
    <div v-if="loading" class="report-loading-row">
      <div class="loading-ring small"></div>
      <span class="report-loading-text">Loading results…</span>
    </div>

    <!-- Error state -->
    <div v-if="error" class="report-error">{{ error }}</div>

    <!-- No data yet -->
    <div v-if="!loading && !error && !variantResults" class="report-empty">
      Results will appear here once the simulation completes.
    </div>

    <!-- Full report -->
    <template v-if="variantResults">
      <!-- Winner callout -->
      <div class="winner-callout">
        <div class="winner-label">★ WINNER</div>
        <div class="winner-name">{{ variantResults.winner.variant_label }}</div>
        <div class="winner-hook">{{ formatHook(variantResults.winner.hook_type) }} hook</div>
        <div v-if="variantResults.runner_up_delta" class="winner-delta">
          +{{ pct(variantResults.runner_up_delta.reply_rate_diff) }} reply rate
          vs {{ variantResults.runner_up_delta.label }}
        </div>
      </div>

      <!-- Performance table -->
      <div class="report-section">
        <h4 class="section-title">Variant Performance</h4>
        <table class="results-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Variant</th>
              <th>Hook</th>
              <th>Open%</th>
              <th>Read%</th>
              <th>Reply%</th>
              <th>Fwd%</th>
              <th>Intent</th>
              <th>Score</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(v, idx) in variantResults.variants"
              :key="v.variant_label"
              :class="{ 'row-winner': idx === 0 }"
            >
              <td class="rank-num">{{ idx + 1 }}</td>
              <td class="variant-name-cell">
                <span v-if="idx === 0" class="star">★</span>
                {{ v.variant_label }}
              </td>
              <td class="hook-cell">{{ formatHook(v.hook_type) }}</td>
              <td>{{ pct(v.open_rate) }}</td>
              <td>{{ pct(v.read_rate) }}</td>
              <td class="reply-cell">{{ pct(v.reply_rate) }}</td>
              <td>{{ pct(v.forward_rate) }}</td>
              <td>{{ v.avg_intent_score.toFixed(2) }}</td>
              <td class="score-cell">{{ v.composite_score.toFixed(3) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Dropout funnel -->
      <div v-if="hasDropouts" class="report-section">
        <h4 class="section-title">Dropout Funnel — where readers disengaged</h4>
        <div class="dropout-grid">
          <div
            v-for="(points, label) in variantResults.dropouts"
            :key="label"
            class="dropout-variant"
          >
            <div class="dropout-variant-label">{{ label }}</div>
            <div
              v-for="dp in points"
              :key="dp.dropout_point"
              class="dropout-row"
            >
              <span class="dropout-point-label">{{ formatDropoutPoint(dp.dropout_point) }}</span>
              <div class="dropout-bar-wrap">
                <div
                  class="dropout-bar-fill"
                  :style="{ width: dropoutBarWidth(dp.count, points) + '%' }"
                ></div>
              </div>
              <span class="dropout-count">{{ dp.count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Hook-type ranking -->
      <div v-if="variantResults.hook_types.length > 1" class="report-section">
        <h4 class="section-title">Hook-Type Performance</h4>
        <div class="hook-ranking">
          <div
            v-for="(ht, idx) in variantResults.hook_types"
            :key="ht.hook_type"
            class="hook-row"
          >
            <span class="hook-rank">{{ idx + 1 }}</span>
            <span class="hook-name">{{ formatHook(ht.hook_type) }}</span>
            <span class="hook-stat">{{ pct(ht.avg_reply_rate) }} reply</span>
            <span class="hook-stat secondary">{{ pct(ht.avg_open_rate) }} open</span>
            <span class="hook-n">(n={{ ht.count }})</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'EmailVariantReport',
  props: {
    variantResults: { type: Object, default: null },
    loading:        { type: Boolean, default: false },
    error:          { type: String,  default: '' },
  },
  setup(props) {
    const hasDropouts = computed(() =>
      props.variantResults &&
      Object.keys(props.variantResults.dropouts || {}).length > 0
    )

    // Format a rate (0-1) as "xx.x%"
    const pct = (v) => (v == null ? '—' : (v * 100).toFixed(1) + '%')

    const HOOK_LABELS = {
      problem:      'Problem',
      timeline:     'Timeline',
      numbers:      'Numbers',
      social_proof: 'Social proof',
      curiosity:    'Curiosity',
    }
    const formatHook = (h) => HOOK_LABELS[h] || h || '—'

    const DROPOUT_LABELS = {
      subject_line: 'Subject line',
      opening:      'Opening',
      body:         'Body',
      cta:          'CTA',
      timing:       'Timing',
    }
    const formatDropoutPoint = (dp) => DROPOUT_LABELS[dp] || dp || '—'

    // Bar width relative to the highest count in that variant's dropout list
    const dropoutBarWidth = (count, points) => {
      const max = Math.max(...points.map((p) => p.count))
      return max > 0 ? Math.round((count / max) * 100) : 0
    }

    return { hasDropouts, pct, formatHook, formatDropoutPoint, dropoutBarWidth }
  },
}
</script>

<style scoped>
.variant-report {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Loading / empty / error */
.report-loading-row {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #6b6b82;
  font-size: 13px;
}

.report-error  { color: #f87171; font-size: 13px; }
.report-empty  { color: #4b4b60; font-size: 13px; }

.loading-ring.small {
  width: 16px;
  height: 16px;
  border: 2px solid #1e1e2e;
  border-top-color: #a78bfa;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Winner callout */
.winner-callout {
  background: linear-gradient(135deg, #1a1a2e 0%, #111118 100%);
  border: 1px solid #3d2b6b;
  border-radius: 10px;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.winner-label {
  font-size: 10px;
  color: #a78bfa;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-weight: 700;
}

.winner-name {
  font-size: 22px;
  font-weight: 700;
  color: #e4e4e9;
  margin-top: 2px;
}

.winner-hook {
  font-size: 13px;
  color: #6b6b82;
}

.winner-delta {
  font-size: 14px;
  color: #4ade80;
  font-weight: 600;
  margin-top: 6px;
}

/* Section header */
.report-section { display: flex; flex-direction: column; gap: 12px; }

.section-title {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #4b4b60;
  font-weight: 600;
  margin: 0;
}

/* Performance table */
.results-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.results-table th {
  text-align: left;
  padding: 6px 10px;
  color: #4b4b60;
  font-size: 11px;
  font-weight: 500;
  border-bottom: 1px solid #1e1e2e;
}

.results-table td {
  padding: 8px 10px;
  color: #a0a0b4;
  border-bottom: 1px solid #111118;
}

.results-table tr.row-winner td { color: #e4e4e9; background: #12121c; }
.results-table tr.row-winner .reply-cell { color: #a78bfa; font-weight: 600; }

.rank-num       { color: #4b4b60; width: 24px; }
.variant-name-cell { font-weight: 500; }
.hook-cell      { color: #6b6b82; }
.score-cell     { color: #a78bfa; font-weight: 600; }
.star           { color: #a78bfa; margin-right: 4px; }

/* Dropout funnel */
.dropout-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dropout-variant-label {
  font-size: 11px;
  font-weight: 600;
  color: #6b6b82;
  margin-bottom: 6px;
}

.dropout-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.dropout-point-label {
  font-size: 11px;
  color: #4b4b60;
  width: 80px;
  flex-shrink: 0;
}

.dropout-bar-wrap {
  flex: 1;
  height: 6px;
  background: #1e1e2e;
  border-radius: 3px;
  overflow: hidden;
}

.dropout-bar-fill {
  height: 100%;
  background: #7c3aed;
  border-radius: 3px;
  transition: width 0.4s ease;
}

.dropout-count {
  font-size: 11px;
  color: #6b6b82;
  width: 24px;
  text-align: right;
  flex-shrink: 0;
}

/* Hook-type ranking */
.hook-ranking { display: flex; flex-direction: column; gap: 6px; }

.hook-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
}

.hook-rank   { color: #4b4b60; width: 16px; flex-shrink: 0; }
.hook-name   { color: #e4e4e9; font-weight: 500; min-width: 90px; }
.hook-stat   { color: #a78bfa; }
.hook-stat.secondary { color: #6b6b82; }
.hook-n      { color: #4b4b60; font-size: 10px; }
</style>
