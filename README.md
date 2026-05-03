
# Codebase Brain 🧠

> **Stop wasting 30 minutes every time you ask AI about your code. Give AI assistants permanent memory.**

[![🎥 Watch Demo](https://img.shields.io/badge/🎥_Watch-2--Min_Demo-red?style=for-the-badge)](https://youtu.be/W-TUSyk-O8U?si=99irgwXUQteszmbZ)
[![🚀 Try Live](https://img.shields.io/badge/🚀_Try-Live_Demo-0f62fe?style=for-the-badge)](https://neetagrg.github.io/codebase-brain/watsonx-query.html)

[![Powered by IBM watsonx.ai](https://img.shields.io/badge/Powered%20by-IBM%20watsonx.ai-0f62fe)](https://www.ibm.com/watsonx)
[![Accuracy](https://img.shields.io/badge/AI_Accuracy-94%25-success)](docs/CASE_STUDY.md)
[![ROI](https://img.shields.io/badge/First_Year_ROI-22,200%25-green)](docs/CASE_STUDY.md)
[![Validated](https://img.shields.io/badge/Domains_Validated-4-blue)](examples/)
[![Lines](https://img.shields.io/badge/Lines_Covered-160K+-orange)](docs/CASE_STUDY.md)

## 🎯 The Problem

**Developers waste 30 minutes per session explaining their codebase to AI assistants.**

Every time you start a new chat, you re-explain the architecture, signal chains, and gotchas. The AI finally understands. Session ends. Tomorrow, you start over.

**In a 10-person team, this compounds to 40 hours/month of wasted context re-establishment.**

## ⚡ The Solution

**One command gives any codebase permanent AI memory.**

Codebase Brain generates three artifacts that make your codebase instantly understandable to any AI:

| Artifact | What It Does | Impact |
|----------|-------------|---------|
| **AGENTS.md** | Complete system map with failure modes | 60-second onboarding |
| **Slash Commands** | Executable debugging workflows | 88% faster debugging |
| **Domain Skill** | AI becomes instant expert | 94% answer accuracy |

## 🎥 Watch It Work (2 Minutes)

[![Codebase Brain Demo](https://img.youtube.com/vi/W-TUSyk-O8U/maxresdefault.jpg)](https://youtu.be/W-TUSyk-O8U?si=99irgwXUQteszmbZ)

**[▶️ Watch the 2-minute demo](https://youtu.be/W-TUSyk-O8U?si=99irgwXUQteszmbZ)** • **[🚀 Try live watsonx.ai queries](https://neetagrg.github.io/codebase-brain/watsonx-query.html)** • **[📊 See before/after comparison](https://neetagrg.github.io/codebase-brain/comparison.html)**

---

## The Problem

Large codebases fail not from code errors, but from **context errors**.

A developer changes file A, not knowing it breaks file B. They ask an AI for help—spending 30 minutes explaining the architecture. The AI finally understands. Session ends. Tomorrow, they start over.

**In a 10-person team, this compounds to 40 hours/month of wasted context re-establishment.**

---

## The Solution

Codebase Brain generates three permanent artifacts that give any codebase AI-readable memory:

| Artifact | What It Does | Size |
|---|---|---|
| **AGENTS.md** | Complete system map: architecture, signal chains, failure modes, gotchas | 300+ lines |
| **Slash Commands** | Executable domain expertise (debug workflows, trace signals) | 2,333 lines |
| **Domain Skill** | Turns Bob into instant expert on your specific codebase | 545 lines |

**Result:** Any developer or AI session has full context in 60 seconds instead of 2 weeks.

---

## Proof It Works

Validated on **4 completely different codebases** (160K+ LOC total):

**Robotics** - ArduPilot + Gazebo humanoid simulation (30 files, C++/Python)  
**Web** - Next.js e-commerce platform (50K LOC, React/Node)  
**Data** - Apache Airflow ETL pipeline (30K LOC, Python/SQL)  
**Microservices** - Kubernetes distributed system (80K LOC, Node.js)

| Metric | Before | After | Improvement |
|---|---|---|---|
| Developer onboarding | 2 weeks | 60 seconds | **99.5%** |
| AI context setup | 30 minutes | 0 minutes | **100%** |
| AI answer accuracy | 68% | 94% | **38%** |
| Knowledge retention | 0% (leaves with employees) | 100% (permanent) | **∞** |

---

## Live Demos

**[Comparison Demo](https://neetagrg.github.io/codebase-brain/comparison.html)** - Same question, with/without Codebase Brain  
**[watsonx.ai Query Interface](https://neetagrg.github.io/codebase-brain/watsonx-query.html)** - Real AI answers powered by IBM watsonx.ai  
**[Pricing](https://neetagrg.github.io/codebase-brain/pricing.html)** - Enterprise SaaS model

---

## Quick Start

```bash
# Install
pip install codebase-brain

# Generate artifacts for any repo
codebase-brain init /path/to/your/repo

# Validate quality
codebase-brain validate

# Query from CLI
codebase-brain query "Why does X fail when Y?"
```

---

## Who This Helps

** Engineering Leaders** - Cut onboarding 95%, retain knowledge permanently, measure ROI  
** Developers** - AI assistants understand your code, find bugs in minutes not hours  
** New Team Members** - Productive day 1 instead of week 2, learn without bothering seniors

---

## Technology

**Built with IBM Bob** across 16 sessions  
**Powered by IBM watsonx.ai** for production query interface  
**Production-ready:** CLI tool, validation framework, CI/CD integration, metrics dashboard

---

## Documentation

 [Architecture Deep-Dive](docs/ARCHITECTURE.md) - How it works technically  
 [Case Study](docs/CASE_STUDY.md) - Real metrics from ArduHumanoid robotics project  
 [Deployment Guide](DEPLOYMENT.md) - Production deployment on IBM Cloud  
 [watsonx.ai Integration](docs/WATSONX_INTEGRATION.md) - API architecture and implementation

---

## Repository Structure

```
codebase-brain/
├── bob-copilot/           # Generated artifacts (3,178 lines)
│   ├── AGENTS.md          # Knowledge base
│   ├── commands/          # 4 slash commands
│   └── skills/            # Domain expert skill
├── examples/              # 3 validation examples (816 lines)
├── tools/                 # CLI, validation, metrics
├── docs/                  # Architecture, case study, deployment
├── bob-sessions/          # All 16 Bob sessions exported
└── tests/                 # Automated tests
```

**Total Generated:** 4,741 lines of expert content  
**Coverage:** 160K+ LOC across 4 domains  
**Sessions:** 16 Bob sessions with full iteration history

---

## FAQ

**Does this work for my language/framework?**  
Yes. Tested on Python, JavaScript, C++, TypeScript, SQL. Language-agnostic approach.

**How long does generation take?**  
~45 minutes for initial generation. Updates take 2-5 minutes.

**What if my code changes?**  
Validation tool detects drift and regenerates only changed sections.

---

**Built for IBM Bob Dev Day Hackathon 2026**

[GitHub Repository](https://github.com/Neetagrg/codebase-brain) • [Live Demo Site](https://neetagrg.github.io/codebase-brain/)

**License:** MIT • **Powered by:** IBM Bob & IBM watsonx.ai
