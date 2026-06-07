# XBOW Validation Benchmarks Integration

Runs Claude Code security agents against [XBOW's 104 CTF-style validation benchmarks](https://github.com/xbow-engineering/validation-benchmarks).

## What is XBOW?

XBOW validation-benchmarks is a collection of **104 Dockerized web security challenges** designed to evaluate offensive security tools. Each benchmark is a real-world-style web application with an intentional vulnerability. The agent must discover and exploit the vulnerability to capture a hidden flag.

**Vulnerability types covered**: SQL Injection, XSS, IDOR, SSRF, Command Injection, Path Traversal, Authentication Bypass, Deserialization, and more.

**Difficulty levels**: 1 (Easy), 2 (Medium), 3 (Hard)

## Prerequisites

- **Docker** & **Docker Compose** (v2 plugin)
- **Claude CLI** (`npm install -g @anthropic-ai/claude-cli`)
- **Python 3.9+**
- **openssl** (for flag generation)

## Quick Start

```bash
# 1. Clone the XBOW benchmarks
python benchmarks/xbow/run_xbow.py --setup

# 2. Check prerequisites
python benchmarks/xbow/run_xbow.py --check

# 3. List available benchmarks
python benchmarks/xbow/run_xbow.py --list

# 4. Run a single benchmark (recommended first)
python benchmarks/xbow/run_xbow.py --benchmark XBEN-001-24

# 5. Run all easy benchmarks
python benchmarks/xbow/run_xbow.py --level 1

# 6. Run all benchmarks with skills
python benchmarks/xbow/run_xbow.py

# 7. Run without skills for baseline comparison
python benchmarks/xbow/run_xbow.py --vanilla
```

## Step-by-Step Walkthrough

### Step 1: Setup

```bash
cd /path/to/communitytools

# Clone the XBOW benchmark repo to /tmp
python benchmarks/xbow/run_xbow.py --setup

# Verify Docker, Docker Compose, Claude CLI, and openssl are installed
python benchmarks/xbow/run_xbow.py --check
```

### Step 2: Explore Available Benchmarks

```bash
# List all 104 benchmarks with levels and tags
python benchmarks/xbow/run_xbow.py --list

# Filter by difficulty
python benchmarks/xbow/run_xbow.py --list --level 1    # Easy only
python benchmarks/xbow/run_xbow.py --list --level 3    # Hard only

# Filter by vulnerability type
python benchmarks/xbow/run_xbow.py --list --tags xss
python benchmarks/xbow/run_xbow.py --list --tags sqli,idor
```

### Step 3: Run Your First Benchmark

Start with a single benchmark to verify everything works:

```bash
# Run one benchmark with your pentest skills loaded
python benchmarks/xbow/run_xbow.py --benchmark XBEN-001-24

# What happens:
# 1. Docker builds the vulnerable app (IDOR trading platform)
# 2. App starts on a random local port
# 3. Claude agent is launched with the challenge description
# 4. Agent explores, identifies, and exploits the vulnerability
# 5. Script checks if the flag was captured
# 6. Docker containers are cleaned up
# 7. Results saved to benchmarks/xbow/results/
```

### Step 4: Run Benchmark Suites

```bash
# Run all easy benchmarks
python benchmarks/xbow/run_xbow.py --level 1

# Run only XSS challenges
python benchmarks/xbow/run_xbow.py --tags xss

# Run all benchmarks (this takes a while)
python benchmarks/xbow/run_xbow.py

# Run with more time per challenge (15 min instead of default 10)
python benchmarks/xbow/run_xbow.py --timeout 900

# Run 3 benchmarks in parallel (needs adequate Docker resources)
python benchmarks/xbow/run_xbow.py --parallel 3
```

### Step 5: Compare Skills vs Vanilla

```bash
# Run WITH your pentest skills
python benchmarks/xbow/run_xbow.py --level 1

# Run WITHOUT skills (baseline)
python benchmarks/xbow/run_xbow.py --level 1 --vanilla

# Compare the results in benchmarks/xbow/results/
ls benchmarks/xbow/results/
# xbow_results_skills_20260227_143022.json
# xbow_results_vanilla_20260227_150511.json
```

### Step 6: Analyze Results

Results are saved as JSON in `benchmarks/xbow/results/`. Each file contains:

```json
{
  "timestamp": "2026-02-27T14:30:22",
  "benchmark": "xbow-validation-benchmarks",
  "mode": "skills",
  "summary": {
    "total": 104,
    "flags_captured": 42,
    "capture_rate": 0.404,
    "completed": 98,
    "timed_out": 6,
    "errors": 0,
    "avg_duration_seconds": 245.3
  },
  "results": [...]
}
```

## How It Works

```
┌─────────────────────────────────────────────────────┐
│                   run_xbow.py                        │
│                                                      │
│  1. Clone XBOW repo (/tmp/xbow-validation-benchmarks)│
│  2. Discover benchmarks (benchmark.json files)       │
│  3. For each benchmark:                              │
│     a. docker compose build --build-arg FLAG=...     │
│     b. docker compose up -d --wait                   │
│     c. Find mapped port                              │
│     d. Launch Claude agent with challenge prompt     │
│     e. Check if agent output contains the flag       │
│     f. docker compose down                           │
│  4. Aggregate results & save JSON                    │
└─────────────────────────────────────────────────────┘
```

## CLI Reference

| Flag | Description | Default |
|------|-------------|---------|
| `--setup` | Clone XBOW repo to /tmp | - |
| `--check` | Verify prerequisites | - |
| `--list` | List available benchmarks | - |
| `--benchmark ID` | Run specific benchmark | All |
| `--level N` | Filter by level (1/2/3) | All |
| `--tags t1,t2` | Filter by vuln tags | All |
| `--parallel N` | Parallel workers | 1 |
| `--timeout N` | Seconds per benchmark | 600 |
| `--vanilla` | Run without skills | false |
| `--skip-auth-check` | Skip Claude auth check | false |
| `--dry-run` | Show what would run | false |

## Output Structure

```
benchmarks/xbow/
├── run_xbow.py                 # Main runner script
├── README.md                   # This file
└── results/
    ├── run_20260227/           # Per-run output directories
    │   ├── XBEN-001-24/
    │   │   ├── prompt.txt      # Agent prompt
    │   │   └── claude_output.txt
    │   └── XBEN-002-24/
    │       └── ...
    ├── xbow_results_skills_20260227_143022.json
    └── xbow_results_vanilla_20260227_150511.json
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Docker not found | Install Docker Desktop |
| Claude auth fails | Run from Terminal.app (not VS Code), run `claude login` |
| Build timeout | Increase timeout: `--timeout 900` |
| Port conflicts | Stop other Docker containers: `docker ps` then `docker stop <id>` |
| Out of disk space | Clean Docker: `docker system prune -a` |
