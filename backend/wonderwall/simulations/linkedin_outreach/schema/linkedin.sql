-- LinkedIn outreach simulation schema
-- Tracks connection request + opening message variants and per-agent state.
-- Mirrors email inbox schema pattern: one static variants table, one cumulative
-- state table, one append-only event log.

-- LinkedIn copy variants under test (connection_note + opening_message pairs)
CREATE TABLE IF NOT EXISTS linkedin_variant (
    variant_id      INTEGER PRIMARY KEY,
    variant_label   TEXT NOT NULL,          -- e.g. "Variant A — Personalized"
    connection_note TEXT NOT NULL,          -- ≤300 chars (LinkedIn hard limit)
    opening_message TEXT NOT NULL,          -- First message after connection accepted
    approach_type   TEXT DEFAULT 'unknown', -- personalized | value_prop | mutual_interest | direct | question_based
    created_at      TEXT NOT NULL
);

-- Per-agent state per variant across all rounds
-- One row per (agent_id, variant_id) — updated in place as rounds progress.
-- Flags are cumulative: set to 1 once triggered, never reversed.
CREATE TABLE IF NOT EXISTS linkedin_outreach_state (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id            INTEGER NOT NULL,
    variant_id          INTEGER NOT NULL,
    -- Funnel flags (1 = action taken, 0 = not yet)
    accepted_connection INTEGER NOT NULL DEFAULT 0,
    viewed_profile      INTEGER NOT NULL DEFAULT 0,  -- visited sender's profile before deciding
    replied             INTEGER NOT NULL DEFAULT 0,  -- replied to opening message
    ignored             INTEGER NOT NULL DEFAULT 0,  -- declined / ignored the request
    -- Where the agent dropped off (NULL = still in play or completed positively)
    dropout_point       TEXT, -- 'connection_note' | 'pending' | 'no_context' | NULL
    last_round          INTEGER NOT NULL DEFAULT 0,
    created_at          TEXT NOT NULL,
    UNIQUE(agent_id, variant_id)
);

-- Append-only event log — every interaction action logged here for live feed + reporting
CREATE TABLE IF NOT EXISTS linkedin_event (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id      INTEGER NOT NULL,
    variant_id    INTEGER NOT NULL,
    round_num     INTEGER NOT NULL,
    -- Action taken: accept_connection | view_profile | reply_message | ignore_request | check_profile
    event_type    TEXT NOT NULL,
    dropout_point TEXT,
    notes         TEXT,
    created_at    TEXT NOT NULL
);
