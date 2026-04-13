"""LinkedIn outreach agent actions — LLM-callable tools for B2B decision-maker personas.

Each public async method is auto-discovered as an LLM tool via
BaseAction.get_openai_function_list(). Docstrings become the tool descriptions
the LLM sees — they must guide realistic LinkedIn B2B behavior.

LinkedIn cold outreach reality:
  - B2B decision-makers receive 20-50 connection requests per week
  - Most are ignored without reading the note (< 5 seconds of attention)
  - Personalized notes with a clear, credible reason perform best
  - Acceptance rate for cold outreach: ~15-30% for well-targeted messages
  - Reply rate after acceptance: ~20-40% depending on opening message quality
"""
from __future__ import annotations

from wonderwall.simulations.base import BaseAction


class LinkedInOutreachAction(BaseAction):
    """Actions available to a B2B decision-maker agent in the LinkedIn outreach simulation."""

    async def accept_connection(self, variant_id: int):
        """Accept a LinkedIn connection request — you've decided the sender is worth connecting with.

        Call this ONLY when the connection note passes ALL of:
        1. The note is personalised — mentions something specific about your role, company, or posts
        2. The sender's apparent profile/title is credible and relevant to your function
        3. The reason for connecting is clear and non-generic
        4. The note doesn't immediately ask for a call or demo

        As a busy B2B decision-maker, you accept maybe 15-30% of cold connection requests.
        Most notes are generic templates — reject or ignore those.

        Args:
            variant_id (int): The ID of the connection request variant to accept.

        Returns:
            dict: Contains the opening_message and approach_type you'll read next.
        """
        return await self.perform_action(variant_id, "accept_connection")

    async def view_profile(self, variant_id: int):
        """Visit the sender's LinkedIn profile to evaluate them before deciding.

        Call this when the connection note made you curious but you're not ready
        to accept yet. You check: job title, current company, past experience,
        mutual connections. This is due diligence — not commitment.

        Profile check triggers:
        - The note mentions a specific shared context you want to verify
        - The sender's title suggests they could be relevant (VP, Director, etc.)
        - You want to see mutual connections before deciding

        Args:
            variant_id (int): The ID of the variant whose sender you're researching.

        Returns:
            dict: Confirmation that you've viewed the sender's profile.
        """
        return await self.perform_action(variant_id, "view_profile")

    async def reply_message(self, variant_id: int, notes: str = ""):
        """Reply to the opening message — you're genuinely interested in the conversation.

        Call this ONLY after accepting the connection AND finding the opening message
        relevant. The reply means you're open to a conversation, not just network-building.

        For a reply to happen:
        1. You accepted the connection (note was personalised and credible)
        2. The opening message addressed a real current pain or opportunity
        3. The ask is specific and low-commitment (not 'book a 30-min call')
        4. The timing is right for you (budget season, hiring push, etc.)

        As a B2B decision-maker, you reply to maybe 20-40% of accepted connections.

        Args:
            variant_id (int): The ID of the variant you're replying to.
            notes (str): Brief reason for your reply or what resonated with you.

        Returns:
            dict: Confirmation of your reply.
        """
        return await self.perform_action((variant_id, notes), "reply_message")

    async def ignore_request(self, variant_id: int, dropout_point: str = "connection_note"):
        """Ignore or decline the connection request — this is your default for most cold outreach.

        Call this when the connection request doesn't meet your bar. Be specific
        about WHERE you disengaged — this is the most valuable feedback signal.

        dropout_point options:
        - 'connection_note' — the note was generic/templated/no note at all
        - 'pending'         — left it in pending limbo (overwhelmed, will never act)
        - 'no_context'      — blank connection request, ignored as irrelevant spam

        B2B decision-makers ignore 70-85% of cold connection requests.
        This is your default action for requests that don't stand out.

        Args:
            variant_id (int): The ID of the variant you're ignoring.
            dropout_point (str): Where you stopped engaging. Be specific.

        Returns:
            dict: Confirmation with dropout point recorded.
        """
        return await self.perform_action((variant_id, dropout_point), "ignore_request")

    async def check_profile(self, variant_id: int):
        """Quickly glance at the sender's profile — a passive, uncommitted action.

        Use this for a brief hover/click on the sender's name without fully reading
        their profile. It signals mild curiosity but no active evaluation.
        Weaker signal than view_profile.

        This typically happens when:
        - You noticed a connection request in your notifications but didn't click through
        - The sender's name appeared in 'People You May Know' while you were doing something else
        - You did a cursory check but weren't engaged enough to really read

        Args:
            variant_id (int): The ID of the variant whose sender you glanced at.

        Returns:
            dict: Confirmation of the quick check.
        """
        return await self.perform_action(variant_id, "check_profile")
