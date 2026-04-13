"""LinkedIn outreach simulation for B2B connection request copy variant testing.

Tests LinkedIn connection note + opening message copy variants against synthetic
B2B decision-maker personas before sending to real prospects.

Usage::

    from wonderwall.simulations.linkedin_outreach import linkedin_outreach_simulation

    env = oasis.make(
        agent_graph=agent_graph,
        simulation=linkedin_outreach_simulation,
        database_path="./data/linkedin.db",
    )
"""
from wonderwall.simulations.base import SimulationConfig
from wonderwall.simulations.linkedin_outreach.actions import LinkedInOutreachAction
from wonderwall.simulations.linkedin_outreach.environment import LinkedInOutreachEnvironment
from wonderwall.simulations.linkedin_outreach.platform import LinkedInOutreachPlatform
from wonderwall.simulations.linkedin_outreach.prompts import LinkedInOutreachPromptBuilder

linkedin_outreach_simulation = SimulationConfig(
    name="linkedin_outreach",
    platform_cls=LinkedInOutreachPlatform,
    action_cls=LinkedInOutreachAction,
    environment_cls=LinkedInOutreachEnvironment,
    prompt_builder=LinkedInOutreachPromptBuilder(),
    default_actions=[
        "accept_connection",
        "view_profile",
        "reply_message",
        "ignore_request",
        "check_profile",
        "do_nothing",
    ],
    # Variants injected at runtime via platform_kwargs (same pattern as email_inbox)
    platform_kwargs={},
)

__all__ = [
    "linkedin_outreach_simulation",
    "LinkedInOutreachPlatform",
    "LinkedInOutreachAction",
    "LinkedInOutreachEnvironment",
    "LinkedInOutreachPromptBuilder",
]
