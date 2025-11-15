from dude.agents.orchestrator import Orchestrator
from dude.agents import planner, coder
import os

# Configure with environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")

# Set environment for LiteLLM
os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY
os.environ["OPENROUTER_API_BASE"] = OPENROUTER_BASE_URL

root_agent = Orchestrator(
    name="orchestrator", planner_agent=planner, coder_agent=coder, tester_agent=coder
)
