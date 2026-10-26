#!/usr/bin/env python3
"""
Command-line interface for the Marketing Content Agent.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from marketing_agent.agent import MarketingAgent, format_result_as_json, format_result_as_markdown
from marketing_agent.llm import create_llm


def load_brief_from_file(filepath: str) -> dict:
    """Load brief from a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Marketing Content Agent - Draft and validate marketing content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with a brief file (mock mode, no API key needed)
  python -m marketing_agent.cli --brief examples/coffee_brand.json --mock

  # Run with OpenAI API
  python -m marketing_agent.cli --brief examples/fitness_app.json

  # Generate for multiple channels
  python -m marketing_agent.cli --brief examples/coffee_brand.json --channels twitter facebook_post --mock

  # Save output to file
  python -m marketing_agent.cli --brief examples/coffee_brand.json --mock --output results.md
        """
    )
    
    parser.add_argument(
        "--brief",
        required=True,
        help="Path to JSON file containing the content brief"
    )
    
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use deterministic mock LLM (no API key required)"
    )
    
    parser.add_argument(
        "--channels",
        nargs="+",
        help="Additional channels to generate content for (e.g., twitter facebook_post)"
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum revision iterations (default: 3)"
    )
    
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini)"
    )
    
    parser.add_argument(
        "--output",
        help="Output file path (default: stdout). Use .json for JSON, .md for Markdown"
    )
    
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="markdown",
        help="Output format (default: markdown)"
    )
    
    args = parser.parse_args()
    
    load_dotenv()
    
    if not Path(args.brief).exists():
        print(f"Error: Brief file not found: {args.brief}", file=sys.stderr)
        sys.exit(1)
    
    try:
        brief = load_brief_from_file(args.brief)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in brief file: {e}", file=sys.stderr)
        sys.exit(1)
    
    required_fields = ["product", "audience", "channel"]
    missing = [f for f in required_fields if f not in brief]
    if missing:
        print(f"Error: Brief missing required fields: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
    
    try:
        llm = create_llm(mock=args.mock, model=args.model)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nSet OPENAI_API_KEY environment variable or use --mock flag", file=sys.stderr)
        sys.exit(1)
    
    agent = MarketingAgent(
        llm=llm,
        max_iterations=args.max_iterations,
        channels=args.channels,
    )
    
    print(f"Running Marketing Content Agent...", file=sys.stderr)
    print(f"Brief: {args.brief}", file=sys.stderr)
    print(f"Mode: {'Mock (offline)' if args.mock else f'OpenAI ({args.model})'}", file=sys.stderr)
    print(f"Max iterations: {args.max_iterations}", file=sys.stderr)
    print("", file=sys.stderr)
    
    result = agent.run(brief)
    
    output_format = args.format
    if args.output:
        ext = Path(args.output).suffix.lower()
        if ext == ".json":
            output_format = "json"
        elif ext == ".md":
            output_format = "markdown"
    
    if output_format == "json":
        output_text = format_result_as_json(result)
    else:
        output_text = format_result_as_markdown(result)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_text)
        print(f"Results saved to: {args.output}", file=sys.stderr)
    else:
        print(output_text)
    
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
