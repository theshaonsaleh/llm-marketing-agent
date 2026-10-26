"""CLI for the marketing content agent."""

import argparse
import json
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from .agent import MarketingAgent
from .llm_client import LLMClient


def load_brief_from_file(filepath: str) -> dict:
    """Load brief from JSON file."""
    with open(filepath, "r") as f:
        return json.load(f)


def print_results(results: dict):
    """Pretty print agent results."""
    print("\n" + "=" * 80)
    print("MARKETING CONTENT GENERATION RESULTS")
    print("=" * 80)

    print(f"\n📋 BRIEF:")
    brief = results["brief"]
    print(f"  Product: {brief['product']}")
    print(f"  Audience: {brief['audience']}")
    print(f"  Channel: {brief['channel']}")
    print(f"  Tone: {brief['tone']}")

    print(f"\n📊 VARIANTS PLANNED: {len(results['variants'])}")
    for variant in results["variants"]:
        print(f"  • {variant['id']}: {variant['angle']} ({variant['tone']})")

    print(f"\n✍️  DRAFTS:")
    for variant_id, draft_data in results["drafts"].items():
        print(f"\n  [{variant_id}]")
        print(f"  Content: {draft_data['content']}")
        checks = draft_data["check_results"]
        print(f"  Status: {'✅ PASSED' if checks['passed'] else '❌ FAILED'}")

        if not checks["passed"]:
            print(f"  Issues:")
            for check_name, check_result in checks["checks"].items():
                if not check_result.get("passed", True):
                    print(f"    - {check_name}: {check_result}")

    if results["revisions"]:
        print(f"\n🔄 REVISIONS:")
        for variant_id, revision_data in results["revisions"].items():
            print(f"\n  [{variant_id}]")
            print(f"  Content: {revision_data['content']}")
            print(f"  Changes: {revision_data['changes_made']}")
            checks = revision_data["check_results"]
            print(f"  Status: {'✅ PASSED' if checks['passed'] else '❌ FAILED'}")

    print(f"\n🔢 Total iterations: {results['iterations']}")
    print("=" * 80 + "\n")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Marketing Content Agent - Draft and check marketing content"
    )
    parser.add_argument(
        "--brief",
        type=str,
        help="Path to brief JSON file (see examples/)",
    )
    parser.add_argument(
        "--product",
        type=str,
        help="Product description",
    )
    parser.add_argument(
        "--audience",
        type=str,
        help="Target audience",
    )
    parser.add_argument(
        "--channel",
        type=str,
        help="Channel (twitter, instagram, facebook, linkedin, tiktok, ad_copy)",
    )
    parser.add_argument(
        "--tone",
        type=str,
        help="Desired tone",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed agent execution",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key (or set OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        help="OpenAI base URL (or set OPENAI_BASE_URL env var)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="Model name (default: gpt-4o-mini)",
    )

    args = parser.parse_args()

    load_dotenv()

    if args.brief:
        brief = load_brief_from_file(args.brief)
    elif all([args.product, args.audience, args.channel, args.tone]):
        brief = {
            "product": args.product,
            "audience": args.audience,
            "channel": args.channel,
            "tone": args.tone,
        }
    else:
        parser.error(
            "Either --brief or all of (--product, --audience, --channel, --tone) required"
        )

    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    base_url = args.base_url or os.getenv("OPENAI_BASE_URL")
    model = args.model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if api_key:
        print(f"🔑 Using OpenAI-compatible API with model: {model}")
    else:
        print("🤖 Using mock LLM (no API key provided)")

    llm_client = LLMClient(api_key=api_key, base_url=base_url, model=model)

    agent = MarketingAgent(llm_client)

    print(f"\n🚀 Running agent...")
    if args.verbose:
        print(f"Brief: {json.dumps(brief, indent=2)}")

    results = agent.run(brief, verbose=args.verbose)

    print_results(results)


if __name__ == "__main__":
    main()
