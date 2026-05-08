"""
main.py
Main entry point for the AI Content Creator.
Provides a CLI interface for running the content pipeline.

Usage:
  python main.py run --topic "Alert fatigue in SOC teams" --template blog_ciso
  python main.py monitor
  python main.py brief --topic "Zero trust implementation"
  python main.py list-templates
  python main.py kb-status
"""

import argparse
import sys
import os
from pathlib import Path

# Ensure src/ is on the path when running from project root
sys.path.insert(0, str(Path(__file__).parent))

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[Config] Loaded .env file")
except ImportError:
    pass  # python-dotenv optional


def cmd_run(args):
    """Run the full content pipeline."""
    from content_pipeline import ContentPipeline

    pipeline = ContentPipeline(
        knowledge_base_path=args.kb_path,
        output_dir=args.output_dir,
        auto_save=True,
    )

    topic = args.topic

    if not topic:
        print("\n🔍 Running market monitor to identify content opportunities...\n")
        monitor_response = pipeline.monitor()

        lines = monitor_response.content.split("\n")
        opportunities = [l for l in lines if l.strip().startswith("OPPORTUNITY")]

        print("\n📋 CONTENT OPPORTUNITIES:\n")
        for i, opp in enumerate(opportunities, 1):
            print(f"  [{i}] {opp.replace('OPPORTUNITY #', '').strip()}")

        print("\nChoose a number from the list, or type your own topic:")
        choice = input("Your choice: ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(opportunities):
            topic = opportunities[int(choice) - 1].replace("OPPORTUNITY #", "").strip()
            if ":" in topic:
                topic = topic.split(":", 1)[1].strip()
        else:
            topic = choice

        print(f"\n✅ Topic: '{topic}'")

    # Audience selection from IronVeil brand guidelines
    print("\n🎯 Select your target audience:")
    print("  [1] Security Directors & CISOs (Mid-Market)")
    print("  [2] SOC Analysts (Tier 2/3)")
    print("  [3] IT Directors / vCISOs (Channel Partners)")

    audience_choice = input("\nYour choice [1-3]: ").strip()

    template_map = {
        "1": "blog_post_ciso",
        "2": "blog_post_analyst",
        "3": "blog_post_ciso",
    }

    template = template_map.get(audience_choice, "blog_post_ciso")

    published = pipeline.run(
        topic=topic,
        template_name=template,
        word_count=args.word_count,
        skip_monitor=True,
        human_review=not args.no_review,
    )

    print(f"\n✅ Done! Content saved to: {published.output_file}")


def cmd_monitor(args):
    """Run just the monitor stage."""
    from content_pipeline import ContentPipeline

    pipeline = ContentPipeline(
        knowledge_base_path=args.kb_path,
        output_dir=args.output_dir,
    )

    response = pipeline.monitor()
    print("\n📊 MONITOR REPORT:\n")
    print(response.content)


def cmd_brief(args):
    """Generate a content brief for a topic."""
    from content_pipeline import ContentPipeline

    pipeline = ContentPipeline(
        knowledge_base_path=args.kb_path,
        output_dir=args.output_dir,
    )

    brief = pipeline.brief(topic=args.topic)
    print("\n📋 CONTENT BRIEF:\n")
    print(brief.raw_brief)


def cmd_list_templates(args):
    """List all available content templates."""
    from prompt_templates import list_templates

    templates = list_templates()
    print("\n📚 AVAILABLE TEMPLATES:\n")
    for t in templates:
        print(f"  [{t['name']}]")
        print(f"    Format:   {t['format']}")
        print(f"    Audience: {t['audience']}")
        print(f"    Notes:    {t['notes']}")
        print()


def cmd_kb_status(args):
    """Show knowledge base status and document inventory."""
    from knowledge_base import KnowledgeBase

    kb = KnowledgeBase(base_path=args.kb_path)
    state = kb.monitor_knowledge_state()

    print("\n📂 KNOWLEDGE BASE STATUS:\n")
    print(f"  Total Documents: {state['total_documents']}")
    print(f"  Primary KB ({state['primary_count']} docs): {', '.join(state['primary_categories'])}")
    print(f"  Secondary KB ({state['secondary_count']} docs): {', '.join(state['secondary_categories'])}")
    print(f"  Total Words: {state['total_words']:,}")
    print("\n  Documents:")
    for doc in state["documents"]:
        print(f"    [{doc['kb_type'].upper()}] {doc['filename']} — {doc['word_count']} words")


def main():
    parser = argparse.ArgumentParser(
        description="AI Content Creator — CyberContent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py run --topic "Why alert fatigue is a leadership problem"
  python main.py run --topic "Zero trust for mid-market" --template blog_analyst
  python main.py monitor
  python main.py brief --topic "AI-powered phishing threats"
  python main.py list-templates
  python main.py kb-status
        """
    )

    # Shared arguments
    parser.add_argument("--kb-path", default="knowledge_base", help="Path to knowledge base directory")
    parser.add_argument("--output-dir", default="output", help="Directory for generated content")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # run command
    run_parser = subparsers.add_parser("run", help="Run the full content pipeline")
    run_parser.add_argument("--topic", required=False, default=None, help="Content topic or angle")
    run_parser.add_argument(
        "--template", default="blog_post_ciso",
        choices=["blog_post_ciso", "blog_post_analyst", "linkedin_thought_leadership", "content_brief", "iterate_and_refine", "monitor_trends"],
        help="Content template to use"
    )
    run_parser.add_argument("--word-count", type=int, default=1600, help="Target word count")
    run_parser.add_argument("--skip-monitor", action="store_true", help="Skip market monitoring stage")
    run_parser.add_argument("--no-review", action="store_true", help="Skip human review step")
    run_parser.set_defaults(func=cmd_run)

    # monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Run market monitoring analysis")
    monitor_parser.set_defaults(func=cmd_monitor)

    # brief command
    brief_parser = subparsers.add_parser("brief", help="Generate a content brief")
    brief_parser.add_argument("--topic", required=True, help="Content topic")
    brief_parser.set_defaults(func=cmd_brief)

    # list-templates command
    list_parser = subparsers.add_parser("list-templates", help="List available prompt templates")
    list_parser.set_defaults(func=cmd_list_templates)

    # kb-status command
    kb_parser = subparsers.add_parser("kb-status", help="Show knowledge base status")
    kb_parser.set_defaults(func=cmd_kb_status)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
