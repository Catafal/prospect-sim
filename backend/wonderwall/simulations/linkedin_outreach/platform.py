"""LinkedIn outreach simulation platform.

Handles B2B LinkedIn connection request + opening message variant testing.
Each agent receives all connection request variants and decides how to interact:
accept, view the sender's profile, reply, ignore, or check the profile without committing.

State is tracked in SQLite — mirrors email inbox platform pattern exactly:
  - linkedin_variant      — static copy variants (seeded once at init)
  - linkedin_outreach_state — cumulative per-agent-per-variant flags
  - linkedin_event          — append-only action log (for live feed + reporting)

Follows the same BasePlatform pattern as EmailInboxPlatform.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List

from wonderwall.clock.clock import Clock
from wonderwall.simulations.base import BasePlatform

logger = logging.getLogger(__name__)


class LinkedInOutreachPlatform(BasePlatform):
    """B2B LinkedIn outreach platform for connection request copy variant testing.

    Agents represent B2B decision-makers (heads of department, directors, VPs)
    who receive connection requests paired with an opening message. Each round,
    agents decide how to interact with the pending requests.

    State lives in SQLite: acceptance, profile views, replies, and dropout points.
    """

    required_schemas = ["linkedin.sql"]

    def __init__(
        self,
        db_path: str,
        channel: Any = None,
        sandbox_clock: Clock | None = None,
        start_time: datetime | None = None,
        variants: List[Dict] | None = None,
    ):
        # Store variants before super().__init__ so _seed_variants can be called
        # after the DB schema is initialised by BasePlatform.
        self._pending_variants = variants or []
        super().__init__(
            db_path=db_path,
            channel=channel,
            sandbox_clock=sandbox_clock,
            start_time=start_time,
        )
        # Seed variants immediately after schema init — agents need them in round 1
        if self._pending_variants:
            self._seed_variants(self._pending_variants)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _seed_variants(self, variants: List[Dict]) -> None:
        """Insert LinkedIn copy variants into the DB at simulation start.

        Called once during __init__. Uses INSERT OR IGNORE so re-runs are safe.
        Validates connection_note length at seed time to catch violations early.
        """
        current_time = self.get_current_time()
        for v in variants:
            note = v.get("connection_note", "")
            if len(note) > 300:
                # Truncate and warn — hard LinkedIn limit; agents should never see invalid copy
                logger.warning(
                    f"[LinkedInOutreach] connection_note for '{v.get('variant_label')}' "
                    f"exceeds 300 chars ({len(note)}), truncating."
                )
                note = note[:300]

            self._execute_db_command(
                "INSERT OR IGNORE INTO linkedin_variant "
                "(variant_id, variant_label, connection_note, opening_message, approach_type, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    v.get("variant_id", v.get("id", 0)),
                    v.get("variant_label", v.get("label", f"Variant {v.get('id', 0)}")),
                    note,
                    v.get("opening_message", ""),
                    v.get("approach_type", "unknown"),
                    current_time,
                ),
                commit=False,
            )
        self.db.commit()
        logger.info(f"[LinkedInOutreach] Seeded {len(variants)} LinkedIn variants into DB")

    # ------------------------------------------------------------------
    # Platform actions (dispatched via getattr by BasePlatform.running)
    # ------------------------------------------------------------------

    async def accept_connection(self, agent_id: int, message: Any) -> Dict:
        """Agent accepts the connection request — primary positive signal.

        Accepting means the agent found the connection note compelling enough
        to let the sender into their network and read the opening message.
        """
        variant_id = int(message) if message is not None else 0
        current_time = self.get_current_time()

        self._execute_db_command(
            "INSERT INTO linkedin_outreach_state "
            "(agent_id, variant_id, accepted_connection, last_round, created_at) "
            "VALUES (?, ?, 1, ?, ?) "
            "ON CONFLICT(agent_id, variant_id) DO UPDATE SET "
            "accepted_connection=1, last_round=excluded.last_round",
            (agent_id, variant_id, 0, current_time),
            commit=True,
        )
        self._record_trace(agent_id, "accept_connection", {"variant_id": variant_id}, current_time)
        self._log_linkedin_event(agent_id, variant_id, "accept_connection", None, None, current_time)

        # Return the opening message content so the agent can read it next round
        row = self._execute_db_command(
            "SELECT variant_label, opening_message, approach_type FROM linkedin_variant WHERE variant_id=?",
            (variant_id,)
        ).fetchone()

        if row:
            return {"success": True, "variant_id": variant_id, "variant_label": row[0],
                    "opening_message": row[1], "approach_type": row[2]}
        return {"success": False, "error": f"Variant {variant_id} not found"}

    async def view_profile(self, agent_id: int, message: Any) -> Dict:
        """Agent visits the sender's LinkedIn profile before deciding to accept.

        Profile views indicate interest but not commitment — agent is doing
        their due diligence (checking title, company, mutual connections).
        """
        variant_id = int(message) if message is not None else 0
        current_time = self.get_current_time()

        self._execute_db_command(
            "INSERT INTO linkedin_outreach_state "
            "(agent_id, variant_id, viewed_profile, last_round, created_at) "
            "VALUES (?, ?, 1, ?, ?) "
            "ON CONFLICT(agent_id, variant_id) DO UPDATE SET "
            "viewed_profile=1, last_round=excluded.last_round",
            (agent_id, variant_id, 0, current_time),
            commit=True,
        )
        self._record_trace(agent_id, "view_profile", {"variant_id": variant_id}, current_time)
        self._log_linkedin_event(agent_id, variant_id, "view_profile", None, None, current_time)

        return {"success": True, "variant_id": variant_id, "action": "viewed_sender_profile"}

    async def reply_message(self, agent_id: int, message: Any) -> Dict:
        """Agent replies to the opening message — strongest success signal.

        Replying means the agent accepted the connection AND found the opening
        message relevant enough to engage in a conversation.
        """
        # message can be (variant_id, reply_notes) or just variant_id
        if isinstance(message, (list, tuple)) and len(message) >= 1:
            variant_id = int(message[0])
            notes = str(message[1]) if len(message) > 1 else None
        else:
            variant_id = int(message) if message is not None else 0
            notes = None

        current_time = self.get_current_time()

        # Reply implies acceptance (you can't reply without accepting first)
        self._execute_db_command(
            "INSERT INTO linkedin_outreach_state "
            "(agent_id, variant_id, accepted_connection, replied, last_round, created_at) "
            "VALUES (?, ?, 1, 1, ?, ?) "
            "ON CONFLICT(agent_id, variant_id) DO UPDATE SET "
            "accepted_connection=1, replied=1, last_round=excluded.last_round",
            (agent_id, variant_id, 0, current_time),
            commit=True,
        )
        self._record_trace(agent_id, "reply_message", {"variant_id": variant_id, "notes": notes}, current_time)
        self._log_linkedin_event(agent_id, variant_id, "reply_message", None, notes, current_time)

        return {"success": True, "variant_id": variant_id, "action": "replied_to_opening"}

    async def ignore_request(self, agent_id: int, message: Any) -> Dict:
        """Agent ignores or declines the connection request.

        This is the default outcome for most cold LinkedIn requests.
        dropout_point tells us WHERE the agent lost interest:
          - 'connection_note' — declined based on the note alone
          - 'pending'         — left it pending (passive ignore, no decision)
          - 'no_context'      — no note at all, connection ignored as spam
        """
        if isinstance(message, (list, tuple)) and len(message) >= 1:
            variant_id = int(message[0])
            dropout_point = str(message[1]) if len(message) > 1 else "connection_note"
        else:
            variant_id = int(message) if message is not None else 0
            dropout_point = "connection_note"

        current_time = self.get_current_time()

        # dropout_point is set only once — first ignore decision wins
        self._execute_db_command(
            "INSERT INTO linkedin_outreach_state "
            "(agent_id, variant_id, ignored, dropout_point, last_round, created_at) "
            "VALUES (?, ?, 1, ?, ?, ?) "
            "ON CONFLICT(agent_id, variant_id) DO UPDATE SET "
            "ignored=1, "
            "dropout_point=CASE WHEN dropout_point IS NULL THEN excluded.dropout_point ELSE dropout_point END, "
            "last_round=excluded.last_round",
            (agent_id, variant_id, dropout_point, 0, current_time),
            commit=True,
        )
        self._record_trace(agent_id, "ignore_request", {"variant_id": variant_id, "dropout_point": dropout_point}, current_time)
        self._log_linkedin_event(agent_id, variant_id, "ignore_request", dropout_point, None, current_time)

        return {"success": True, "variant_id": variant_id, "dropout_point": dropout_point}

    async def check_profile(self, agent_id: int, message: Any) -> Dict:
        """Agent glances at the sender's profile without committing to a decision.

        Softer than view_profile — represents a quick hover/click, not a
        deliberate research action. Sets viewed_profile=1 as a side effect.
        """
        variant_id = int(message) if message is not None else 0
        current_time = self.get_current_time()

        self._execute_db_command(
            "INSERT INTO linkedin_outreach_state "
            "(agent_id, variant_id, viewed_profile, last_round, created_at) "
            "VALUES (?, ?, 1, ?, ?) "
            "ON CONFLICT(agent_id, variant_id) DO UPDATE SET "
            "viewed_profile=1, last_round=excluded.last_round",
            (agent_id, variant_id, 0, current_time),
            commit=True,
        )
        self._record_trace(agent_id, "check_profile", {"variant_id": variant_id}, current_time)
        self._log_linkedin_event(agent_id, variant_id, "check_profile", None, None, current_time)

        return {"success": True, "variant_id": variant_id, "action": "checked_sender_profile"}

    # ------------------------------------------------------------------
    # Query helpers used by LinkedInOutreachEnvironment
    # ------------------------------------------------------------------

    async def get_connection_requests(self, agent_id: int) -> Dict:
        """Return all variants with current acceptance/view/reply status for agent."""
        rows = self._execute_db_command(
            "SELECT v.variant_id, v.variant_label, v.connection_note, v.approach_type, "
            "COALESCE(s.accepted_connection, 0), COALESCE(s.viewed_profile, 0), "
            "COALESCE(s.replied, 0), COALESCE(s.ignored, 0), s.dropout_point "
            "FROM linkedin_variant v "
            "LEFT JOIN linkedin_outreach_state s "
            "ON v.variant_id = s.variant_id AND s.agent_id = ? "
            "ORDER BY v.variant_id",
            (agent_id,)
        ).fetchall()

        return {
            "success": True,
            "requests": [
                {
                    "variant_id": row[0],
                    "variant_label": row[1],
                    "connection_note": row[2],
                    "approach_type": row[3],
                    "accepted": bool(row[4]),
                    "viewed_profile": bool(row[5]),
                    "replied": bool(row[6]),
                    "ignored": bool(row[7]),
                    "dropout_point": row[8],
                }
                for row in rows
            ]
        }

    # ------------------------------------------------------------------
    # Report data helpers — called by API after simulation completes
    # ------------------------------------------------------------------

    def get_variant_summary(self) -> List[Dict]:
        """Aggregate stats per variant across all agents — for report generation.

        Returns accept/view/reply rates and composite score (reply×3 + accept×2 + view).
        """
        rows = self._execute_db_command(
            "SELECT "
            "  v.variant_id, v.variant_label, v.approach_type, "
            "  COUNT(DISTINCT s.agent_id) as total_agents, "
            "  SUM(s.accepted_connection) as total_accepts, "
            "  SUM(s.viewed_profile) as total_views, "
            "  SUM(s.replied) as total_replies "
            "FROM linkedin_variant v "
            "LEFT JOIN linkedin_outreach_state s ON v.variant_id = s.variant_id "
            "GROUP BY v.variant_id "
            "ORDER BY total_replies DESC, total_accepts DESC",
        ).fetchall()

        return [
            {
                "variant_id": row[0],
                "variant_label": row[1],
                "approach_type": row[2],
                "total_agents": row[3] or 0,
                "total_accepts": row[4] or 0,
                "total_views": row[5] or 0,
                "total_replies": row[6] or 0,
                "accept_rate": round((row[4] or 0) / max(row[3] or 1, 1), 3),
                "view_rate": round((row[5] or 0) / max(row[3] or 1, 1), 3),
                "reply_rate": round((row[6] or 0) / max(row[3] or 1, 1), 3),
            }
            for row in rows
        ]

    def get_dropout_breakdown(self) -> Dict[str, List[Dict]]:
        """Per-variant dropout point distribution — where agents stopped engaging."""
        rows = self._execute_db_command(
            "SELECT v.variant_label, s.dropout_point, COUNT(*) as count "
            "FROM linkedin_outreach_state s "
            "JOIN linkedin_variant v ON s.variant_id = v.variant_id "
            "WHERE s.dropout_point IS NOT NULL "
            "GROUP BY v.variant_id, s.dropout_point "
            "ORDER BY v.variant_id, count DESC"
        ).fetchall()

        result: Dict[str, List[Dict]] = {}
        for row in rows:
            label = row[0]
            if label not in result:
                result[label] = []
            result[label].append({"dropout_point": row[1], "count": row[2]})
        return result

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------

    def _log_linkedin_event(
        self,
        agent_id: int,
        variant_id: int,
        event_type: str,
        dropout_point: str | None,
        notes: str | None,
        timestamp: str,
    ) -> None:
        """Append a row to the linkedin_event log.

        The event log is the source of truth for the live feed API and the
        progress counter the SimulationRunner monitor reads from JSONL.
        """
        row = self._execute_db_command(
            "SELECT last_round FROM linkedin_outreach_state WHERE agent_id=? AND variant_id=?",
            (agent_id, variant_id)
        ).fetchone()
        round_num = row[0] if row else 0

        self._execute_db_command(
            "INSERT INTO linkedin_event "
            "(agent_id, variant_id, round_num, event_type, dropout_point, notes, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (agent_id, variant_id, round_num, event_type, dropout_point, notes, timestamp),
            commit=True,
        )
