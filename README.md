# Codebase Brain 🧠

![Tests](https://img.shields.io/badge/tests-passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Bob Sessions](https://img.shields.io/badge/Bob%20Sessions-8-blue)
![Lines Generated](https://img.shields.io/badge/Lines%20Generated-3%2C623-green)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-orange)](https://neetagrg.github.io/codebase-brain/comparison.html)

## 🎥 See It In Action

[Animated demo showing comparison.html in action]

👉 [**Live Demo**](https://neetagrg.github.io/codebase-brain/comparison.html)

> Stop explaining your codebase from scratch every single AI session.

## The Problem

Every developer knows this pain. You spend 30 messages 
explaining your codebase to an AI, get a partial answer, 
then start a new session and explain everything again. 
Forever. On a simple project this is annoying. On a 
complex multi-system codebase — it costs weeks.

## The Solution

Codebase Brain uses IBM Bob to generate three permanent 
artifacts that give any complex codebase instant memory:

| Artifact | What It Does | Size |
|---|---|---|
| AGENTS.md | Complete technical brain — architecture, failures, gotchas | 300+ lines |
| Slash Commands | Domain expert commands any developer can invoke | 2,333 lines |
| Domain Skill | Makes Bob a senior engineer on your codebase instantly | 545 lines |

## Results

| Before | After |
|---|---|
| 30 messages to establish context | 1 command |
| Start from zero every session | Permanent memory |
| Only you understand the codebase | Any developer contributes instantly |
| Weeks to onboard a new developer | 60 seconds |

## How It Works

**Step 1** — Point IBM Bob at your repository

**Step 2** — Bob reads every file and generates AGENTS.md 
with complete architecture, signal chains, failure modes, 
and gotchas

**Step 3** — Bob creates slash commands encoding deep 
domain expertise for your specific codebase

**Step 4** — Bob generates a domain expert skill that 
makes any future Bob session an instant expert

**Step 5** — Any developer or future Bob session has 
full context in 60 seconds

## Demo

Built on a real-world humanoid robotics codebase 
(ArduPilot SITL + Gazebo Harmonic). Bob generated:

- Complete signal chain: MAVLink → ArduPilot → 
  Plugin → Gazebo joints
- 10 critical gotchas identified
- 10 failure modes with root causes and fixes
- All 30+ files documented with breaking change warnings

## Bob Sessions

All IBM Bob sessions are exported and available in 
`bob-sessions/` — showing exactly how Bob was used 
to build every artifact in this project.

## Project Structure

```
codebase-brain/
├── bob-copilot/
│   ├── AGENTS.md              # Bob-generated codebase brain
│   ├── commands/              # 4 domain slash commands
│   │   ├── debug-joint.md
│   │   ├── lua-trace.md
│   │   ├── sdf-check.md
│   │   └── gait-plan.md
│   └── skills/
│       └── arduhumanoid-expert.md  # Domain expert skill
├── bob-sessions/              # Exported Bob session reports
└── docs/
    ├── problem-statement.md
    └── bob-usage-statement.md
```

## Built For

IBM Bob Dev Day Hackathon 2026
Powered by IBM Bob
