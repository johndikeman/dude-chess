"""Token Optimizer Agent - Always uses cheap models to summarize console output.

This agent is a specialized sub-agent that takes execution results, test output,
or any console text and returns a structured summary. It NEVER passes full
console output up to expensive parent agents.
"""

from typing import Optional, Dict, Any
import litellm
from loguru import logger

from ..models import ExecutionResult, ConsoleSummary, TaskStatus, SubAgentResult, SubTask
from .base import BaseSubAgent


class TokenOptimizerAgent(BaseSubAgent):
    """Specialized agent for compressing console output using cheap models."""
    
    DEFAULT_MODEL = "gemini/gemini-1.5-flash"  # Very cheap for summarization
    
    # Prompt to extract key information from console output
    SUMMARIZATION_PROMPT = """You are a console output analyzer. Your job is to extract the most important information 
from the following console output and return it as structured JSON.

Focus on:
1. What was the overall result (success, failure, partial success)
2. Key errors or failures with their messages
3. Warnings that should be noted
4. Success indicators (tests passed, files created, etc.)
5. Any metrics or numbers (test counts, coverage, etc.)
6. Files mentioned (especially error locations)
7. Whether human intervention is needed

Output Format:
{
  "summary": "brief summary in 2-3 sentences",
  "key_errors": ["error1", "error2", ...],
  "warnings": ["warning1", "warning2", ...],
  "success_indicators": ["indicator1", ...],
  "metrics": {"tests_run": 50, "failed": 2, ...},
  "relevant_files": ["file1.py", "file2.py", ...],
  "action_needed": false
}

Return ONLY valid JSON, no extra text.

Console Output:
{console_output}
"""
    
    def __init__(self, model_name: Optional[str] = None):
        """Initialize token optimizer.
        
        Args:
            model_name: Override the default cheap model
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        logger.info(f"TokenOptimizerAgent initialized with model: {self.model_name}")
    
    async def execute(self, task: SubTask) -> SubAgentResult:
        """Execute token optimization on execution result.
        
        Args:
            task: Must contain execution_result in context or metadata
            
        Returns:
            SubAgentResult with ConsoleSummary
        """
        logger.info(f"TokenOptimizerAgent executing task {task.task_id}")
        
        # Extract execution result from context
        execution_result: Optional[ExecutionResult] = None
        
        if "execution_result" in task.context:
            execution_result = ExecutionResult(**task.context["execution_result"])
        elif hasattr(task, "execution_result") and task.execution_result:
            execution_result = task.execution_result
        else:
            logger.error("No execution_result found in task context")
            return SubAgentResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                result="No execution result provided for summarization",
                token_usage={}
            )
        
        # Concatenate stdout and stderr for summarization
        console_output = f"STDOUT:\n{execution_result.stdout}\n\nSTDERR:\n{execution_result.stderr}"
        
        # Early exit for empty output
        if not console_output.strip():
            logger.warning("Empty console output, returning minimal summary")
            console_summary = ConsoleSummary(
                summary="No output generated",
                metrics={"exit_code": execution_result.exit_code}
            )
            return SubAgentResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                result="Empty output summarized",
                console_summary=console_summary,
                token_usage={}
            )
        
        # Build prompt
        prompt = self.SUMMARIZATION_PROMPT.format(console_output=console_output[:20000])  # Limit length
        
        try:
            # Call cheap model for summarization
            response = await litellm.acompletion(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=1000,
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            # Extract response
            content = response.choices[0].message.content
            token_usage = {
                "input": response.usage.prompt_tokens,
                "output": response.usage.completion_tokens,
                "cost": self._estimate_cost(response.usage)
            }
            
            # Parse JSON response
            import json
            try:
                summary_data = json.loads(content)
                console_summary = ConsoleSummary(**summary_data)
                
                # Add execution info
                console_summary.metrics["exit_code"] = execution_result.exit_code
                console_summary.metrics["duration_seconds"] = execution_result.duration_seconds
                
                logger.info(f"Successfully summarized output in {token_usage['input'] + token_usage['output']} tokens")
                logger.debug(f"Summary: {console_summary.summary}")
                
                return SubAgentResult(
                    task_id=task.task_id,
                    status=TaskStatus.COMPLETED,
                    result="Console output summarized successfully",
                    console_summary=console_summary,
                    execution_result=execution_result,
                    token_usage=token_usage
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw response: {content}")
                
                # Fallback to simple error message
                console_summary = ConsoleSummary(
                    summary="Failed to parse model response",
                    key_errors=[f"JSON parse error: {str(e)}"],
                    metrics={"exit_code": execution_result.exit_code}
                )
                
                return SubAgentResult(
                    task_id=task.task_id,
                    status=TaskStatus.FAILED,
                    result="Failed to parse summarization",
                    console_summary=console_summary,
                    execution_result=execution_result,
                    token_usage=token_usage
                )
        
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            
            # Fallback: create basic summary without model
            console_summary = ConsoleSummary(
                summary=f"Command exited with code {execution_result.exit_code}",
                key_errors=[line for line in execution_result.stderr.split('\n') if 'error' in line.lower()][:5],
                metrics={
                    "exit_code": execution_result.exit_code,
                    "duration_seconds": execution_result.duration_seconds,
                    "stdout_lines": len(execution_result.stdout.split('\n')),
                    "stderr_lines": len(execution_result.stderr.split('\n'))
                }
            )
            
            return SubAgentResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,  # Not a failure, just fallback
                result="Console output summarized with fallback method",
                console_summary=console_summary,
                execution_result=execution_result,
                token_usage={},
                metadata={"fallback_used": True, "error": str(e)}
            )
    
    def _estimate_cost(self, usage: Any) -> float:
        """Estimate cost for cheap model (approximate)."""
        # Gemini Flash: ~$0.00001875 per 1K tokens
        return (usage.prompt_tokens + usage.completion_tokens) * 0.00001875 / 1000
