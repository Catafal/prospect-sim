<template>
  <div class="action-feed">
    <div class="feed-header">
      <span class="feed-title">Live Agent Feed</span>
      <span class="feed-count" v-if="events.length">{{ events.length }} actions</span>
    </div>

    <!-- Empty states -->
    <div v-if="events.length === 0 && !active" class="feed-empty">
      Waiting for simulation to start…
    </div>
    <div v-if="events.length === 0 && active" class="feed-empty active">
      <span class="pulse-dot"></span>
      Running — waiting for first agent actions…
    </div>

    <!-- Event list (newest first, capped at 50) -->
    <div v-if="events.length > 0" class="feed-list">
      <div
        v-for="ev in events"
        :key="ev.id"
        class="feed-item"
        :class="ev.event_type"
      >
        <span class="ev-emoji">{{ actionEmoji(ev.event_type) }}</span>
        <span class="ev-agent">{{ ev.agent_name }}</span>
        <span class="ev-action">{{ actionLabel(ev.event_type) }}</span>
        <span class="ev-variant">{{ ev.variant_label }}</span>
        <span class="ev-round">R{{ ev.round_num }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, onUnmounted } from 'vue'

export default {
  name: 'EmailActionFeed',
  props: {
    simulationId: { type: String,  required: true },
    active:       { type: Boolean, default: false },
  },
  setup(props) {
    const events = ref([])
    const nextId = ref(0)
    let pollTimer = null

    const ACTION_EMOJIS = {
      open_email: '📬',
      read_email: '👁',
      reply:      '↩',
      forward:    '↗',
      archive:    '📥',
      do_nothing: '—',
    }
    const ACTION_LABELS = {
      open_email: 'opened',
      read_email: 'read',
      reply:      'replied to',
      forward:    'forwarded',
      archive:    'archived',
      do_nothing: 'skipped',
    }

    const actionEmoji = (type) => ACTION_EMOJIS[type] || '•'
    const actionLabel = (type) => ACTION_LABELS[type] || type

    async function fetchEvents() {
      if (!props.simulationId) return
      try {
        const resp = await fetch(
          `/api/simulation/${props.simulationId}/inbox-events?since_id=${nextId.value}`
        )
        const data = await resp.json()
        if (!data.success || !data.data?.events?.length) return

        // Prepend new events (newest first), cap at 50
        const newEvents = [...data.data.events].reverse()
        events.value = [...newEvents, ...events.value].slice(0, 50)
        nextId.value = data.data.next_id
      } catch (_) {
        // Non-fatal — keep polling
      }
    }

    function startPolling() {
      if (pollTimer) return   // Avoid duplicate timers
      fetchEvents()           // Immediate fetch on start
      pollTimer = setInterval(fetchEvents, 3000)
    }

    function stopPolling() {
      if (pollTimer) {
        clearInterval(pollTimer)
        pollTimer = null
      }
    }

    // React to active prop changes — mirrors Step3Simulation.vue polling pattern
    watch(() => props.active, (isActive) => {
      if (isActive) startPolling()
      else stopPolling()
    }, { immediate: true })

    // Final fetch when simulation ends so we capture the last round's events
    watch(() => props.active, (isActive, wasActive) => {
      if (!isActive && wasActive) fetchEvents()
    })

    onUnmounted(stopPolling)

    return { events, actionEmoji, actionLabel }
  },
}
</script>

<style scoped>
.action-feed {
  background: #0d0d14;
  border: 1px solid #1e1e2e;
  border-radius: 8px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 280px;
  overflow: hidden;
}

.feed-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.feed-title {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #4b4b60;
  font-weight: 600;
}

.feed-count {
  font-size: 10px;
  color: #4b4b60;
}

/* Empty states */
.feed-empty {
  color: #4b4b60;
  font-size: 12px;
  padding: 8px 0;
}

.feed-empty.active {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #6b6b82;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  background: #a78bfa;
  border-radius: 50%;
  flex-shrink: 0;
  animation: pulse 1.4s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.4; transform: scale(0.7); }
}

/* Event list */
.feed-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
  max-height: 220px;
}

.feed-list::-webkit-scrollbar { width: 4px; }
.feed-list::-webkit-scrollbar-track  { background: transparent; }
.feed-list::-webkit-scrollbar-thumb  { background: #2e2e42; border-radius: 2px; }

.feed-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  padding: 3px 0;
  border-bottom: 1px solid #0f0f18;
  color: #6b6b82;
}

/* Highlight engaged actions */
.feed-item.reply   { color: #a78bfa; }
.feed-item.forward { color: #60a5fa; }

.ev-emoji   { width: 16px; flex-shrink: 0; }
.ev-agent   { color: #a0a0b4; font-weight: 500; min-width: 90px; max-width: 110px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ev-action  { color: #6b6b82; min-width: 60px; }
.ev-variant { color: #4b4b60; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ev-round   { color: #2e2e42; font-size: 10px; flex-shrink: 0; }
</style>
