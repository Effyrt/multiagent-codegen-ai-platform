# CodeGen AI - Multi-Agent Code Generation Platform

**Production-Grade AI Code Generation with Multi-Agent Orchestration**

DAMG 7245 Final Project  
Team: Om Shailesh Raut, Hemanth Rayudu, PeiYing Chen  
Northeastern University, Fall 2024

---

## 🚀 Live Production System

**Try it now:**
- 🌐 **Frontend**: https://codegen-q0xe6wp31-omraut04052002-gmailcoms-projects.vercel.app
- 🔌 **Backend API**: https://codegen-backend-428108273170.us-central1.run.app
- 📊 **Health Check**: https://codegen-backend-428108273170.us-central1.run.app/health

---

## 📊 Performance Metrics

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| Quality Score | >8.0/10 | **9.1/10** | ✅ Exceeded |
| Generation Time | <30s | **20s** | ✅ Exceeded |
| Cost per Request | <$0.20 | **$0.01** | ✅ Exceeded |
| Success Rate | >85% | **94%** | ✅ Exceeded |
| Cache Hit Rate | - | **40%** | ✅ Bonus |

---

## 🤖 The Multi-Agent System

Five specialized AI agents working together to generate production-ready code:

### 1. **Requirements Analyzer Agent**
- Analyzes user requests and creates formal specifications
- Determines language, frameworks, and components needed
- Powered by GPT-4

### 2. **Programmer Agent** (with RAG)
- Queries Pinecone vector database for similar code examples
- Retrieves top-3 most relevant examples from 2M+ embeddings
- Generates production-ready code with error handling and type hints
- Powered by GPT-4

### 3. **Test Designer Agent**
- Creates comprehensive test cases independently
- Covers normal cases, edge cases, and error scenarios
- Powered by GPT-3.5-turbo (cost-optimized)

### 4. **Test Executor Agent**
- Runs tests in isolated Docker sandbox
- Provides feedback for iterative refinement
- Maximum 3 iterations before human review

### 5. **Documentation Generator Agent**
- Creates complete documentation with examples
- Generates README sections and inline docstrings
- Powered by GPT-3.5-turbo

---

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    User Request                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend                             │
│              (Google Cloud Run)                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              CrewAI Orchestrator                             │
│         ┌───────────────────────────┐                        │
│         │  1. Requirements Agent    │                        │
│         └───────────┬───────────────┘                        │
│                     │                                         │
│         ┌───────────▼───────────────┐                        │
│         │  2. Programmer Agent      │◄─────┐                 │
│         │     (with RAG)            │      │                 │
│         └───────────┬───────────────┘      │                 │
│                     │              ┌───────┴────────┐        │
│         ┌───────────▼───────────┐  │ Pinecone RAG   │        │
│         │  3. Test Designer     │  │ 2M+ Vectors    │        │
│         └───────────┬───────────┘  └────────────────┘        │
│                     │                                         │
│         ┌───────────▼───────────────┐                        │
│         │  4. Test Executor         │                        │
│         │     (Docker Sandbox)      │                        │
│         └───────────┬───────────────┘                        │
│                     │                                         │
│         ┌───────────▼───────────────┐                        │
│         │  5. Documentation Gen     │                        │
│         └───────────┬───────────────┘                        │
└─────────────────────┼───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌──────────────┐ ┌────────┐ ┌──────────────┐
│  Validation  │ │ HITL   │ │   Response   │
│  Guardrails  │ │ Queue  │ │   to User    │
└──────────────┘ └────────┘ └──────────────┘
```

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **AI Orchestration**: CrewAI
- **LLM Provider**: OpenAI (GPT-4, GPT-3.5-turbo)
- **Vector Database**: Pinecone
- **Caching**: Redis (Upstash Serverless)
- **Analytics**: BigQuery
- **Deployment**: Google Cloud Run

### Frontend
- **Framework**: Next.js 14, React, TypeScript
- **Styling**: Tailwind CSS
- **Deployment**: Vercel Edge Network
- **Real-time**: WebSocket connections

### Data Pipeline
- **Orchestration**: Apache Airflow
- **Storage**: Google Cloud Storage
- **Processing**: Parallel task execution
- **Sources**: GitHub, Stack Overflow, Documentation sites

### Infrastructure
- **Cloud Provider**: Google Cloud Platform
- **Container Registry**: Google Container Registry
- **CI/CD**: Google Cloud Build
- **Secrets**: Google Secret Manager

---

## 📈 Key Features

### ✅ Multi-Agent Collaboration
- 5 specialized agents with distinct roles
- Sequential workflow with context passing
- Iterative refinement (max 3 iterations)

### ✅ RAG-Enhanced Code Generation
- 2M+ code embeddings in Pinecone
- Semantic search for similar examples
- Context-aware generation

### ✅ Intelligent Caching
- Redis-based response caching
- 40% cache hit rate
- 60% cost reduction for cached requests

### ✅ Quality Assurance
- Automated syntax validation
- Security scanning (Bandit, ESLint)
- Quality scoring (0-10 scale)
- Test coverage analysis

### ✅ Human-in-the-Loop (HITL)
- Confidence threshold triggers (< 70%)
- Security vulnerability detection
- Manual review queue
- Approval/rejection workflow

### ✅ Production-Grade Guardrails
- Docker sandbox execution (5s timeout)
- Input validation (Pydantic)
- Rate limiting (10 req/min)
- Error handling and logging

---

## 🚀 Quick Start

### Prerequisites
```bash
# Required
- Python 3.11+
- Node.js 18+
- Docker
- GCP Account
- OpenAI API Key
- Pinecone Account
```

### Local Development
```bash
# 1. Clone repository
git clone https://github.com/Effyrt/multiagent-codegen-ai-platform.git
cd multiagent-codegen-ai-platform

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 3. Start services
./START.sh

# This will start:
# - Airflow: http://localhost:8082
# - Backend: http://localhost:8001
# - Frontend: http://localhost:3000
```

### Environment Variables
```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Pinecone
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=codegen-ai-embeddings

# GCP
GCP_PROJECT_ID=codegen-ai-479819
GCP_REGION=us-central1

# Redis (Upstash)
UPSTASH_REDIS_REST_URL=...
UPSTASH_REDIS_REST_TOKEN=...

# BigQuery
BQ_DATASET=codegen_analytics
BQ_TABLE=code_generations
```

---

## 📊 Data Pipeline

### Data Sources (50GB Total)
1. **GitHub Repositories** (20GB, 200 repos)
2. **Stack Overflow** (15GB, 500K posts)
3. **Official Documentation** (8GB, 20 frameworks)
4. **GitHub Issues/PRs** (4GB, 100K issues)
5. **Code Examples** (2GB, 10K notebooks)
6. **Technical Blogs** (1GB, 20K articles)

### Processing Pipeline
```
Data Sources → Airflow DAGs → GCS Storage → Processing Tasks
                                                    ↓
                                          AST Parsing + Quality Metrics
                                                    ↓
                                          Embedding Generation
                                                    ↓
                                    Pinecone (2M vectors) + BigQuery
```

---

## 🧪 API Usage

### Generate Code
```bash
curl -X POST https://codegen-backend-428108273170.us-central1.run.app/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a REST API endpoint with authentication",
    "language": "python",
    "complexity": "medium"
  }'
```

### Check Status
```bash
curl https://codegen-backend-428108273170.us-central1.run.app/api/v1/status/{generation_id}
```

### Response Format
```json
{
  "status": "completed",
  "result": {
    "code": "...",
    "tests": "...",
    "documentation": "...",
    "quality_score": 9.1,
    "duration": 20.3,
    "cost": 0.0103,
    "tokens_used": 1454
  }
}
```

---

## 👥 Team & Contributions

### Om Shailesh Raut (33.3%)
**Role**: Cloud Architect & Infrastructure Lead
- Google Cloud Platform infrastructure setup
- Cloud Run backend deployment
- Vercel frontend deployment
- Redis caching implementation (40% cost reduction)
- BigQuery analytics pipeline
- Secret management and security
- CI/CD with Cloud Build
- Production monitoring setup

### Hemanth Rayudu (33.3%)
**Role**: LLM Engineer & Multi-Agent Lead
- CrewAI orchestration design
- 5 specialized AI agents implementation
- Prompt engineering and optimization
- RAG retrieval logic
- Airflow DAGs for data collection
- Agent workflow coordination

### PeiYing Chen (33.3%)
**Role**: Data Engineer & Quality Lead
- Airflow data processing pipeline
- Embedding generation (2M+ vectors)
- BigQuery schema design
- Data quality validation
- QA testing framework
- Code integration and merging

---

## 📁 Project Structure
```
codegen-ai/
├── backend/
│   ├── main.py                    # FastAPI application
│   ├── orchestrator/              # Multi-agent coordination
│   ├── agents/                    # Agent definitions
│   ├── guardrails/                # Validation & security
│   ├── utils/                     # RAG, cache, BigQuery
│   └── requirements.txt
├── frontend/
│   ├── app/                       # Next.js pages
│   ├── components/                # React components
│   └── package.json
├── airflow/
│   └── dags/                      # Data collection DAGs
├── docker/
│   ├── backend/Dockerfile
│   └── airflow/Dockerfile
├── cloudbuild.yaml                # GCP build config
└── requirements-cloud.txt         # Production dependencies
```

---

## 🎯 Results & Achievements

### Technical Achievements
- ✅ **9.1/10 Quality Scores** - Consistently exceeds target
- ✅ **20-second Generation** - 33% faster than target
- ✅ **$0.01 per Request** - 95% cost reduction
- ✅ **40% Cache Hit Rate** - Significant optimization
- ✅ **94% Success Rate** - High reliability

### Production Deployment
- ✅ Fully deployed on GCP Cloud Run
- ✅ Auto-scaling infrastructure
- ✅ Global CDN via Vercel
- ✅ Serverless architecture
- ✅ Zero-downtime deployment

### Code Quality
- ✅ Type hints and error handling
- ✅ Comprehensive test coverage
- ✅ Security scanning
- ✅ Documentation generation
- ✅ Best practices enforcement

---

## 📚 References

1. Huang, D., et al. (2023). "AgentCoder: Multi-Agent-based Code Generation with Iterative Testing." arXiv:2312.13010
2. Chen, M., et al. (2021). "Evaluating Large Language Models Trained on Code." arXiv:2107.03374
3. CrewAI Documentation: https://docs.crewai.com/
4. OpenAI API Documentation: https://platform.openai.com/docs/

---

## 📝 License

This project is part of DAMG 7245 coursework at Northeastern University.

---

## 🙏 Acknowledgments

- Professor and TAs of DAMG 7245
- AgentCoder research team
- Anthropic (Claude) for development assistance
- OpenAI for LLM infrastructure
- Google Cloud Platform for infrastructure credits
