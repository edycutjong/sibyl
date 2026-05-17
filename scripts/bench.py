"""Sibyl — Brier score benchmarking script.

Usage:
  python scripts/bench.py [--events data/fixtures/resolved_events.json]

Runs the agent on resolved events and computes Brier score.
"""

import asyncio
import json
import sys
from pathlib import Path


async def main():
    """Run benchmark against resolved events."""
    # Default to resolved events
    events_path = sys.argv[1] if len(sys.argv) > 1 else "data/fixtures/resolved_events.json"

    if not Path(events_path).exists():
        print(f"❌ Events file not found: {events_path}")
        print("   Run: prophet forecast retrieve --dataset sample-resolved --include-resolved -o data/fixtures/resolved_events.json")
        sys.exit(1)

    with open(events_path) as f:
        events = json.load(f)

    print(f"🔮 Sibyl Benchmark — {len(events)} events")
    print("=" * 60)

    # Import agent
    from sibyl.agent import predict, startup

    startup()

    brier_scores: list[float] = []

    for i, event in enumerate(events):
        title = event.get("title", "Unknown")
        print(f"\n[{i + 1}/{len(events)}] {title[:70]}")

        try:
            result = await predict(event)

            # For binary events with known resolution
            if "p_yes" in result:
                p = result["p_yes"]
                # If event has resolution info
                actual = event.get("resolved_outcome", event.get("resolution"))
                if actual is not None:
                    actual_binary = 1 if str(actual).lower() in ("yes", "1", "true") else 0
                    brier = (p - actual_binary) ** 2
                    brier_scores.append(brier)
                    print(f"   p_yes={p:.4f} | actual={actual_binary} | brier={brier:.4f}")
                else:
                    print(f"   p_yes={p:.4f} (no resolution data)")
            else:
                probs = result.get("probabilities", [])
                print(f"   probabilities: {probs}")

        except Exception as err:
            print(f"   ❌ Error: {err}")

    # Summary
    print("\n" + "=" * 60)
    if brier_scores:
        avg_brier = sum(brier_scores) / len(brier_scores)
        print(f"📊 Average Brier Score: {avg_brier:.4f}")
        print(f"   Events scored: {len(brier_scores)}/{len(events)}")
        print(f"   Lower is better (0.0 = perfect, 0.25 = coin flip)")
    else:
        print("⚠️  No events with resolution data for scoring")


if __name__ == "__main__":
    asyncio.run(main())
