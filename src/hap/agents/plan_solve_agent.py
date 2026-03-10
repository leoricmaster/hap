import ast
import logging
import re
from typing import Optional, List, Dict, Tuple, Callable
from hap.core.agent import Agent
from hap.core.llm import LLMClient

logger = logging.getLogger(__name__)

__all__ = ["Planner", "Executor", "PlanAndSolveAgent"]

# Default planner prompt template
DEFAULT_PLANNER_PROMPT = """
You are a top-tier AI planning expert. Your task is to break down the user's complex problem into an action plan consisting of multiple simple steps.
Ensure that each step in the plan is an independent, executable subtask, arranged in strict logical order.
Your output must be a Python list, where each element is a string describing a subtask.

Problem: {question}

Please output your plan strictly in the following format:
```python
["Step 1", "Step 2", "Step 3", ...]
```
"""

# Default executor prompt template
DEFAULT_EXECUTOR_PROMPT = """
You are a top-tier AI execution expert. Your task is to strictly follow the given plan and solve the problem step by step.
You will receive the original problem, the complete plan, and the steps completed so far with their results.
Focus on solving the "current step" and output only the final answer for that step. Do not include any extra explanations or conversation.

# Original Problem:
{question}

# Complete Plan:
{plan}

# History of Steps and Results:
{history}

# Current Step:
{current_step}

Please output only the answer for the "current step":
"""

class Planner:
    """Planner - responsible for decomposing complex problems into simple steps"""

    def __init__(self, llm_client: LLMClient, prompt_template: Optional[str] = None):
        self.llm_client = llm_client
        self.prompt_template = prompt_template if prompt_template else DEFAULT_PLANNER_PROMPT

    def plan(self, question: str, **kwargs) -> List[str]:
        """
        Generate execution plan

        Args:
            question: Problem to solve
            **kwargs: LLM invocation parameters

        Returns:
            List of steps
        """
        prompt = self.prompt_template.format(question=question)
        messages = [{"role": "user", "content": prompt}]

        logger.info("--- Generating plan ---")
        response_text = self.llm_client.invoke(messages, **kwargs) or ""
        logger.info(f"LLM response:\n{response_text}")

        plan = self._extract_plan(response_text)
        if plan:
            logger.info(f"✅ Successfully parsed plan with {len(plan)} steps")
        else:
            logger.warning("❌ Failed to parse a valid plan from the response")

        return plan

    def _extract_plan(self, response_text: str) -> List[str]:
        """Extract plan list from response, supporting multiple formats"""
        if not response_text:
            return []

        # Try multiple pattern matching
        patterns = [
            r'```python\s*(.*?)\s*```',  # ```python ... ```
            r'```\s*(.*?)\s*```',         # ``` ... ```
        ]

        candidates = []

        # Extract from code blocks
        for pattern in patterns:
            matches = re.findall(pattern, response_text, re.DOTALL | re.IGNORECASE)
            candidates.extend(matches)

        # Try the entire text (strip leading/trailing whitespace)
        candidates.append(response_text.strip())

        for candidate in candidates:
            candidate = candidate.strip()
            try:
                plan = ast.literal_eval(candidate)
                if isinstance(plan, list) and all(isinstance(s, str) and s.strip() for s in plan):
                    return [s.strip() for s in plan if s.strip()]
            except (ValueError, SyntaxError):
                continue

        logger.warning(f"Could not parse plan from response: {response_text[:200]}...")

        # Last resort: split by lines, extract numbered steps or filter empty lines
        lines = response_text.strip().split('\n')
        fallback_plan = []
        for line in lines:
            line = line.strip()
            # Remove common prefix symbols (e.g., numbers, -, *, >, etc.)
            cleaned = re.sub(r'^[\s\d\[\]()]+[.、)\]\-*>\s]*', '', line)
            if cleaned and len(cleaned) > 3:  # At least 3 characters to be a valid step
                fallback_plan.append(cleaned)

        if fallback_plan:
            logger.info(f"Using text parsing as fallback, extracted {len(fallback_plan)} steps")
            return fallback_plan

        return []

class Executor:
    """Executor - responsible for step-by-step execution of the plan"""

    def __init__(self, llm_client: LLMClient, prompt_template: Optional[str] = None):
        self.llm_client = llm_client
        self.prompt_template = prompt_template if prompt_template else DEFAULT_EXECUTOR_PROMPT

    def _format_prompt(self, question: str, plan: List[str], execution_log: str, current_step: str) -> str:
        """Safely format executor prompt, escaping curly braces in user content."""
        # Escape curly braces in user-provided content to prevent format errors
        safe_question = question.replace("{", "{{").replace("}", "}}")
        safe_execution_log = execution_log.replace("{", "{{").replace("}", "}}")
        safe_current_step = current_step.replace("{", "{{").replace("}", "}}")
        safe_plan_lines = [s.replace("{", "{{").replace("}", "}}") for s in plan]

        return self.prompt_template.format(
            question=safe_question,
            plan="\n".join(f"{j+1}. {s}" for j, s in enumerate(safe_plan_lines)),
            history=safe_execution_log if execution_log else "None",
            current_step=safe_current_step
        )

    def execute(
        self,
        question: str,
        plan: List[str],
        on_step_start: Optional[Callable[[int, str], None]] = None,
        on_step_complete: Optional[Callable[[int, str, str], None]] = None,
        max_steps: int = 10,
        **kwargs
    ) -> Tuple[str, List[Dict]]:
        """
        Execute tasks according to the plan

        Args:
            question: Original problem
            plan: Execution plan
            on_step_start: Optional callback function, called when a step starts, parameters are (step_index, step_description)
            on_step_complete: Optional callback function, called when a step completes, parameters are (step_index, step_description, result)
            max_steps: Maximum number of execution steps
            **kwargs: LLM invocation parameters

        Returns:
            (Final answer, Step execution history list)
        """
        # Filter and limit the number of steps
        valid_steps = [s.strip() for s in plan if s and s.strip()]
        steps_to_execute = valid_steps[:max_steps]

        if len(valid_steps) > max_steps:
            logger.warning(f"Plan has too many steps ({len(valid_steps)}), truncated to {max_steps}")

        execution_log = ""
        final_answer = ""
        step_results = []

        logger.info(f"\n--- Executing plan ({len(steps_to_execute)} steps) ---")

        for i, step in enumerate(steps_to_execute, 1):
            if not step:
                logger.warning(f"Step {i} is empty, skipping")
                continue

            logger.info(f"-> Executing step {i}/{len(steps_to_execute)}: {step}")

            # Record plan execution start
            if on_step_start:
                on_step_start(i, step)

            prompt = self._format_prompt(question, steps_to_execute, execution_log, step)
            messages = [{"role": "user", "content": prompt}]

            try:
                response_text = self.llm_client.invoke(messages, **kwargs) or ""

                # Check result validity
                if not response_text.strip():
                    response_text = "[Step execution returned empty result]"
                    logger.warning(f"Step {i} returned empty result")

            except Exception as e:
                response_text = f"[Step execution error: {str(e)}]"
                logger.error(f"Step {i} execution exception: {e}")

            execution_log += f"Step {i}: {step}\nResult: {response_text}\n\n"
            final_answer = response_text

            step_results.append({
                "step": i,
                "description": step,
                "result": response_text
            })

            # Record step result to Agent history
            if on_step_complete:
                on_step_complete(i, step, response_text)

            logger.info(f"✅ Step {i} completed")

        return final_answer, step_results


class PlanAndSolveAgent(Agent):
    """
    Plan and Solve Agent - An agent that decomposes planning and step-by-step execution

    This Agent can:
    1. Decompose complex problems into simple steps
    2. Execute step-by-step according to the plan
    3. Maintain execution history and context
    4. Arrive at the final answer

    Especially suitable for multi-step reasoning, mathematical problems, complex analysis, and similar tasks.
    """

    def __init__(
        self,
        name: str,
        llm: LLMClient,
        system_prompt: Optional[str] = None,
        custom_prompts: Optional[Dict[str, str]] = None,
        max_steps: int = 10,
    ):
        """
        Initialize PlanAndSolveAgent

        Args:
            name: Agent name
            llm: LLM instance
            system_prompt: System prompt
            custom_prompts: Custom prompt templates {"planner": "", "executor": ""}
            max_steps: Maximum number of execution steps
        """
        super().__init__(name, llm, system_prompt)
        self.max_steps = max_steps

        # Set prompt templates: user-defined takes priority, otherwise use default
        planner_prompt = custom_prompts.get("planner") if custom_prompts else None
        executor_prompt = custom_prompts.get("executor") if custom_prompts else None

        self.planner = Planner(self._llm, planner_prompt)
        self.executor = Executor(self._llm, executor_prompt)

    def run(self, input_text: str, **kwargs) -> str:
        """
        Run Plan and Solve Agent

        Args:
            input_text: Problem to solve
            **kwargs: Other parameters

        Returns:
            Final answer
        """
        logger.info(f"\n🤖 {self._name} starting to process: {input_text}")

        # Clear history and start a new conversation
        self.clear_history()

        # Add system prompt
        if self._system_prompt:
            self.add_message("system", self._system_prompt)

        # Add user question
        self.add_message("user", input_text)

        # 1. Generate plan
        plan = self.planner.plan(input_text, **kwargs)
        if not plan:
            final_answer = "Unable to generate a valid action plan. Task terminated."
            logger.warning(f"Task terminated: {final_answer}")

            self.add_message("assistant", final_answer)
            return final_answer

        # Record generated plan
        plan_text = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))
        self.add_message("assistant", f"**Execution Plan**:\n{plan_text}")

        # 2. Execute plan
        final_answer, step_results = self.executor.execute(
            input_text,
            plan,
            on_step_start=lambda i, step: self.add_message("assistant", f"**Step {i}**: {step}"),
            on_step_complete=lambda i, step, result: self.add_message("assistant", f"**Result**: {result}"),
            max_steps=self.max_steps,
            **kwargs
        )

        logger.info(f"\n--- Task completed ---\nFinal answer: {final_answer}")

        # Add final answer
        self.add_message("assistant", f"**Final Answer**: {final_answer}")

        return final_answer