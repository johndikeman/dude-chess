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
from pydantic import BaseModel, Field


class Orchestrator(LlmAgent):
    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        yield Event()
