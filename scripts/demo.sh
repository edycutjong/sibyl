#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# Sibyl — Live Demo Script
# Runs through all API endpoints with formatted output
# Usage: bash scripts/demo.sh
# ═══════════════════════════════════════════════════════════
set -uo pipefail

BASE_URL="${SIBYL_URL:-http://localhost:8001}"
CYAN='\033[0;36m'
GREEN='\033[0;32m'
AMBER='\033[0;33m'
RED='\033[0;31m'
VIOLET='\033[0;35m'
DIM='\033[0;90m'
BOLD='\033[1m'
RESET='\033[0m'

banner() {
  echo ""
  echo -e "${CYAN}${BOLD}"
  cat << 'EOF'
  ███████╗██╗██████╗ ██╗   ██╗██╗
  ██╔════╝██║██╔══██╗╚██╗ ██╔╝██║
  ███████╗██║██████╔╝ ╚████╔╝ ██║
  ╚════██║██║██╔══██╗  ╚██╔╝  ██║
  ███████║██║██████╔╝   ██║   ███████╗
  ╚══════╝╚═╝╚═════╝    ╚═╝   ╚══════╝
EOF
  echo -e "${RESET}"
  echo -e "${DIM}  The oracle that knows what it doesn't know.${RESET}"
  echo -e "${DIM}  ═══════════════════════════════════════════${RESET}"
  echo ""
}

section() {
  echo ""
  echo -e "${VIOLET}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo -e "${VIOLET}${BOLD}  $1${RESET}"
  echo -e "${VIOLET}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo ""
}

step() {
  echo -e "  ${CYAN}❯${RESET} ${BOLD}$1${RESET}"
  echo ""
}

pause() {
  echo -e "  ${DIM}Press Enter to continue...${RESET}"
  read -r
  clear
}

pretty_json() {
  python3 -m json.tool 2>/dev/null | sed 's/^/    /'
}

api_call() {
  local method="$1" url="$2" data="${3:-}"
  local token="${SIBYL_TOKEN:-sibyl-secret-token}"
  local response
  if [ -n "$data" ]; then
    response=$(curl -s --max-time 60 -X "$method" "$url" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $token" \
      -d "$data" 2>&1) || true
  else
    response=$(curl -s --max-time 10 "$url" \
      -H "Authorization: Bearer $token" 2>&1) || true
  fi
  if [ -z "$response" ]; then
    echo -e "    ${RED}✗ No response (timeout or connection error)${RESET}"
  elif echo "$response" | python3 -m json.tool > /dev/null 2>&1; then
    echo "$response" | pretty_json
  else
    echo -e "    ${RED}✗ Error: ${response}${RESET}"
  fi
}

# ─────────────────────────────────────────────────────────
# Pre-flight check
# ─────────────────────────────────────────────────────────
preflight() {
  echo -e "  ${DIM}Checking server at ${BASE_URL}...${RESET}"
  if ! curl -sf "${BASE_URL}/health" > /dev/null 2>&1; then
    echo -e "  ${AMBER}⟳ Server not running — starting uvicorn...${RESET}"
    bash scripts/run_server.sh > /tmp/sibyl-server.log 2>&1 &
    SERVER_PID=$!
    echo -e "  ${DIM}  PID: ${SERVER_PID}${RESET}"

    for i in $(seq 1 30); do
      if curl -sf "${BASE_URL}/health" > /dev/null 2>&1; then
        break
      fi
      sleep 0.5
    done

    if ! curl -sf "${BASE_URL}/health" > /dev/null 2>&1; then
      echo -e "  ${RED}✗ Server failed to start after 15s${RESET}"
      echo -e "  ${DIM}  Check /tmp/sibyl-server.log${RESET}"
      exit 1
    fi
    echo -e "  ${GREEN}✓ Server started${RESET}"
  else
    echo -e "  ${GREEN}✓ Server already running${RESET}"
  fi
  echo ""
}

# ─────────────────────────────────────────────────────────
# Demo Steps
# ─────────────────────────────────────────────────────────

demo_health() {
  section "1/6 — Health Check"
  step "GET /health"
  api_call GET "${BASE_URL}/health"
  echo ""
}

demo_sports() {
  section "2/6 — Sports Prediction"
  step "POST /predict — Will the Lakers win the NBA championship?"
  echo -e "  ${DIM}Domain: Sports → Cost-optimized routing${RESET}"
  echo ""
  api_call POST "${BASE_URL}/predict" '{"event_title":"Will the Lakers win the NBA championship?","description":"2025-26 NBA season"}'
  echo ""
}

demo_geo() {
  section "3/6 — Geopolitics Prediction"
  step "POST /predict — Will France hold early elections?"
  echo -e "  ${AMBER}Domain: Geopolitics → Claude Sonnet 4 (nuance override)${RESET}"
  echo ""
  api_call POST "${BASE_URL}/predict" '{"event_title":"Will France hold early legislative elections within 6 months?","description":"Minority coalition government, no-confidence motion pending"}'
  echo ""
}

demo_econ() {
  section "4/6 — Economics Prediction"
  step "POST /predict — Will the Fed cut rates in Q3 2026?"
  echo -e "  ${DIM}Domain: Economics → Tiered routing${RESET}"
  echo ""
  api_call POST "${BASE_URL}/predict" '{"event_title":"Will the Federal Reserve cut interest rates in Q3 2026?","description":"Current fed funds rate at 4.25-4.50%"}'
  echo ""
}

demo_stats() {
  section "5/6 — Cost & Performance Stats"
  step "GET /stats"
  api_call GET "${BASE_URL}/stats"
  echo ""
}

demo_bench() {
  section "6/6 — Calibration Benchmark"
  step "python scripts/bench.py"
  echo -e "  ${DIM}Running Brier score evaluation on resolved events...${RESET}"
  echo ""
  python3 scripts/bench.py 2>&1 | sed 's/^/    /' || echo -e "    ${RED}✗ Bench failed${RESET}"
  echo ""
}

# ─────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────
main() {
  # Clear screen and set terminal window title
  clear
  printf '\033]0;\xf0\x9f\x94\xae Sibyl \xe2\x80\x94 Live Demo\007'

  banner
  preflight

  echo -e "  ${BOLD}Demo Mode: ${GREEN}Interactive${RESET}"
  echo -e "  ${DIM}Each step pauses. Press Enter to advance.${RESET}"
  echo ""
  pause

  banner
  demo_health
  pause

  banner
  demo_sports
  pause

  banner
  demo_geo
  pause

  banner
  demo_econ
  pause

  banner
  demo_stats
  pause

  banner
  demo_bench

  echo ""
  echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo -e "${GREEN}${BOLD}  ✓ Demo Complete${RESET}"
  echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo ""
  echo -e "  ${DIM}Sibyl — Built for Prophet Arena${RESET}"
  echo -e "  ${CYAN}sibyl.edycu.dev${RESET}"
  echo ""
}

main "$@"
