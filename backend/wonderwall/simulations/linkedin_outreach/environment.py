"""LinkedIn outreach agent environment — what the B2B agent observes each round.

Converts the platform's connection request state into a text prompt the agent's
LLM receives. The agent sees all pending requests, their current status
(pending / accepted / ignored / replied), and can decide what to do next.
"""
from __future__ import annotations

from wonderwall.simulations.base import BaseEnvironment


class LinkedInOutreachEnvironment(BaseEnvironment):
    """Converts connection request state into the observation prompt for B2B agents."""

    async def to_text_prompt(self) -> str:
        # Fetch the agent's current connection request state from the platform
        data = await self.action.perform_action(
            self.action.agent_id, "get_connection_requests"
        )

        parts = []

        if data.get("success") and data.get("requests"):
            parts.append("YOUR LINKEDIN CONNECTION REQUESTS — PENDING & RECENT:")
            parts.append("")

            for req in data["requests"]:
                # Build a clear status label for this variant
                if req["replied"]:
                    status = "✓ REPLIED"
                elif req["accepted"]:
                    status = "✓ ACCEPTED — opening message received"
                elif req["ignored"]:
                    dropout = req.get("dropout_point") or "unknown"
                    status = f"✗ IGNORED [dropped at: {dropout}]"
                elif req["viewed_profile"]:
                    status = "PROFILE VIEWED — not yet decided"
                else:
                    status = "PENDING — not yet reviewed"

                parts.append(
                    f"  [{req['variant_id']}] {req['variant_label']}\n"
                    f"      Approach: {req['approach_type']} | Status: {status}\n"
                    f"      Connection note: \"{req['connection_note']}\""
                )
                parts.append("")
        else:
            parts.append("No connection requests in your LinkedIn inbox yet.")
            parts.append("")

        # Cross-platform context (e.g. from social media simulation rounds, if any)
        if self.extra_observation_context:
            parts.append(f"CONTEXT FROM OTHER CHANNELS:\n{self.extra_observation_context}")
            parts.append("")

        parts.append("DECIDE how to interact with your pending connection requests this round:")
        parts.append("  - accept_connection(variant_id) — accept the request and receive the opening message")
        parts.append("  - view_profile(variant_id)     — check the sender's profile before deciding")
        parts.append("  - reply_message(variant_id, notes) — reply to an accepted connection's opening message")
        parts.append("  - ignore_request(variant_id, dropout_point) — decline or ignore the request")
        parts.append("  - check_profile(variant_id)    — quick glance at the sender (passive, uncommitted)")
        parts.append("  - do_nothing()                 — no action this round (busy, distracted, etc.)")
        parts.append("")
        parts.append(
            "You receive many cold connection requests per week. Be realistic — most will be ignored. "
            "Only accept if the note is genuinely personalised and the sender is credible."
        )

        return "\n".join(parts)
