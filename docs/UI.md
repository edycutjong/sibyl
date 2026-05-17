# OracleChain — UI Design Decisions

## No UI Needed

> **This hackathon has NO subjective judging.** Winners are determined purely by Brier score performance over a 2-week evaluation window. There is no demo day, no pitch, and no judge reviewing a dashboard.

## What We Build Instead

### 1. README with Architecture Diagram
The "UI" of this project is the README.md — it must be clear, comprehensive, and impressive enough for the Devpost project page and judge review.

Key sections:
- Architecture diagram (Mermaid)
- Performance benchmark table
- Cost analysis
- Setup instructions
- Design decisions

### 2. Terminal Output
The agent's "interface" is its terminal output:
```
[OracleChain] Event: Will the Fed raise rates? (Economics)
[OracleChain] Market anchor: 0.42
[OracleChain] Retrieved: 3 sources (CPI report, FedWatch, governor speech)
[OracleChain] Model: gemini-2.5-flash (medium confidence)
[OracleChain] Raw prediction: 0.28
[OracleChain] Calibrated: 0.31
[OracleChain] Response: {"probabilities": [{"market": "Yes", "probability": 0.31}, {"market": "No", "probability": 0.69}]}
[OracleChain] Latency: 4.2s | Cost: $0.0012
```

### 3. Stats Endpoint
Simple JSON endpoint at `GET /stats` for monitoring:
```json
{
  "predictions_total": 847,
  "avg_latency_ms": 3200,
  "total_cost_usd": 12.47,
  "uptime_pct": 99.8,
  "categories": {
    "Sports": 312, "Geopolitics": 201, "Economics": 178,
    "Science/Tech": 98, "Pop Culture": 58
  }
}
```

## Design Decisions

| Decision | Rationale |
|---|---|
| No frontend | Competition is judged by Brier score, not aesthetics |
| Rich logging | Terminal output IS the demo — make it informative |
| JSON stats endpoint | Enables monitoring during 2-week eval without building a dashboard |
| Mermaid diagrams in README | Visual architecture for Devpost page without building a UI |
