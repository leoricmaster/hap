import json
import logging
import re
from typing import Optional, Tuple, Dict, Any
from hap.core.agent import Agent
from hap.core.llm import LLMClient
from hap.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

# Pre-compiled regex patterns for performance
_THOUGHT_PATTERN = re.compile(r"\*\*Thought:\*\*\s*(.*?)(?=\*\*Action:\*\*|$)", re.IGNORECASE | re.DOTALL)
_ACTION_PATTERN = re.compile(r"\*\*Action:\*\*\s*(.*?)(?=\*\*|$)", re.IGNORECASE | re.DOTALL)
_TOOL_PATTERN = re.compile(r"([a-zA-Z0-9_-]+)\[(.*?)\]")  # Non-greedy, supports hyphenated tool names
_FINISH_ACTION = "Finish"

# Default system prompt - defines Agent role and ReAct rules
DEFAULT_SYSTEM_PROMPT = """You are an AI assistant with reasoning and action capabilities. You can analyze problems, invoke appropriate tools to gather information, and provide accurate answers.

## Workflow
Please respond strictly in the following format, one step at a time:

**Thought:** Analyze the current problem and determine what action to take.
**Action:** Choose an action, which must be one of:
- `{{tool_name}}[{{input_json}}]` - Call a specific tool, where input_json is a JSON-formatted parameter object
- `Finish[final answer]` - When you have enough information to provide the final answer

## Important Notes
1. Each response must include both Thought and Action
2. Tool call format must strictly follow: tool_name[JSON parameters]
3. Only use Finish when you are confident you can answer the question
4. If tool results are insufficient, continue using other tools or different parameters

## Examples
- Search tool: `search[{"query": "Characteristics of Python programming language"}]`
- Calculator tool: `calculator[{"a": 10, "b": 5, "operation": "add"}]`

## Formatting Tips
- Key-value pairs in JSON must be separated by commas
- String values must be enclosed in double quotes
- Numeric values do not need quotes

When receiving an Observation, continue reasoning and acting based on the new information."""

# Default ReAct prompt template (for first user message)
DEFAULT_REACT_PROMPT = """## Available Tools
{tools}

## Current Task
**Question:** {question}

Please begin your reasoning and action:"""

class ReActAgent(Agent):
    """
    ReAct (Reasoning and Acting) Agent

    An agent that combines reasoning and action capabilities:
    1. Analyzes problems and formulates action plans
    2. Invokes external tools to gather information
    3. Reasons based on observation results
    4. Iterates until reaching a final answer

    This is a classic agent paradigm, particularly suitable for tasks requiring external information.
    """

    # Override base class attribute to be non-optional
    _tool_registry: ToolRegistry

    def __init__(
        self,
        name: str,
        llm: LLMClient,
        tool_registry: ToolRegistry,
        system_prompt: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        max_steps: int = 5
    ):
        """
        Initialize ReActAgent

        Args:
            name: Agent name
            llm: LLM client instance
            tool_registry: Tool registry for tool management
            system_prompt: System prompt (optional, uses default if not provided)
            custom_prompt: Custom prompt template (optional)
            max_steps: Maximum execution steps
        """
        super().__init__(name, llm, system_prompt, tool_registry)
        self._max_steps = max_steps

        # Use custom prompt if provided, otherwise use default
        self._prompt_template = custom_prompt if custom_prompt else DEFAULT_REACT_PROMPT

    def run(self, input_text: str, **kwargs) -> str:
        """
        Run ReAct Agent

        Args:
            input_text: User question
            **kwargs: Additional parameters passed to LLM

        Returns:
            Final answer
        """
        current_step = 0

        logger.info(f"\n🤖 {self._name} processing: {input_text}")

        # Clear history for new conversation
        self.clear_history()

        # 1. Add system prompt (custom or default)
        system_content = self._system_prompt if self._system_prompt else DEFAULT_SYSTEM_PROMPT
        self.add_message("system", system_content)

        # 2. Add first user message (with tool descriptions and specific question)
        tools_desc = self._tool_registry.get_tools_description()
        initial_prompt = self._prompt_template.format(
            tools=tools_desc,
            question=input_text
        )
        self.add_message("user", initial_prompt)

        while current_step < self._max_steps:
            current_step += 1
            logger.info(f"\n--- Step {current_step} ---")

            # Build messages from history for LLM
            messages = [m for m in self._history]
            response_text = self._llm.invoke(messages, **kwargs)

            if not response_text:
                logger.error("Error: LLM returned no valid response.")
                break

            # Parse output
            thought, action = self._parse_output(response_text)

            if thought:
                logger.info(f"🤔 Thought: {thought}")

            if not action:
                logger.warning("Warning: No valid Action parsed, terminating.")
                break

            # Add assistant response to history
            self.add_message("assistant", response_text)

            # Check if finished
            if action.strip().startswith(_FINISH_ACTION):
                final_answer = self._parse_action_input(action)
                logger.info(f"🎉 Final answer: {final_answer}")
                return final_answer

            # Execute tool call
            tool_name, input_json = self._parse_action(action)
            if not tool_name or input_json is None:
                # Add observation to history for model to continue
                self.add_message("user", "Observation: Invalid Action format, please check.")
                continue

            logger.info(f"🎬 Action: {tool_name}[{input_json}]")

            # Call tool
            observation = self._tool_registry.execute_tool(tool_name, input_json)
            logger.info(f"👀 Observation: {observation}")

            # Add observation to history
            self.add_message("user", f"Observation: {observation}")

        logger.warning("Max steps reached, terminating.")
        final_answer = "Sorry, I could not complete this task within the step limit."

        # Add final result to history
        self.add_message("assistant", final_answer)

        return final_answer
    
    def _parse_output(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse LLM output to extract thought and action"""
        thought_match = _THOUGHT_PATTERN.search(text)
        action_match = _ACTION_PATTERN.search(text)

        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None

        # Clean leading asterisks and spaces
        if thought:
            thought = thought.lstrip("* ").strip()
        if action:
            action = action.lstrip("* ").strip()

        return thought, action

    def _parse_action(self, action_text: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Parse action text to extract tool name and parameters

        Args:
            action_text: Action text in format tool_name[json_params]

        Returns:
            Tuple[tool_name, parameter_dict]
        """
        match = _TOOL_PATTERN.match(action_text)
        if match:
            tool_name = match.group(1)
            params_str = match.group(2)

            try:
                # Try to parse JSON parameters
                params = json.loads(params_str)
                if isinstance(params, dict):
                    return tool_name, params
                else:
                    # Wrap non-dict values as "input" parameter
                    return tool_name, {"input": str(params)}
            except (json.JSONDecodeError, ValueError):
                # If JSON parsing fails, use entire string as "input" parameter
                return tool_name, {"input": params_str}

        return None, None

    def _parse_action_input(self, action_text: str) -> str:
        """Extract input from Finish action"""
        match = _TOOL_PATTERN.match(action_text)
        return match.group(2) if match else ""

