# 📘 InsightFlow: AI 기반 데이터 분석 플랫폼 & DevOps 마스터 가이드

## 1. 프로젝트 개요 (Overview)
>
> - 프로젝트명: InsightFlow
> - 핵심 컨셉: "Natural Language to Workflow"사용자가 자연어로 데이터 분석을 요청하면, AI가 의도를 파악하고 Airflow DAG(워크플로우)를 동적으로 생성/실행하여 결과를 도출하는 지능형 플랫폼.
> - 학습 목표: 단순한 기능 구현을 넘어, MSA, 이벤트 기반 아키텍처, RAG, 그리고 Kubernetes 기반의 DevOps 파이프라인을 바닥부터 직접 구축하며 시니어 레벨의 엔지니어링 역량을 확보함.

## 2. 전체 아키텍처 & 기술 스택 (Tech Stack)

> - 이 프로젝트는 이원화된 데이터 저장소와 비동기 이벤트 처리, 그리고 클라우드 네이티브 배포를 지향합니다.

### 🛠 Backend & Data Engineering

| 영역 | 기술 스택 | 선정 이유 |
| :--- | :--- | :--- |
| **Core** | Python 3.10+, FastAPI | 비동기 처리에 최적화된 고성능 API 서버 |
| **Messaging** | RabbitMQ | 서비스 간 결합도를 낮추고 트래픽 폭주를 막는 버퍼 역할 |
| **API Protocol** | gRPC (Upload), REST (Client) | 대용량 파일 전송 속도 최적화(gRPC) 및 범용성(REST) |
| **Orchestration** | Apache Airflow | 복잡한 분석 순서 제어 및 동적 DAG 실행 |
| **Object Storage** | MinIO (S3 Compatible) | 원본 데이터(CSV/Parquet) 및 결과 이미지 저장 |

### 🗄 Database & Persistence (Polyglot)

| 데이터 종류 | 저장소 기술 | 용도 |
| :--- | :--- | :--- |
| **RDBMS** | MariaDB | 사용자 정보, 프로젝트 관리 (정형 데이터) |
| **NoSQL** | MongoDB | 분석 로그, 비정형 메타데이터, 동적 결과물 |
| **Cache/Auth** | Redis | JWT 토큰 관리(Blacklist), API Rate Limiting |
| **Vector DB** | ChromaDB | RAG 구현을 위한 임베딩 데이터 저장 (유사도 검색) |

### 🧠 AI & LLM (RAG Pipeline)

- LLM: Gemini / Ollama (추론 및 코드 생성)
- Embedding: HuggingFace Transformers (Sentence-BERT)
- Framework: LangChain or LlamaIndex (RAG 파이프라인 구성)

### 💻 Frontend

- React + Vite: 빠르고 가벼운 SPA 프레임워크
- Tailwind CSS + shadcn/ui: 모던하고 컴팩트한 UI 디자인 시스템

### 🚀 DevOps & Infrastructure

| 영역 | 개발 환경 (Windows/WSL2) | 배포 환경 (Ubuntu Server) |
| :--- | :--- | :--- |
| **Container** | Docker, Docker Compose | Kubernetes (K3s) |
| **Package** | docker-compose.yml | Helm Charts |
| **Gateway** | Nginx (Local Proxy) | Traefik (Ingress Controller) |
| **Monitoring** | - | Prometheus (수집), Grafana (시각화) |
| **CI/CD** | - | GitHub Actions |
