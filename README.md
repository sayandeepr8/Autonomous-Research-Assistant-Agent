# 🔬 Autonomous Research Assistant

A **multi-agent AI system** that simulates the workflow of a real research analyst. Instead of merely answering prompts, the system autonomously plans research questions, retrieves real academic papers from arXiv, evaluates coverage completeness, identifies knowledge gaps, and generates structured literature review reports.

![Autonomous Research Assistant](https://img.shields.io/badge/python-3.12-blue) ![Flask](https://img.shields.io/badge/flask-3.1-green) ![Gemini](https://img.shields.io/badge/Gemini-2.0--flash-purple)

---

## 🏗️ Architecture

The system is built with an **agentic workflow architecture** featuring five specialized agents that work in concert:

```
┌─────────────────────────────────────────────────────────────┐
│                   RESEARCH ORCHESTRATOR                     │
│                                                             │
│  ┌──────────┐   ┌───────────┐   ┌──────────┐   ┌────────┐ │
│  │ 🧠       │   │ 📚        │   │ 🔬       │   │ 🧐     │ │
│  │ PLANNER  │──▸│ RETRIEVER │──▸│ ANALYZER │──▸│ CRITIC │ │
│  │          │   │           │   │          │   │        │ │
│  └──────────┘   └───────────┘   └──────────┘   └───┬────┘ │
│       ▲                                             │      │
│       │            ITERATIVE LOOP                   │      │
│       └─────────── (if gaps found) ─────────────────┘      │
│                                                             │
│                    ┌──────────┐                              │
│                    │ 📝       │                              │
│                    │ REPORTER │ ── Final Literature Review   │
│                    └──────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

### Agent Descriptions

| Agent | Role | Description |
|-------|------|-------------|
| 🧠 **Planner** | Research Planning | Decomposes a broad topic into structured research questions and arXiv search queries |
| 📚 **Retriever** | Paper Retrieval | Searches the arXiv API, retrieves paper metadata, and deduplicates results |
| 🔬 **Analyzer** | Synthesis & Analysis | Clusters papers thematically, maps coverage to questions, identifies methodologies |
| 🧐 **Critic** | Quality Evaluation | Scores coverage across 5 dimensions, identifies knowledge gaps, decides whether to iterate |
| 📝 **Reporter** | Report Generation | Compiles findings into a publication-quality Markdown literature review |

### Critic Loop (Meta-Reasoning)

The system incorporates a **critic loop** that enables iterative self-improvement:

1. After analysis, the **Critic Agent** evaluates coverage across: *breadth, depth, recency, methodology diversity, and question coverage*
2. If the overall score is below threshold (7/10) or critical gaps exist, the **Planner Agent** refines the search strategy
3. New queries are executed, and the cycle repeats (up to 3 iterations)
4. This meta-reasoning ensures comprehensive coverage before generating the final report

---

## ✨ Features

- **Autonomous Research Pipeline** — Set a topic and the system handles everything
- **Real arXiv Integration** — Retrieves actual academic papers via the arXiv API
- **Multi-Agent Architecture** — Five specialized agents with distinct responsibilities
- **Iterative Self-Evaluation** — Critic loop for coverage assessment and gap filling
- **Real-Time Progress Streaming** — SSE-based live updates showing agent workflow
- **Structured Literature Reviews** — Publication-quality Markdown reports
- **Interactive Dashboard** — Tabbed views for plan, analysis, critique, papers, and logs
- **Coverage Scoring** — Multi-dimensional scoring with visual ring charts
- **Knowledge Gap Identification** — Identifies missing areas with severity ratings
- **Thematic Clustering** — Groups papers into meaningful research themes

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A [Google Gemini API key](https://aistudio.google.com/apikey)

### Installation

1. **Clone the repository**
   ```bash
   cd Project1
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your API key**
   ```bash
   # Create a .env file
   cp .env.example .env
   
   # Edit .env and add your Gemini API key
   GEMINI_API_KEY=your_actual_api_key_here
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open in browser**
   Navigate to [http://localhost:5000](http://localhost:5000)

---

## 📁 Project Structure

```
Project1/
├── app.py                  # Flask application with API endpoints
├── config.py               # Configuration management
├── orchestrator.py          # Multi-agent workflow coordinator
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── README.md               # This file
│
├── agents/                 # Agent modules
│   ├── __init__.py
│   ├── base.py             # Base agent with Gemini integration
│   ├── planner.py          # Research planning agent
│   ├── retriever.py        # arXiv paper retrieval agent
│   ├── analyzer.py         # Paper analysis & synthesis agent
│   ├── critic.py           # Coverage evaluation agent
│   └── reporter.py         # Literature review generation agent
│
├── templates/
│   └── index.html          # Main web interface
│
└── static/
    ├── style.css           # Premium dark theme styles
    └── app.js              # Frontend logic & SSE handling
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python, Flask |
| AI Model | Google Gemini 2.0 Flash |
| Paper Source | arXiv API (Atom/XML) |
| Real-time Updates | Server-Sent Events (SSE) |
| Frontend | Vanilla HTML/CSS/JS |
| Feed Parsing | feedparser |

---

## 📊 Example Research Topics

Try these topics to see the system in action:

- *"Vision transformers for medical image analysis"*
- *"Reinforcement learning from human feedback (RLHF) in large language models"*
- *"Neural radiance fields (NeRF) and 3D scene reconstruction"*
- *"Diffusion models for text-to-image generation"*
- *"Graph neural networks for drug discovery"*
- *"Meta-learning and few-shot learning approaches"*

---

## 📝 License

This project is for educational and research purposes.
