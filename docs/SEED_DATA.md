# OracleChain — Seed Data Strategy

## Available Datasets (from `ai-prophet-datasets`)

Four sample datasets are published in the registry, each with one `v1.0.0` release:

| Dataset | Events | Resolved? | Categories | Use For |
|---|---|---|---|---|
| `sample-sports` | 16 | No | NBA/MLB playoffs, tennis, championships | Practice predict → evaluate loop |
| `sample-entertainment` | 13 | No | Eurovision, anime awards, Emmys, music charts | Multi-outcome practice |
| `sample-economics` | 13 | No | CPI, GDP, central bank rates, UST yields | Range-bucket questions |
| `sample-resolved` | 26 | **Yes** | Mixed (resolved outcomes with ground truth) | **Benchmarking + calibration training** |

**Total**: 68 events across 4 datasets, 26 with ground truth.

## How to Retrieve

```bash
# Install CLI
pip install ai-prophet

# Default: pulls sample-sports
prophet forecast retrieve -o data/fixtures/sports_events.json

# Other datasets
prophet forecast retrieve --dataset sample-entertainment -o data/fixtures/entertainment_events.json
prophet forecast retrieve --dataset sample-economics -o data/fixtures/economics_events.json

# Resolved dataset (needs --include-resolved flag)
prophet forecast retrieve \
    --dataset sample-resolved --include-resolved \
    -o data/fixtures/resolved_events.json
```

### Environment Variable Overrides
```bash
export PA_FORECAST_DATASET=sample-resolved           # Default dataset
export PA_FORECAST_DATASETS_REPO_PATH=./local-clone  # Offline mode
```

## Event Schema (Retrieved Format)

```json
{
  "event_ticker": "KXNBAGAME-26MAY15DETCLE",
  "market_ticker": "KXNBAGAME-26MAY15DETCLE",
  "title": "Will Cleveland beat Detroit in NBA Eastern Conference Game 6 on May 15, 2026?",
  "subtitle": null,
  "description": "If Cleveland wins the Game 6...",
  "category": "Sports",
  "rules": "If Cleveland wins the Game 6...",
  "close_time": "2026-05-15T20:00:00Z",
  "outcomes": ["Cleveland", "Detroit"],
  "resolved_outcome": null
}
```

### Resolved Outcome Format
```json
{
  "resolved_outcome": {
    "value": ["Anna Lena Ebster"],
    "resolved_at": "2026-05-13T17:02:27.064637+00:00",
    "source": "KXITFWMATCH-26MAY12NAJEBS"
  }
}
```

**Note**: `value` is **always a list of strings**, even for single outcomes. Multi-entry lists express "all of these resolved positive."

## ⚠️ Important Schema Notes

- `market_ticker` is the **join key** for all `prophet forecast` commands
- `close_time` is UTC — `prophet forecast predict` skips events past close_time
- `description` and `rules` are the same string in current samples — **feed `rules` to prompt verbatim**
- `outcomes` can be 2 (binary) or 20+ (multi-outcome like award nominees)

## Calibration Strategy

### Training Data: `sample-resolved` (26 events)
1. Run base agent (no calibration) on all 26 resolved events
2. Collect `(predicted_probability, actual_outcome)` pairs
3. Train Platt scaling (LogisticRegression) on these pairs
4. Validate with leave-one-out cross-validation (small dataset)

### Challenges
- **26 events is small** for calibration training
- Mitigations:
  - Use simpler calibration (histogram binning with 3-5 bins)
  - Use temperature scaling (single parameter) instead of full Platt
  - Bootstrap + aggregate calibration curves
  - If calibration degrades Brier score → fall back to raw probabilities

### Benchmark Flow
```bash
# 1. Retrieve resolved events
prophet forecast retrieve --dataset sample-resolved --include-resolved -o resolved.json

# 2. Run agent predictions
prophet forecast predict --local oraclechain.agent --events resolved.json -o predictions.json

# 3. Score against ground truth
prophet forecast evaluate --predictions predictions.json --events resolved.json
```

## Demo Events (for Screenshots/Video)

For demo recording, use one event from each category to show the full pipeline:

```json
[
  {"category": "Sports", "title": "Will Cleveland beat Detroit?", "outcomes": ["Cleveland", "Detroit"]},
  {"category": "Entertainment", "title": "Who will win Eurovision 2026?", "outcomes": ["Sweden", "Ukraine", "Italy", "France", "Spain", "Others"]},
  {"category": "Economics", "title": "Will CPI print above 3% in May?", "outcomes": ["Yes", "No"]},
  {"category": "Science", "title": "Will SpaceX complete Starship orbital flight by June?", "outcomes": ["Yes", "No"]},
  {"category": "Pop Culture", "title": "Will Taylor Swift break Hot 100 record?", "outcomes": ["Yes", "No"]}
]
```

## Cost Estimation

Given 2-week evaluation window with ~100-200 questions per day:
- **Cheap questions** (>85% or <15% market confidence): GPT-4o-mini → $0.0001/q → ~$0.28/2wk
- **Medium questions** (15-85%): Gemini Flash → $0.001/q → ~$2.80/2wk
- **Complex questions** (40-60%): Claude Sonnet → $0.005/q → ~$7.00/2wk
- **Retrieval API calls**: NewsAPI/FRED/ESPN → mostly free tier
- **Total estimated**: ~$10-20 for 2-week evaluation (well under $40 budget)
