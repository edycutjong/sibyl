<div align="center">
  <h1>Sibyl 🔮</h1>
  <p><em>Retrieval-augmented forecasting agent for Prophet Arena — calibrated probability predictions with cost-tiered LLM routing.</em></p>
  <img src="docs/readme-hero.png" alt="Sibyl" width="100%">

  <br/>

  [![Live Demo](https://img.shields.io/badge/🚀_Live-Demo-06b6d4?style=for-the-badge)](https://github.com/edycutjong/sibyl)
  [![Pitch Video](https://img.shields.io/badge/🎬_Pitch-Video-ef4444?style=for-the-badge)](https://youtu.be/your-video)
  [![Pitch Deck](https://img.shields.io/badge/📊_Pitch-Deck-f59e0b?style=for-the-badge)](https://github.com/edycutjong/sibyl/pitch)
  [![Built for Prophet Hacks](https://img.shields.io/badge/Devpost-Prophet_Hacks-8b5cf6?style=for-the-badge)](https://prophethacks.devpost.com/)

  <br/>

  ![Python](https://img.shields.io/badge/Python_3.12-3776AB?style=flat&logo=python&logoColor=white)
  ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
  ![OpenAI](https://img.shields.io/badge/GPT--4o-412991?style=flat&logo=openai&logoColor=white)
  ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
  ![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=flat&logo=pytest&logoColor=white)
  [![CI](https://github.com/edycutjong/sibyl/actions/workflows/ci.yml/badge.svg)](https://github.com/edycutjong/sibyl/actions/workflows/ci.yml)

</div>

---

## 📸 See it in Action

<div align="center">
  <img src="docs/readme-hero.png" alt="Sibyl Demo" width="100%">
</div>

> **Predict accurately and efficiently.** Event → Classify → Retrieve Context → Anchor on Market → Select Model → Reason → Calibrate → Predict.

---

## 💡 The Problem & Solution
Current forecasting models struggle with nuanced topics due to lack of real-time context and high computational costs for simple queries.
**Sibyl** solves this by using a cost-tiered LLM routing system that balances accuracy and efficiency, anchoring predictions on current market prices.

**Key Features:**
- ⚡ **Cost-Tiered Routing:** Routes predictions to the cheapest suitable model (GPT-4o-mini, Gemini Flash, Claude Sonnet) based on confidence.
- 🔒 **Category-Aware Retrieval:** Uses Exa and Brave for optimized search queries depending on the category.
- 🎨 **Calibrated Predictions:** Uses Platt scaling to return accurate probability estimates.

## 🏗️ Architecture & Tech Stack

| Layer | Technology |
|---|---|
| **Runtime** | Python 3.12 |
| **Framework** | FastAPI + Uvicorn |
| **LLM** | litellm (OpenAI, Anthropic, Google) |
| **Search** | Exa API, Brave Search |
| **Calibration** | scikit-learn (Platt scaling) |
| **Cache** | diskcache |
| **Deploy** | Railway / Docker |

## 🏆 Sponsor Tracks Targeted
- **Prophet Arena** — Agent implementation and forecasting performance.
- **OpenAI** — Utilizing GPT-4o-mini for efficient predictions.

## 🚀 Getting Started

### Prerequisites
- Python ≥ 3.12

### Installation
1. Clone: `git clone https://github.com/edycutjong/sibyl.git`
2. Configure: `cp .env.example .env` and add your keys
3. Install: `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
4. Run: `uvicorn sibyl.server:app --port 8001`


## 🧪 Testing & CI
```bash
ruff check .          # Linting
pytest --cov          # Run tests with coverage
```

## 📁 Project Structure
```
sibyl/
├── docs/              # README assets (hero, screenshots)
├── sibyl/             # Core prediction pipeline and server
│   ├── server.py      # FastAPI dual-endpoint server
│   ├── agent.py       # Core prediction pipeline
│   └── model_router.py# Cost-tiered model selection
├── tests/             # Pytest test suite
├── .env.example       # Environment template
├── .github/           # CI workflows
└── README.md          # You are here
```

## 📄 License
[MIT](LICENSE) © 2026 Edy Cu

## 🙏 Acknowledgments
Built for Prophet Hacks. Thank you to the sponsors for the APIs and tools.
