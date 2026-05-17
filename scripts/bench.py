"""Sibyl — Brier score benchmarking script.

Usage:
  python scripts/bench.py [--events data/fixtures/resolved_events.json]

Runs the agent on resolved events and computes Brier score
with p50/p95 percentile breakdown.
"""

import asyncio
import json
import sys
from pathlib import Path

import numpy as np


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
    category_scores: dict[str, list[float]] = {}
    errors = 0

    for i, event in enumerate(events):
        title = event.get("title", "Unknown")
        category = event.get("category", "Other")
        print(f"\n[{i + 1}/{len(events)}] {title[:70]}")

        try:
            result = await predict(event)

            # Extract resolved outcome
            resolved = event.get("resolved_outcome", {})
            actual_values = resolved.get("value", []) if isinstance(resolved, dict) else []

            if not actual_values:
                # Try flat format
                flat_resolved = event.get("resolution")
                if flat_resolved is not None:
                    actual_values = [str(flat_resolved)]

            if not actual_values:
                print(f"   ⚠️  No resolution data — skipping")
                continue

            # Compute Brier score across all outcomes
            probs = result.get("probabilities", [])
            brier = 0.0
            for prob_obj in probs:
                market = prob_obj.get("market", "")
                p = prob_obj.get("probability", 0.5)
                actual = 1.0 if market in actual_values else 0.0
                brier += (p - actual) ** 2

            # Normalize by number of outcomes
            n_outcomes = max(1, len(probs))
            brier /= n_outcomes

            brier_scores.append(brier)

            # Track by category
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(brier)

            winning = actual_values[0] if actual_values else "?"
            print(f"   brier={brier:.4f} | resolved={winning}")

        except Exception as err:
            errors += 1
            print(f"   ❌ Error: {err}")

    # ── Summary ───────────────────────────────────────────────
    print("\n" + "=" * 60)
    if brier_scores:
        scores = np.array(brier_scores)
        avg = float(np.mean(scores))
        p50 = float(np.percentile(scores, 50))
        p75 = float(np.percentile(scores, 75))
        p95 = float(np.percentile(scores, 95))
        best = float(np.min(scores))
        worst = float(np.max(scores))

        print(f"📊 Brier Score Summary")
        print(f"   Events scored : {len(brier_scores)}/{len(events)}")
        print(f"   Errors        : {errors}")
        print()
        print(f"   ┌────────────┬──────────┐")
        print(f"   │  Metric    │  Score   │")
        print(f"   ├────────────┼──────────┤")
        print(f"   │  Mean      │  {avg:.4f}  │")
        print(f"   │  p50       │  {p50:.4f}  │")
        print(f"   │  p75       │  {p75:.4f}  │")
        print(f"   │  p95       │  {p95:.4f}  │")
        print(f"   │  Best      │  {best:.4f}  │")
        print(f"   │  Worst     │  {worst:.4f}  │")
        print(f"   └────────────┴──────────┘")
        print()
        print(f"   (Lower is better: 0.0 = perfect, 0.25 = coin flip)")

        # Per-category breakdown
        if category_scores:
            print()
            print(f"   📂 Per-Category Breakdown:")
            for cat, cat_scores in sorted(category_scores.items()):
                cat_arr = np.array(cat_scores)
                print(f"      {cat:20s} n={len(cat_scores):2d}  mean={float(np.mean(cat_arr)):.4f}  p50={float(np.percentile(cat_arr, 50)):.4f}")
    else:
        print("⚠️  No events with resolution data for scoring")


if __name__ == "__main__":
    asyncio.run(main())

