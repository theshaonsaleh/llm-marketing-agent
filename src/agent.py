"""Marketing content agent with tool-calling loop."""

import json
from typing import Any, Dict, List, Optional

from .content_checks import ContentChecker
from .llm_client import LLMClient
from .tools import get_tool_definitions


class MarketingAgent:
    """Agent that drafts and checks marketing content."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.checker = ContentChecker()
        self.tools = get_tool_definitions()
        self.max_iterations = 20

    def create_brief_prompt(self, brief: Dict[str, str]) -> str:
        """Create the initial system prompt from the brief."""
        return f"""You are a marketing content agent. Your task is to draft and revise marketing content.

Brief:
- Product: {brief['product']}
- Audience: {brief['audience']}
- Channel: {brief['channel']}
- Tone: {brief['tone']}

Process:
1. Plan 3 content variants with different angles using plan_variants tool
2. Draft content for each variant using draft_content tool
3. Review check results I'll provide
4. Revise any content that failed checks using revise_content tool

Focus on creating compelling, clear content that passes all checks."""

    def run(self, brief: Dict[str, str], verbose: bool = False) -> Dict[str, Any]:
        """Run the agent loop to generate and check content."""
        messages = [
            {"role": "system", "content": self.create_brief_prompt(brief)},
            {
                "role": "user",
                "content": "Please plan the content variants and then draft each one.",
            },
        ]

        variants = []
        drafts = {}
        revisions = {}
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1

            if verbose:
                print(f"\n--- Iteration {iteration} ---")

            response = self.llm.chat_completion(messages, self.tools)

            if response.get("tool_calls"):
                messages.append(response)

                for tool_call in response["tool_calls"]:
                    func_name = tool_call["function"]["name"]
                    func_args = json.loads(tool_call["function"]["arguments"])

                    if verbose:
                        print(f"Tool call: {func_name}")
                        print(f"Arguments: {json.dumps(func_args, indent=2)}")

                    tool_response = self._handle_tool_call(
                        func_name, func_args, brief, variants, drafts, revisions, verbose
                    )

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": tool_response,
                        }
                    )

            elif response.get("content"):
                if verbose:
                    print(f"Assistant: {response['content']}")

                if drafts and all(
                    v["id"] in drafts or v["id"] in revisions for v in variants
                ):
                    break

                messages.append(response)

            else:
                break

        return {
            "brief": brief,
            "variants": variants,
            "drafts": drafts,
            "revisions": revisions,
            "iterations": iteration,
        }

    def _handle_tool_call(
        self,
        func_name: str,
        func_args: Dict,
        brief: Dict,
        variants: List,
        drafts: Dict,
        revisions: Dict,
        verbose: bool,
    ) -> str:
        """Handle a tool call and return the result."""
        if func_name == "plan_variants":
            variants.clear()
            variants.extend(func_args["variants"])
            return json.dumps(
                {
                    "status": "success",
                    "message": f"Planned {len(variants)} variants. Please draft content for each.",
                }
            )

        elif func_name == "draft_content":
            content = func_args["content"]

            variant_id = self._infer_variant_id(variants, drafts)

            check_results = self.checker.run_all_checks(content, brief["channel"])

            drafts[variant_id] = {
                "content": content,
                "check_results": check_results,
            }

            if verbose:
                print(f"\nDraft for {variant_id}:")
                print(f"Content: {content}")
                print(f"Passed: {check_results['passed']}")
                if not check_results["passed"]:
                    print("Issues:")
                    for check_name, check_data in check_results["checks"].items():
                        if not check_data.get("passed", True):
                            print(f"  - {check_name}: {check_data}")

            if check_results["passed"]:
                response = {
                    "status": "success",
                    "message": "Content passed all checks!",
                    "variant_id": variant_id,
                }
            else:
                issues = []
                for check_name, check_data in check_results["checks"].items():
                    if not check_data.get("passed", True):
                        issues.append(f"{check_name}: {check_data}")

                response = {
                    "status": "needs_revision",
                    "message": "Content needs revision",
                    "variant_id": variant_id,
                    "issues": issues,
                }

            remaining = [v["id"] for v in variants if v["id"] not in drafts]
            if remaining:
                response["next_action"] = f"Draft content for variants: {remaining}"

            return json.dumps(response, indent=2)

        elif func_name == "revise_content":
            revised = func_args["revised_content"]
            changes = func_args["changes_made"]

            variant_id = self._infer_revision_variant_id(drafts, revisions)

            check_results = self.checker.run_all_checks(revised, brief["channel"])

            revisions[variant_id] = {
                "content": revised,
                "changes_made": changes,
                "check_results": check_results,
            }

            if verbose:
                print(f"\nRevision for {variant_id}:")
                print(f"Content: {revised}")
                print(f"Changes: {changes}")
                print(f"Passed: {check_results['passed']}")

            if check_results["passed"]:
                return json.dumps(
                    {
                        "status": "success",
                        "message": "Revised content passed all checks!",
                        "variant_id": variant_id,
                    }
                )
            else:
                issues = []
                for check_name, check_data in check_results["checks"].items():
                    if not check_data.get("passed", True):
                        issues.append(f"{check_name}: {check_data}")

                return json.dumps(
                    {
                        "status": "still_needs_work",
                        "message": "Revised content still has issues",
                        "variant_id": variant_id,
                        "issues": issues,
                    }
                )

        return json.dumps({"status": "error", "message": f"Unknown tool: {func_name}"})

    def _infer_variant_id(self, variants: List, drafts: Dict) -> str:
        """Infer which variant is being drafted."""
        for variant in variants:
            if variant["id"] not in drafts:
                return variant["id"]
        return f"v{len(drafts) + 1}"

    def _infer_revision_variant_id(self, drafts: Dict, revisions: Dict) -> str:
        """Infer which variant is being revised."""
        for variant_id, draft in drafts.items():
            if not draft["check_results"]["passed"] and variant_id not in revisions:
                return variant_id
        return list(drafts.keys())[0] if drafts else "v1"
