"""Simplified Execution Agent Runtime."""

import inspect
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from .agent import ExecutionAgent
from .tools import get_tool_schemas, get_tool_registry
from ...config import get_settings
from ...openrouter_client import request_chat_completion
from ...logging_config import logger
from ...services.execution import get_user_context


@dataclass
class ExecutionResult:
    """Result from an execution agent."""
    agent_name: str
    success: bool
    response: str
    error: Optional[str] = None
    tools_executed: List[str] = None


class ExecutionAgentRuntime:
    """Manages the execution of a single agent request."""

    MAX_TOOL_ITERATIONS = 8

    # Initialize execution agent runtime with settings, tools, and agent instance
    def __init__(self, agent_name: str):
        settings = get_settings()
        self.agent = ExecutionAgent(agent_name)
        self.api_key = settings.openrouter_api_key
        self.model = settings.execution_agent_model
        self.agent_name = agent_name

        # Store user context info for deferred service creation
        user_context = get_user_context()
        self._user_id = user_context.user_id if user_context else None
        self._user_type = user_context.user_type if user_context else "adult"

        # Defer tool registry creation until execute() when we have our own session
        self.tool_registry = None
        self.tool_schemas = get_tool_schemas(user_type=self._user_type)

        if not self.api_key:
            raise ValueError("OpenRouter API key not configured. Set OPENROUTER_API_KEY environment variable.")

    # Main execution loop for running agent with LLM calls and tool execution
    async def execute(self, instructions: str) -> ExecutionResult:
        """Execute the agent with given instructions.

        Creates its own database session to avoid concurrency issues with
        the interaction agent's session.
        """
        # Create our own session to avoid sharing with interaction agent
        from ...database.session import async_session_factory

        async with async_session_factory() as session:
            return await self._execute_with_session(session, instructions)

    async def _execute_with_session(self, session, instructions: str) -> ExecutionResult:
        """Execute the agent with a dedicated database session."""
        try:
            # Create services with our own session
            await self._create_services(session)

            # Build system prompt with history
            system_prompt = self.agent.build_system_prompt_with_history()

            # Start conversation with the instruction
            messages = [{"role": "user", "content": instructions}]
            tools_executed: List[str] = []
            final_response: Optional[str] = None

            for iteration in range(self.MAX_TOOL_ITERATIONS):
                logger.info(
                    f"[{self.agent.name}] Requesting plan (iteration {iteration + 1})"
                )
                response = await self._make_llm_call(system_prompt, messages, with_tools=True)
                assistant_message = response.get("choices", [{}])[0].get("message", {})

                if not assistant_message:
                    raise RuntimeError("LLM response did not include an assistant message")

                raw_tool_calls = assistant_message.get("tool_calls", []) or []
                parsed_tool_calls = self._extract_tool_calls(raw_tool_calls)

                assistant_entry: Dict[str, Any] = {
                    "role": "assistant",
                    "content": assistant_message.get("content", "") or "",
                }
                if raw_tool_calls:
                    assistant_entry["tool_calls"] = raw_tool_calls
                messages.append(assistant_entry)

                if not parsed_tool_calls:
                    final_response = assistant_entry["content"] or "No action required."
                    break

                for tool_call in parsed_tool_calls:
                    tool_name = tool_call.get("name", "")
                    tool_args = tool_call.get("arguments", {})
                    call_id = tool_call.get("id")

                    if not tool_name:
                        logger.warning("Tool call missing name: %s", tool_call)
                        failure = {"error": "Tool call missing name; unable to execute."}
                        tool_message = {
                            "role": "tool",
                            "tool_call_id": call_id or "unknown_tool",
                            "content": self._format_tool_result(
                                tool_name or "<unknown>", False, failure, tool_args
                            ),
                        }
                        messages.append(tool_message)
                        continue

                    tools_executed.append(tool_name)
                    logger.info(f"[{self.agent.name}] Executing tool: {tool_name}")

                    success, result = await self._execute_tool(tool_name, tool_args)

                    if success:
                        logger.info(f"[{self.agent.name}] Tool {tool_name} completed successfully")
                        record_payload = self._safe_json_dump(result)
                    else:
                        error_detail = result.get("error") if isinstance(result, dict) else str(result)
                        logger.warning(f"[{self.agent.name}] Tool {tool_name} failed: {error_detail}")
                        record_payload = error_detail

                    self.agent.record_tool_execution(
                        tool_name,
                        self._safe_json_dump(tool_args),
                        record_payload
                    )

                    tool_message = {
                        "role": "tool",
                        "tool_call_id": call_id or tool_name,
                        "content": self._format_tool_result(tool_name, success, result, tool_args),
                    }
                    messages.append(tool_message)

            else:
                raise RuntimeError("Reached tool iteration limit without final response")

            if final_response is None:
                raise RuntimeError("LLM did not return a final response")

            self.agent.record_response(final_response)

            return ExecutionResult(
                agent_name=self.agent.name,
                success=True,
                response=final_response,
                tools_executed=tools_executed
            )

        except Exception as e:
            logger.error(f"[{self.agent.name}] Execution failed: {e}")
            error_msg = str(e)
            failure_text = f"Failed to complete task: {error_msg}"
            self.agent.record_response(f"Error: {error_msg}")

            return ExecutionResult(
                agent_name=self.agent.name,
                success=False,
                response=failure_text,
                error=error_msg
            )

    async def _create_services(self, session) -> None:
        """Create services with the provided session.

        This ensures the execution agent uses its own database session,
        preventing concurrent operation errors with the interaction agent.
        """
        if not self._user_id:
            # No user context - create minimal tool registry
            self.tool_registry = get_tool_registry(
                agent_name=self.agent_name,
                user_type=self._user_type,
            )
            return

        finance_service = None
        achievements_service = None
        adult_finance_service = None
        insights_service = None

        if self._user_type == "child":
            from ...repositories.expenses import ExpenseRepository
            from ...repositories.savings_goals import SavingsGoalRepository
            from ...repositories.achievements import AchievementRepository
            from ...repositories.users import UserRepository
            from ...services.v2.finance_service import FinanceService
            from ...services.v2.achievements_service import AchievementsService

            user_repo = UserRepository(session)
            user = await user_repo.get_by_id(self._user_id)

            if user:
                expense_repo = ExpenseRepository(session, self._user_id)
                savings_repo = SavingsGoalRepository(session, self._user_id)
                achievement_repo = AchievementRepository(session, self._user_id)

                finance_service = FinanceService(
                    expense_repo=expense_repo,
                    savings_repo=savings_repo,
                    user=user,
                    auto_commit=True,
                )
                achievements_service = AchievementsService(
                    achievement_repo=achievement_repo,
                    auto_commit=True,
                )

        elif self._user_type == "adult":
            from ...repositories.transactions import TransactionRepository
            from ...repositories.budgets import BudgetRepository
            from ...repositories.debts import DebtRepository
            from ...repositories.recurring_transactions import RecurringTransactionRepository
            from ...repositories.exchange_rates import ExchangeRateRepository
            from ...repositories.users import UserRepository
            from ...services.v2.adult_finance_service import AdultFinanceService
            from ...services.v2.currency_service import CurrencyService
            from ...services.v2.insights_service import InsightsService

            user_repo = UserRepository(session)
            user = await user_repo.get_by_id(self._user_id)

            if user:
                transaction_repo = TransactionRepository(session, self._user_id)
                budget_repo = BudgetRepository(session, self._user_id)
                debt_repo = DebtRepository(session, self._user_id)
                recurring_repo = RecurringTransactionRepository(session, self._user_id)
                exchange_rate_repo = ExchangeRateRepository(session)

                currency_service = CurrencyService(exchange_rate_repo)
                adult_finance_service = AdultFinanceService(
                    transaction_repo=transaction_repo,
                    budget_repo=budget_repo,
                    debt_repo=debt_repo,
                    recurring_repo=recurring_repo,
                    currency_service=currency_service,
                    user=user,
                    auto_commit=True,
                )

                # Create insights service for adult users
                insights_service = InsightsService(
                    transaction_repo=transaction_repo,
                    budget_repo=budget_repo,
                    currency_service=currency_service,
                    user=user,
                )

        self.tool_registry = get_tool_registry(
            agent_name=self.agent_name,
            user_type=self._user_type,
            finance_service=finance_service,
            achievements_service=achievements_service,
            adult_finance_service=adult_finance_service,
            insights_service=insights_service,
        )

    # Execute OpenRouter API call with system prompt, messages, and optional tool schemas
    async def _make_llm_call(self, system_prompt: str, messages: List[Dict], with_tools: bool) -> Dict:
        """Make an LLM call."""
        tools_to_send = self.tool_schemas if with_tools else None
        logger.info(f"[{self.agent.name}] Calling LLM with model: {self.model}, tools: {len(tools_to_send) if tools_to_send else 0}")
        return await request_chat_completion(
            model=self.model,
            messages=messages,
            system=system_prompt,
            api_key=self.api_key,
            tools=tools_to_send
        )

    # Parse and validate tool calls from LLM response into structured format
    def _extract_tool_calls(self, raw_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract tool calls from an assistant message."""
        tool_calls: List[Dict[str, Any]] = []

        for tool in raw_tools:
            function = tool.get("function", {})
            name = function.get("name", "")
            args = function.get("arguments", "")

            if isinstance(args, str):
                try:
                    args = json.loads(args) if args else {}
                except json.JSONDecodeError:
                    args = {}

            if name:
                tool_calls.append({
                    "id": tool.get("id"),
                    "name": name,
                    "arguments": args,
                })

        return tool_calls

    # Safely convert objects to JSON with fallback to string representation
    def _safe_json_dump(self, payload: Any) -> str:
        """Serialize payload to JSON, falling back to string representation."""
        try:
            return json.dumps(payload, default=str)
        except TypeError:
            return str(payload)

    # Format tool execution results into JSON structure for LLM consumption
    def _format_tool_result(
        self,
        tool_name: str,
        success: bool,
        result: Any,
        arguments: Dict[str, Any],
    ) -> str:
        """Build a structured string for tool responses."""
        if success:
            payload: Dict[str, Any] = {
                "tool": tool_name,
                "status": "success",
                "arguments": arguments,
                "result": result,
            }
        else:
            error_detail = result.get("error") if isinstance(result, dict) else str(result)
            payload = {
                "tool": tool_name,
                "status": "error",
                "arguments": arguments,
                "error": error_detail,
            }
        return self._safe_json_dump(payload)

    # Execute tool function from registry with error handling and async support
    async def _execute_tool(self, tool_name: str, arguments: Dict) -> Tuple[bool, Any]:
        """Execute a tool. Returns (success, result)."""
        tool_func = self.tool_registry.get(tool_name)
        if not tool_func:
            return False, {"error": f"Unknown tool: {tool_name}"}

        try:
            result = tool_func(**arguments)
            if inspect.isawaitable(result):
                result = await result
            return True, result
        except Exception as e:
            return False, {"error": str(e)}
