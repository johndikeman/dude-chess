import logging
from typing import AsyncGenerator
from typing_extensions import override

from google.adk.agents import (
    LlmAgent,
    BaseAgent,
    LoopAgent,
    SequentialAgent,
    callback_context,
)
from google.adk.agents.invocation_context import InvocationContext
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.events import Event

from pydantic import BaseModel, Field, ValidateAs, ValidationError

import logging
from dude.models import Plan

logger = logging.getLogger(__name__)


class Orchestrator(LlmAgent):
    planner_agent: LlmAgent
    coder_agent: LlmAgent
    tester_agent: LlmAgent
    name: str

    def __init__(
        self,
        name,
        planner_agent: LlmAgent,
        coder_agent: LlmAgent,
        tester_agent: LlmAgent,
    ):
        planner_agent = planner_agent
        coder_agent = coder_agent
        tester_agent = tester_agent

        super().__init__(
            name=name,
            planner_agent=planner_agent,
            coder_agent=coder_agent,
            tester_agent=tester_agent,
        )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        output_model: Plan | None = None
        num_retry = 0
        while num_retry < 3:
            async for event in self.planner_agent.run_async(ctx):
                yield event

            output = ctx.session.state.get("planner_output")
            try:
                output_model = Plan.model_validate(output)
                break
            except ValidationError as e:
                num_retry += 1
                await ctx.session_service.append_event(
                    session=ctx.session,
                    event=Event(
                        author="system",
                        content=types.Content(
                            parts=[
                                types.Part(
                                    f"previous output failed validation, try again: {e} "
                                )
                            ]
                        ),
                    ),
                )

        if not output_model:
            return

        for task in output_model.subtasks:
            logging.debug(task)
