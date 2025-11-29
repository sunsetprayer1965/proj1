# MASWE: Multi-Agent Software Engineering System

MASWE (Multi-Agent Software Engineering) is a research-oriented orchestration framework designed to simulate a complete software development lifecycle using autonomous LLM agents. It investigates whether structured collaboration among lightweight local LLMs (e.g., Qwen, DeepSeek) can approach the software engineering capabilities of large cloud models like GPT‑4 and Claude.

## Table of Contents

- Overview
- Architecture
- System Components
- Key Features
- Workflow Pipeline
- Installation & Usage
- Evaluation & Benchmarks
- Project Structure
- Contributing
- License

## Overview

MASWE runs inside a fully reproducible Docker environment and orchestrates a team of specialized agents—Product Manager, Architect, Developer, Reviewer—to convert natural language requirements into fully tested, executable software artifacts.

A core design advantage is its unified LLM Backend Layer, enabling seamless switching between local inference (Qwen, DeepSeek, Llama 3) and cloud inference (GPT‑4, Claude, Gemini).

## Architecture

MASWE implements a directed workflow where artifacts flow between agents in a structured cycle.

flowchart TD
    subgraph Input
        A[User Prompt / Issue]
    end

    subgraph Planning_Phase
        B[Product Manager] -->|PRD and Specs| C[System Architect]
        C -->|Design Docs and API| D[Developer Agent]
    end

    subgraph Development_Loop
        D -->|Pull Request| E[Reviewer / QA]
        E -->|Reject and Feedback| D
        E -->|Approve| F[Integration Pipeline]
    end

    subgraph Deployment_and_Eval
        F --> G[CI/CD and Packaging]
        F --> H[Evaluation: HumanEval and SWE-Bench]
    end

    A --> B

## System Components

| Role | Responsibility | Output |
|------|---------------|--------|
| Product Manager | Requirements engineering, user stories | PRD.md, requirements.txt |
| System Architect | System design, data structures, API | design.md, diagrams |
| Developer | Code implementation based on architect specs | Source code |
| Reviewer / QA | Static analysis, testing | Review report |
| Orchestrator | Agent routing, project state management | workflow_trace.json |

## Key Features

### 1. Hybrid Local/Cloud LLM Backend
- Optimized for Qwen2.5-Coder and DeepSeek-Coder locally
- Seamless switching to GPT‑4 or Claude
- Unified LLMClient for temperature, context window, and token usage

### 2. MetaGPT‑Style Orchestration
- Role–Action–Memory pattern
- Individual agent memory + global project state
- Asynchronous execution pipeline

### 3. Fully Reproducible Environments
- Complete Dockerization
- Volume-mounted workspace for persistent outputs
- Clean, isolated execution environment

### 4. Built-In Evaluation Suite
- Supports HumanEval
- Supports SWE-Bench‑Lite
- Produces pass@1, latency, and token-cost metrics

## Workflow Pipeline

1. Product Manager → Parses the task and generates PRD  
2. Architect → Converts PRD into technical design  
3. Developer → Generates code based on design  
4. Reviewer → Runs tests and returns feedback  
5. Integration → Merges code, formats, generates README  
6. Evaluation → Runs benchmarking suite  

## Project Structure

```
maswe/
├── maswe/
│   ├── run_experiment.py
│   ├── __init__.py
│   └── config.py
├── metagpt/
│   ├── roles/
│   ├── actions/
│   └── utils/
├── workspace/
│   └── [TIMESTAMP_ID]/
│       ├── src/
│       ├── docs/
│       └── logs/
├── docker/
│   └── Dockerfile
└── requirements.txt
```

## Installation & Usage

### Prerequisites
- Docker installed
- Optional API keys for cloud inference

### 1. Build the Docker Image

```bash
docker build -t maswe .
```

### 2. Run MASWE with Local LLMs

```bash
docker run --rm -it   -v $(pwd)/workspace:/app/workspace   maswe python maswe/run_experiment.py   --mode local   --model qwen2.5-coder   --task "Build a CLI-based Snake game in Python"
```

### 3. Run with GPT‑4

```bash
docker run --rm -it   -e OPENAI_API_KEY=sk-xxx   -v $(pwd)/workspace:/app/workspace   maswe python maswe/run_experiment.py   --mode cloud   --model gpt-4-turbo   --task "Create a FastAPI-based Todo API"
```

### 4. Run HumanEval Benchmark

```bash
docker run --rm -it   -v $(pwd)/workspace:/app/workspace   maswe python maswe/run_experiment.py   --eval humaneval   --n 50
```

## Evaluation & Benchmarks

Example `metrics.json`:

```json
{
  "task_id": "snake_game_001",
  "success": true,
  "model": "deepseek-coder:33b",
  "steps": 12,
  "cost": 0.0,
  "execution_time_sec": 145.2
}
```

## Contributing

1. Fork the repo  
2. Create a feature branch  
3. Commit changes  
4. Push  
5. Open PR  

