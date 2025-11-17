from typing import List
from google.adk.agents import (
    LlmAgent,
    BaseAgent,
    LoopAgent,
    SequentialAgent,
    callback_context,
)
import os
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from google.adk.models.lite_llm import LiteLlm
from dude.models import Plan

prompt = (
    """
You are an expert project manager agent. your primary directive is in two parts: 
1. to translate the user's overarching goal, provided above, into a series of actionable steps for delegation to agents. 
2. to research the current state of the project to fill in any information required for a full plan.

Guidelines:
- Each sub-task should be atomic and testable
- Provide 2-5 sub-tasks for typical features
- Prioritize based on dependencies
- Consider testing and review needs

Return ONLY valid JSON.

use the filesystem tools provided for the information gathering, or ask the user for clarification. do not make any assumptions.

think carefully, consider all alternatives.
return final output in the format:
%s

"""
    % Plan.model_json_schema()
)


planner = LlmAgent(
    name="planner",
    model=LiteLlm(model="openrouter/moonshotai/kimi-k2-thinking"),
    instruction=prompt,
    output_key="planner_output",
    tools=[
        MCPToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="npx",
                    args=[
                        "-y",  # Argument for npx to auto-confirm install
                        "@modelcontextprotocol/server-filesystem",
                        os.path.abspath(os.getcwd()),
                    ],
                ),
                timeout=60,
            ),
        ),
        MCPToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="uvx",
                    args=["mcp-server-fetch"],
                ),
                timeout=60,
            ),
        ),
    ],
)
