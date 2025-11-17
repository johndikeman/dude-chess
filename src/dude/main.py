import logging
import sys
import asyncio
import uuid
import json
import os
from datetime import datetime
from pathlib import Path

from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService

from dude.agents.orchestrator import Orchestrator
from dude.agents import planner, coder


# Configure logging for CLI
def setup_logging():
    """Configure comprehensive logging for CLI interface with file output"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Remove any existing handlers
    logger.handlers.clear()

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Generate unique log filename with timestamp and session ID
    session_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = log_dir / f"dude_session_{timestamp}_{session_id}.log"

    # Create console handler with detailed formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Create file handler with more detailed formatting for comprehensive logging
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)

    # Create formatter with timestamp, level, function name, and message
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File formatter includes more details
    file_formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler.setFormatter(console_formatter)
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.info(f"Logging initialized. Log file: {log_filename}")
    logger.info(f"Session ID: {session_id}")

    return logger, log_filename


logger, LOG_FILENAME = setup_logging()

import dotenv

dotenv.load_dotenv()
logger.debug("Environment variables loaded from .env file")

from lmnr import Laminar

Laminar.initialize(
    project_api_key="6gbQMsICyAmUq3CYUhCT0IlzVVn44WQN2uSFKSJ7x3723fhRvVp3sGqEMyC7Hsd6"
)


# --- Setup Runner and Session ---
async def setup_session_and_runner():
    """Setup database session and agent runner with comprehensive logging."""
    logger.info("Setting up session and runner")

    try:
        db_url = "sqlite:///./my_agent_data.db"
        logger.debug(f"Using database URL: {db_url}")

        session_service = DatabaseSessionService(db_url=db_url)
        logger.debug("Database session service created successfully")

        session_id = str(uuid.uuid4())
        logger.debug(f"Generated session ID: {session_id}")

        session = await session_service.create_session(
            app_name="dude", user_id="john", session_id=session_id, state={}
        )
        logger.info(
            f"Session created successfully for user 'john' with ID: {session_id[:8]}..."
        )

        logger.debug("Initializing orchestrator agent")
        orchestrator = Orchestrator(
            planner_agent=planner,
            coder_agent=coder,
            tester_agent=coder,
            name="orchestrator",
        )
        logger.info("Orchestrator agent initialized")

        runner = Runner(
            agent=orchestrator,  # Pass the custom orchestrator agent
            app_name="dude",
            session_service=session_service,
        )
        logger.info("Runner created successfully")

        return session_service, session, runner

    except Exception as e:
        logger.error(f"Failed to setup session and runner: {str(e)}", exc_info=True)
        raise


# --- Function to Interact with the Agent ---
async def call_agent_async(user_input_topic: str):
    """
    Sends a new topic to the agent (overwriting the initial one if needed)
    and runs the workflow with comprehensive event and tool usage tracking.
    """
    logger.info(f"call_agent_async started with topic: '{user_input_topic[:50]}...'")

    try:
        session_service, current_session, runner = await setup_session_and_runner()
        logger.debug(f"Session ID: {current_session.id[:8]}...")

        # Update session state
        current_session.state["topic"] = user_input_topic
        logger.info(f"Updated session state topic to: '{user_input_topic[:50]}...'")
        logger.debug(f"Full topic content: {user_input_topic}")

        # Create user message content
        content = types.Content(
            role="user",
            parts=[types.Part(text=f"{user_input_topic}")],
        )
        logger.debug("User message content created")

        # Start agent execution
        logger.info("Starting agent execution...")
        events = runner.run_async(
            user_id=current_session.user_id,
            session_id=current_session.id,
            new_message=content,
        )

        final_response = "No final response captured."
        event_count = 0
        tool_call_count = 0

        # Process events
        async for event in events:
            event_count += 1

            logger.debug(f"Event #{event_count} type: {type(event).__name__}")

            # Log event attributes for tool tracking
            event_attrs = {}
            for attr in dir(event):
                if not attr.startswith("_") and not callable(getattr(event, attr)):
                    try:
                        value = getattr(event, attr)
                        event_attrs[attr] = str(value)[:200]  # Limit length
                    except Exception as e:
                        event_attrs[attr] = f"<Error accessing: {e}>"

            logger.debug(
                f"Event attributes: {json.dumps(event_attrs, indent=2, default=str)}"
            )

            # Check for tool calls and executions
            if hasattr(event, "tool_call"):
                tool_call_count += 1
                tool_call = event.tool_call
                logger.info(f"Tool Call #{tool_call_count}: {tool_call}")

            if hasattr(event, "tool_response"):
                tool_response = event.tool_response
                logger.info(f"Tool Response: {str(tool_response)[:200]}...")

            # Check for usage data
            if hasattr(event, "usage"):
                logger.debug(f"Usage data found: {event.usage}")
            if hasattr(event, "usage_metadata"):
                logger.debug(f"Usage metadata found: {event.usage_metadata}")
            if hasattr(event, "model_dump"):
                try:
                    event_dump = event.model_dump()
                    logger.debug(
                        f"Event dump: {json.dumps(event_dump, indent=2, default=str)[:500]}..."
                    )
                except Exception as e:
                    logger.debug(f"Error dumping event: {e}")

            # Author tracking
            author = getattr(event, "author", "unknown")
            logger.debug(f"Processing event #{event_count} from author: {author}")

            # Final response tracking
            if event.is_final_response() and event.content and event.content.parts:
                response_text = event.content.parts[0].text
                logger.info(
                    f"Final response received from [{author}]: {response_text[:100]}..."
                )
                logger.debug(f"Full response: {response_text}")
                final_response = response_text

        logger.info(
            f"Agent execution completed. Processed {event_count} events ({tool_call_count} tool calls)"
        )
        logger.debug(f"Final response captured: {final_response[:100]}...")

        print("\n--- Agent Interaction Result ---")
        print("Agent Final Response: ", final_response)

    except Exception as e:
        logger.error(f"Error in call_agent_async: {str(e)}", exc_info=True)
        raise
    finally:
        logger.info("call_agent_async completed")


def main():
    """Main CLI entry point with comprehensive logging and error handling."""
    logger.info("=== Dude CLI Agent Starting ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"CLI called at: {datetime.now().isoformat()}")

    # Validate CLI arguments
    if len(sys.argv) < 2:
        logger.error("No topic provided. Usage: dude <topic>")
        print("❌ Error: No topic provided. Usage: dude <topic>")
        logger.info("CLI shutting down due to missing argument")
        sys.exit(1)

    argument = sys.argv[1]
    logger.info(f"CLI argument received: '{argument[:50]}...'")
    logger.debug(f"Full CLI argument: {argument}")

    try:
        # Run the async agent function
        asyncio.run(call_agent_async(str(argument)))
        logger.info("Agent execution completed successfully")
        print("\n✅ Agent execution completed successfully")
    except KeyboardInterrupt:
        logger.warning("CLI execution interrupted by user (Ctrl+C)")
        print("\n❌ Execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"CLI execution failed: {str(e)}", exc_info=True)
        print(f"\n❌ Execution failed: {str(e)}")
        sys.exit(1)
    finally:
        logger.info("=== Dude CLI Agent Shutting Down ===")
        # Flush any remaining log messages
        for handler in logger.handlers:
            handler.flush()
