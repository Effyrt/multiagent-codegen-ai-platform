# CodeGen AI

**Multi-Agent Code Generation Platform**

DAMG 7245 Final Project  
Team: Om Raut, Hemanth Rayudu, PeiYing Chen  
Northeastern University

## What we're building

A code generation system that uses multiple AI agents working together. Think GitHub Copilot but with specialized agents for different tasks.

### The agents
- Requirements Agent - figures out what you want
- Programmer Agent - writes the actual code (uses RAG to find similar examples)
- Test Designer - creates test cases
- Test Executor - runs the tests, gives feedback
- Documentation Agent - writes docs

### Tech we're using
- Backend: FastAPI, Python
- Frontend: Next.js, React
- Cloud: GCP (mainly because free credits)
- AI: OpenAI GPT-4 + GPT-3.5
- Data: We're collecting 50GB of code from GitHub, Stack Overflow, etc.
- Vector DB: Pinecone (for the RAG part)

### Architecture
```
User → API → Agent Orchestrator → 5 Agents → Return Code
                ↓
         Pinecone (2M+ code examples)
```

## Current Status

- [x] Project structure
- [x] Got all the accounts set up (GCP, OpenAI, Pinecone)
- [ ] Infrastructure deployment
- [ ] Agent implementation
- [ ] Data collection pipeline
- [ ] Frontend
- [ ] Testing
- [ ] Final presentation

## Setup

Check `docs/setup.md` for detailed instructions. Basically:
1. Get API keys (OpenAI, Pinecone, GCP)
2. Install dependencies
3. Deploy with Terraform
4. Run it

## Team Breakdown

**Om** - Infrastructure, deployment, frontend, monitoring  
**Hemanth** - AI agents, LLM stuff, data collection  
**PeiYing** - Data pipeline, databases, testing, QA

Equal contributions: 33.3% each

## Notes

Based on the AgentCoder paper/repo - we're taking their multi-agent approach and making it production-ready with real infrastructure, data pipeline, and a proper UI.

---

Built for DAMG 7245 - Big Data & Intelligent Analytics  
Northeastern University, Fall 2024
