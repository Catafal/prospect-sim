"""
Email inbox variant test simulation runner.

Runs B2B decision-maker agents (HR Directors) against email copy variants
stored in email_variants.json in the simulation directory. Each simulation
tests one or more variants; results land in email_simulation.db which the
ReportAgent queries to rank variants by open/reply/intent score.

This script is launched by SimulationRunner as a subprocess:
    python run_email_inbox_simulation.py --config simulation_config.json
    python run_email_inbox_simulation.py --config simulation_config.json --max-rounds 5

Log structure:
    sim_xxx/
    ├── email_inbox/
    │   └── actions.jsonl     # Round/completion events (read by SimulationRunner monitor)
    ├── email_simulation.db   # EmailInboxPlatform SQLite DB (variant stats)
    └── simulation.log        # stdout/stderr captured by SimulationRunner
"""

import sys
import os
import argparse
import asyncio
import json
import logging
import signal
from datetime import datetime
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Path bootstrap — match run_parallel_simulation.py pattern
# ---------------------------------------------------------------------------
_scripts_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.abspath(os.path.join(_scripts_dir, ".."))
_project_root = os.path.abspath(os.path.join(_backend_dir, ".."))
sys.path.insert(0, _scripts_dir)
sys.path.insert(0, _backend_dir)

from dotenv import load_dotenv
_env_file = os.path.join(_project_root, ".env")
if os.path.exists(_env_file):
    load_dotenv(_env_file)
    print(f"Loaded env: {_env_file}")
else:
    _backend_env = os.path.join(_backend_dir, ".env")
    if os.path.exists(_backend_env):
        load_dotenv(_backend_env)
        print(f"Loaded env: {_backend_env}")

# ---------------------------------------------------------------------------
# Imports (after path / env setup)
# ---------------------------------------------------------------------------
try:
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType
    from wonderwall.social_agent.agent import SocialAgent
    from wonderwall.social_platform.channel import Channel
    from wonderwall.social_platform.config import UserInfo
    from wonderwall.simulations.email_inbox import email_inbox_simulation
    from wonderwall.simulations.email_inbox.platform import EmailInboxPlatform
except ImportError as e:
    print(f"[EmailInbox] Error: Missing dependency — {e}")
    print("Run: pip install -e ../wonderwall camel-ai")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------
_shutdown_requested = False


def _on_signal(signum, frame):
    """Set shutdown flag on SIGTERM/SIGINT so the loop exits cleanly."""
    global _shutdown_requested
    _shutdown_requested = True


signal.signal(signal.SIGTERM, _on_signal)
signal.signal(signal.SIGINT, _on_signal)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def init_logging():
    """Configure logging — silence verbose camel/wonderwall internals."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )
    for noisy in ["social.agent", "wonderwall.env", "table", "httpx", "httpcore",
                  "camel", "openai._base_client"]:
        logging.getLogger(noisy).setLevel(logging.CRITICAL)


def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_model(config: Dict[str, Any]):
    """Build the LLM model from env vars, falling back to config file values."""
    api_key = os.environ.get("LLM_API_KEY", "")
    base_url = os.environ.get("LLM_BASE_URL", "")
    model_name = os.environ.get("LLM_MODEL_NAME", "") or config.get("llm_model", "gpt-4o-mini")

    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("LLM_API_KEY not set. Add it to .env in project root.")
    if base_url:
        os.environ["OPENAI_API_BASE_URL"] = base_url

    print(f"[EmailInbox] Using model: {model_name}")
    return ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=model_name,
    )


def load_profiles(sim_dir: str) -> List[Dict[str, Any]]:
    """Load B2B agent profiles from email_inbox_profiles.json."""
    path = os.path.join(sim_dir, "email_inbox_profiles.json")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"email_inbox_profiles.json not found in {sim_dir}. "
            "Call POST /api/simulation/prepare first."
        )
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # reddit_profiles.json is a list; handle both formats
    if isinstance(data, dict):
        return list(data.values())
    return data


def load_variants(sim_dir: str) -> List[Dict[str, Any]]:
    """Load email copy variants from email_variants.json."""
    path = os.path.join(sim_dir, "email_variants.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"email_variants.json not found in {sim_dir}.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def profile_to_user_info(profile: Dict[str, Any]) -> UserInfo:
    """Convert a saved OasisAgentProfile dict to Wonderwall UserInfo.

    EmailInboxPromptBuilder reads from user_info.profile["other_info"], so we
    map the B2B fields (budget_authority, cold_email_skepticism, etc.) there.
    """
    other_info = {
        "user_profile": profile.get("persona") or profile.get("bio", "HR professional"),
        "budget_authority": profile.get("budget_authority", False),
        "cold_email_skepticism": float(profile.get("cold_email_skepticism", 0.6)),
        "inbox_habit": profile.get("inbox_habit", "batch_processor"),
        "pain_signal_sensitivity": profile.get("pain_signal_sensitivity") or {},
        "decision_style": profile.get("decision_style", "roi_driven"),
    }
    return UserInfo(
        user_name=profile.get("user_name", f"agent_{profile.get('user_id', 0)}"),
        name=profile.get("name", ""),
        description=profile.get("bio", ""),
        profile={"other_info": other_info},
    )


def write_event(log_file, event_type: str, **data):
    """Append a JSONL event to the action log for the SimulationRunner monitor."""
    entry = {"event_type": event_type, "timestamp": datetime.now().isoformat(), **data}
    log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
    log_file.flush()


# ---------------------------------------------------------------------------
# Main simulation coroutine
# ---------------------------------------------------------------------------

async def run_simulation(
    config: Dict[str, Any],
    sim_dir: str,
    max_rounds: Optional[int],
    model,
) -> None:
    """Core email inbox simulation loop.

    1. Loads profiles + variants from sim_dir.
    2. Creates EmailInboxPlatform (seeds variants into SQLite DB).
    3. Spawns SocialAgents with email_inbox_simulation SimulationConfig.
    4. Runs max_rounds rounds — all agents act concurrently via asyncio.gather.
    5. Writes round_end + simulation_end events for the monitor.
    """
    global _shutdown_requested

    profiles = load_profiles(sim_dir)
    variants = load_variants(sim_dir)
    total_rounds = max_rounds or config.get("time_config", {}).get("num_rounds", 8)

    print(f"[EmailInbox] agents={len(profiles)}, variants={len(variants)}, rounds={total_rounds}")

    # Ensure log directory exists
    log_dir = os.path.join(sim_dir, "email_inbox")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "actions.jsonl")
    log_file = open(log_path, "w", encoding="utf-8")

    # Shared channel between all agents and the platform
    channel = Channel()

    # Remove stale DB from a previous run attempt
    db_path = os.path.join(sim_dir, "email_simulation.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    # Start the platform message loop as a background task
    platform = EmailInboxPlatform(db_path=db_path, channel=channel, variants=variants)
    platform_task = asyncio.create_task(platform.running())

    # Build one SocialAgent per profile, wired to the email_inbox_simulation config
    agents: List[SocialAgent] = []
    for i, profile in enumerate(profiles):
        user_info = profile_to_user_info(profile)
        agent = SocialAgent(
            agent_id=i,
            user_info=user_info,
            channel=channel,
            model=model,
            simulation=email_inbox_simulation,
        )
        agents.append(agent)

    # Sign up all agents on the platform (creates user rows in DB)
    signup_tasks = [
        agent.env.action.sign_up(
            profiles[i].get("user_name", f"agent_{i}"),
            profiles[i].get("name", f"Agent {i}"),
            profiles[i].get("bio", "HR professional"),
        )
        for i, agent in enumerate(agents)
    ]
    await asyncio.gather(*signup_tasks)
    print(f"[EmailInbox] {len(agents)} agents signed up and ready")

    # ---- Round loop ----
    total_actions = 0
    for round_num in range(total_rounds):
        if _shutdown_requested:
            print(f"[EmailInbox] Shutdown signal — stopping at round {round_num + 1}")
            break

        round_start = datetime.now()
        print(f"[EmailInbox] Round {round_num + 1}/{total_rounds}")

        # All agents act simultaneously in this round
        round_results = await asyncio.gather(
            *[agent.perform_action_by_llm() for agent in agents],
            return_exceptions=True,
        )

        agent_errors = [r for r in round_results if isinstance(r, Exception)]
        round_actions = len(round_results) - len(agent_errors)
        for err in agent_errors:
            print(f"[EmailInbox] Agent error round {round_num + 1}: {err}")

        total_actions += round_actions
        elapsed_ms = int((datetime.now() - round_start).total_seconds() * 1000)

        # Write round_end so SimulationRunner.current_round tracks progress in the UI
        write_event(log_file, "round_end",
                    round=round_num + 1,
                    simulated_hours=round_num + 1,
                    actions_count=round_actions,
                    elapsed_ms=elapsed_ms)

    # ---- Shutdown platform ----
    await channel.write_to_receive_queue((0, None, "exit"))
    try:
        await asyncio.wait_for(platform_task, timeout=5.0)
    except asyncio.TimeoutError:
        platform_task.cancel()

    # Write simulation_end — monitor uses this to mark the simulation COMPLETED
    write_event(log_file, "simulation_end",
                total_rounds=total_rounds,
                total_actions=total_actions,
                agents=len(agents),
                variants=len(variants))
    log_file.close()

    print(f"[EmailInbox] Done. rounds={total_rounds}, actions={total_actions}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Email inbox B2B variant simulation")
    parser.add_argument("--config", required=True, help="Path to simulation_config.json")
    parser.add_argument("--max-rounds", type=int, default=None,
                        help="Override number of rounds (default: from config)")
    args = parser.parse_args()

    config_path = os.path.abspath(args.config)
    sim_dir = os.path.dirname(config_path)

    init_logging()
    config = load_config(config_path)
    model = create_model(config)

    print(f"[EmailInbox] Simulation dir: {sim_dir}")
    asyncio.run(run_simulation(config, sim_dir, args.max_rounds, model))


if __name__ == "__main__":
    main()
