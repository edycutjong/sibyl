"""Sibyl — Calibration training script.

Usage:
  python scripts/calibrate.py [--events data/fixtures/resolved_events.json]

Trains the Platt scaling calibration model using historical resolved events.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Important: do not let the predictor load an existing calibration model
# otherwise we are training on already-calibrated data!
import sibyl.calibration
sibyl.calibration._CALIBRATION_MODEL_PATH = "data/models/calibration_temp.pkl"

from sibyl.agent import predict
from sibyl.calibration import train_calibration_model, _CALIBRATION_MODEL_PATH


async def main():
    events_path = sys.argv[1] if len(sys.argv) > 1 else "data/fixtures/resolved_events.json"

    if not Path(events_path).exists():
        print(f"❌ Events file not found: {events_path}")
        sys.exit(1)

    with open(events_path) as f:
        events = json.load(f)

    print(f"🔮 Sibyl Calibration Training — {len(events)} events")
    print("=" * 60)

    raw_probs = []
    actual_outcomes = []

    for i, event in enumerate(events):
        title = event.get("title", "Unknown")
        print(f"\n[{i + 1}/{len(events)}] {title[:70]}")

        try:
            # Predict
            result = await predict(event)

            # Extract raw 'yes' probability
            # We assume outcomes includes 'yes', or we find the probability for 'yes'
            p = 0.5
            for prob_obj in result.get("probabilities", []):
                if str(prob_obj.get("market")).lower() in ("yes", "1", "true"):
                    p = prob_obj.get("probability", 0.5)
                    break
            
            # Extract actual outcome
            actual = event.get("resolved_outcome", event.get("resolution"))
            if actual is not None:
                actual_binary = 1 if str(actual).lower() in ("yes", "1", "true") else 0
                
                raw_probs.append(p)
                actual_outcomes.append(actual_binary)
                
                print(f"   raw_p_yes={p:.4f} | actual={actual_binary}")
            else:
                print("   Skipped (no resolution data)")

        except Exception as err:
            print(f"   ❌ Error: {err}")

    # Train model
    print("\n" + "=" * 60)
    if not raw_probs:
        print("⚠️  No valid events with probabilities and resolutions found to train on.")
        sys.exit(1)

    print(f"📊 Training calibration model on {len(raw_probs)} events...")
    
    # We want to save to the real path
    sibyl.calibration._CALIBRATION_MODEL_PATH = "data/models/calibration.pkl"
    train_calibration_model(raw_probs, actual_outcomes, save_path="data/models/calibration.pkl")
    
    print("✅ Calibration training complete.")

if __name__ == "__main__":
    asyncio.run(main())
