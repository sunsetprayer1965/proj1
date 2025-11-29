# **MASWE: Multi-Agent Software Engineering System**

**MASWE** (Multi-Agent Software Engineering) is a research-oriented orchestration framework designed to simulate a complete software development lifecycle using autonomous LLM agents.

The core research question behind MASWE is: **Can structured collaboration among lightweight local LLMs (e.g., Qwen, DeepSeek) approach the software engineering performance of massive cloud models (GPT-4, Claude 3.5)?**

## **📑 Table of Contents**

* [Overview](https://www.google.com/search?q=%23-overview)  
* [Architecture](https://www.google.com/search?q=%23-architecture)  
* [System Components](https://www.google.com/search?q=%23-system-components)  
* [Key Features](https://www.google.com/search?q=%23-key-features)  
* [Workflow Pipeline](https://www.google.com/search?q=%23-workflow-pipeline)  
* [Installation & Usage](https://www.google.com/search?q=%23-installation--usage)  
* [Evaluation & Benchmarks](https://www.google.com/search?q=%23-evaluation--benchmarks)  
* [Project Structure](https://www.google.com/search?q=%23-project-structure)  
* [Contributing](https://www.google.com/search?q=%23-contributing)

## **🌟 Overview**

MASWE simulates a miniature software development company within a deterministic, Dockerized environment. It orchestrates a team of specialized agents—Product Manager, Architect, Developer, Reviewer—to convert natural language requirements into fully tested, executable code.

Unlike standard agent frameworks, MASWE abstracts the **LLM Backend Layer**, allowing seamless switching between:

* **Local Inference:** Ollama (Qwen2.5-Coder, DeepSeek-Coder, Llama 3\)  
* **Cloud Inference:** OpenAI (GPT-4), Anthropic (Claude), Google (Gemini)

## **🧱 Architecture**

The system utilizes a directed cyclic graph approach where artifacts (documents, code) are passed and refined between agents.

flowchart TD  
    subgraph Input  
    A\[User Prompt / Issue\]  
    end

    subgraph "Planning Phase"  
    B\[Product Manager\] \--\>|PRD & Specs| C\[System Architect\]  
    C \--\>|Design Docs & API| D\[Developer Agent\]  
    end

    subgraph "Development Loop"  
    D \--\>|Pull Request| E\[Reviewer / QA\]  
    E \--\>|Reject \+ Feedback| D  
    E \--\>|Approve| F\[Integration Pipeline\]  
    end

    subgraph "Deployment & Eval"  
    F \--\> G\[CI/CD & Packaging\]  
    F \--\> H\[Evaluation (HumanEval/SWE-Bench)\]  
    end

    A \--\> B

## **🧩 System Components**

| Role | Responsibility | Output |
| :---- | :---- | :---- |
| **Product Manager** | Requirements engineering, competitive analysis, user stories. | PRD.md, requirements.txt |
| **System Architect** | High-level system design, data structures, file paths, API definition. | design.md, class\_diagram.mmd |
| **Developer** | Implementation of logic based on Architect's specs. | Source Code (.py, .js, etc.) |
| **Reviewer / QA** | Static analysis, logic verification, compliance check against PRD. | Code Review Report, Feedback Loop |
| **Orchestrator** | Message passing, state management, container lifecycle. | workflow\_trace.json |

## **🔥 Key Features**

### **1\. Hybrid LLM Backend**

* **Local-First:** Optimized for Qwen2.5-Coder-7B and DeepSeek via Ollama for zero-cost development.  
* **Cloud-Ready:** Plug-and-play adapters for GPT-4o and Claude Sonnet when higher reasoning capabilities are required.  
* **Unified API:** A single LLMClient interface handles temperature, context window management, and token usage tracking across all providers.

### **2\. MetaGPT-Style Orchestration**

* Implements a structured "Role-Action-Memory" pattern.  
* Agents maintain individual context stacks and share a global "Project State."  
* Asynchronous execution pipeline for performance.

### **3\. Reproducible Environments**

* Entire lifecycle runs inside a **Docker** container.  
* Volume-mounted workspaces ensure that code generation is persistent, while the execution environment remains pristine.

### **4\. Built-in Evaluation Suite**

* Integrated **HumanEval** and **SWE-Bench-Lite** runners.  
* Automated calculation of pass@1, pass@k, and latency metrics.

## **🔄 Workflow Pipeline**

The system follows a strict linear logic with iterative feedback loops:

1. **PM Analysis:** Reads the task, generates a User Requirement Document (URD) and Product Requirement Document (PRD).  
2. **Architectural Design:** Converts the PRD into a technical design, defining file structures and class hierarchies.  
3. **Development:** The Developer Agent writes code strictly adhering to the Architect's file paths.  
4. **Review Cycle:**  
   * The Reviewer analyzes the code.  
   * If issues are found: Sends specific instructions back to the Developer.  
   * If passed: Merges to the release branch.  
5. **Integration:** Generates README.md, installs dependencies, and formats code.  
6. **Evaluation:** Runs the specified benchmark suite.

## **🛠 Project Structure**

maswe/  
├── maswe/  
│   ├── run\_experiment.py     \# Entry point for orchestration  
│   ├── \_\_init\_\_.py  
│   └── config.py             \# LLM settings  
├── metagpt/  
│   ├── roles/                \# Agent definitions (PM.py, Architect.py...)  
│   ├── actions/              \# Specific skills (write\_prd.py, write\_code.py...)  
│   └── utils/                \# Git ops, Mermaid rendering, Cost calc  
├── workspace/                \# OUTPUT DIR (Volume mounted)  
│   ├── \[TIMESTAMP\_ID\]/  
│   │   ├── src/              \# Generated code  
│   │   ├── docs/             \# Generated PRD/Design docs  
│   │   └── logs/             \# Agent thought traces  
├── docker/  
│   └── Dockerfile            \# Environment definition  
└── requirements.txt

## **🚀 Installation & Usage**

### **Prerequisites**

* Docker Desktop installed and running.  
* (Optional) API Keys for OpenAI/Anthropic if running in Cloud Mode.

### **1\. Build the Image**

docker build \-t maswe .

### **2\. Run a Coding Task**

To generate a project using **Local LLMs** (requires Ollama running on host or inside container):

docker run \--rm \-it \\  
  \-v $(pwd)/workspace:/app/workspace \\  
  maswe python maswe/run\_experiment.py \\  
  \--mode local \\  
  \--model qwen2.5-coder \\  
  \--task "Build a CLI-based Snake game using Python and Curses"

To use **GPT-4**:

docker run \--rm \-it \\  
  \-e OPENAI\_API\_KEY=sk-proj-... \\  
  \-v $(pwd)/workspace:/app/workspace \\  
  maswe python maswe/run\_experiment.py \\  
  \--mode cloud \\  
  \--model gpt-4-turbo \\  
  \--task "Create a REST API for a Todo list using FastAPI"

### **3\. Run Evaluation Benchmark**

docker run \--rm \-it \\  
  \-v $(pwd)/workspace:/app/workspace \\  
  maswe python maswe/run\_experiment.py \\  
  \--eval humaneval \\  
  \--n 50

## **📊 Evaluation & Benchmarks**

MASWE automatically generates a metrics.json file after every run.

| Metric | Description |
| :---- | :---- |
| **Pass@1** | Percentage of unit tests passed on the first attempt. |
| **Agent Steps** | Number of iterations required in the PM → Dev → Reviewer loop. |
| **Latency** | End-to-end time for task completion (Local vs. Cloud). |
| **Token Cost** | Calculated usage (Input/Output tokens) based on current API pricing. |

**Example Output:**

{  
  "task\_id": "snake\_game\_001",  
  "success": true,  
  "model": "deepseek-coder:33b",  
  "steps": 12,  
  "cost": 0.0,  
  "execution\_time\_sec": 145.2  
}

## **🤝 Contributing**

Contributions are welcome\! This framework is intended for research on multi-agent collaboration.

1. Fork the repository.  
2. Create your feature branch (git checkout \-b feature/AmazingFeature).  
3. Commit your changes (git commit \-m 'Add some AmazingFeature').  
4. Push to the branch (git push origin feature/AmazingFeature).  
5. Open a Pull Request.

## **📄 License**

Distributed under the MIT License. See LICENSE for more information.