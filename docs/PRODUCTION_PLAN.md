# OracleChain — Production & Deployment Plan

## Deployment Target

**Platform**: Railway (preferred) or Fly.io
**Reason**: Always-on container required for 2-week continuous evaluation window (May 17 → May 31)

## Architecture

```
Railway Container
├── FastAPI (uvicorn)
│   ├── POST /chat/completions  ← Prophet Arena calls this (auto-eval)
│   ├── POST /predict           ← CLI calls this (--agent-url)
│   ├── GET /health             ← Uptime monitoring
│   └── GET /stats              ← Cost/performance tracking
├── diskcache/                  ← Response cache (ephemeral)
├── models/calibration.pkl      ← Pre-trained Platt scaling model
└── .env                        ← API keys (Railway env vars)
```

## Deployment Steps

### 1. Containerize (Dockerfile)
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY oraclechain/ oraclechain/
COPY data/models/ data/models/

EXPOSE 8001
CMD ["uvicorn", "oraclechain.server:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 2. Railway Deploy
```bash
# Create project + deploy
railway init
railway up

# Set environment variables
railway variables set PA_SERVER_API_KEY=prophet_xxx
railway variables set PA_SERVER_URL=https://api.aiprophet.dev
railway variables set OPENAI_API_KEY=sk-...
railway variables set ANTHROPIC_API_KEY=sk-ant-...
railway variables set GOOGLE_API_KEY=AIza...
railway variables set EXA_API_KEY=...
railway variables set BEARER_TOKEN=oraclechain-secret-token-xxx

# Generate domain
railway domain
```

### 3. Verify Endpoint
```bash
# Health check
curl https://<domain>/health

# Test prediction (OpenAI-compatible)
curl -X POST https://<domain>/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer oraclechain-secret-token-xxx" \
  -d '{
    "model": "oraclechain-v1",
    "messages": [{"role": "user", "content": "Predict: Will Cleveland beat Detroit? Outcomes: Cleveland, Detroit"}],
    "max_tokens": 512,
    "temperature": 0.1
  }'
```

### 4. ⚡ Onboard to Prophet Arena
1. Go to `prophetarena.co/onboarding`
2. Enter endpoint URL: `https://<railway-domain>/chat/completions`
3. Enter model name: `oraclechain-v1`
4. Enter bearer token: `oraclechain-secret-token-xxx`
5. Run the onboarding test — verify it passes
6. Submit! 🚀

## Monitoring Strategy (2-Week Window)

### Daily Checks
- [ ] Health endpoint responds 200
- [ ] `/stats` shows reasonable cost accumulation
- [ ] No error spikes in Railway logs

### Weekly Review
- [ ] Check Prophet Arena leaderboard position
- [ ] Review API cost burn rate (target: < $40 total)
- [ ] Check for timeout patterns (p95 < 30s)

### Alert Thresholds
| Metric | Warning | Action |
|---|---|---|
| Response time p95 | > 20s | Check retrieval API latency, consider caching |
| Error rate | > 5% | Check API key quotas, add fallbacks |
| Daily API cost | > $5/day | Lower model tier thresholds, increase caching TTL |
| Container restarts | > 3/day | Check memory limits, add health checks |

## Cost Budget

| Component | Estimated 2-Week Cost |
|---|---|
| Railway hosting | $0-5 (free tier or minimal) |
| OpenAI (GPT-4o-mini) | $0.28-1.00 |
| Google (Gemini Flash) | $1.00-3.00 |
| Anthropic (Claude Sonnet) | $3.00-10.00 |
| Exa Search (SDK SearchClient) | $0-5.00 (free tier) |
| **Total** | **$5-25** |

## Failure Modes & Mitigations

| Failure | Impact | Mitigation |
|---|---|---|
| LLM API down | Predictions fail | Fallback to cheaper model, then to keyword-based heuristic |
| Railway crash | Agent offline | Auto-restart, stateless design (no state to lose) |
| API key quota exceeded | Predictions fail | Cost-tier routing, caching, rate limiting |
| Retrieval timeout | Slower predictions | Timeout after 5s, continue with LLM-only (no retrieval) |
| Evaluation harness changes format | Bad responses | Parse defensively, log unparseable prompts |

## Post-Submission (Evaluation Window)

The agent runs autonomously for 2 weeks. During this time:
- **DO**: Monitor health, check leaderboard, review costs
- **DO**: Fix critical bugs (minimal changes allowed per rules)
- **DON'T**: Retrain on evaluation questions (explicitly prohibited)
- **DON'T**: Make major architectural changes
- **DON'T**: Access non-public benchmark data
