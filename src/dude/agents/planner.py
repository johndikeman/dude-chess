from typing import List
from google.adk.agents import (
    LlmAgent,
    BaseAgent,
    LoopAgent,
    SequentialAgent,
    callback_context,
)
from google.adk.models.lite_llm import LiteLlm
from dude.models import Plan

prompt = """
You are an expert project manager agent. your primary directive is in two parts: 
1. to translate the user's overarching goal into a series of actionable steps for delegation to agents. 
2. to research the current state of the project to fill in any information required for a full plan.

use the filesystem tools provided for the information gathering, or ask the user for clarification. do not make any assumptions.

here is some static information about the project provided by the user:
{dudehints}

here is your goal:
{planner_goal}

think carefully, consider all alternatives.
return final output in the format:
%s
""".format(
    Plan.schema_json()
)

planner = LlmAgent(
    name="planner",
    model=LiteLlm(model="openrouter/moonshotai/kimi-k2-thinking"),
    instruction=prompt,
    output_key="planner_output",
)
