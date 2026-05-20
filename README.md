<div align="center">

![Qolqa Logo](https://raw.githubusercontent.com/QOLQA/frontend-qolqa/main/docs/images/logo.png)

# QOLQA Backend

**REST API for document-oriented schema design and metrics calculation**

[![Frontend](https://img.shields.io/badge/frontend-repo-blue?style=for-the-badge)](https://github.com/QOLQA/frontend-qolqa)
[![Backend](https://img.shields.io/badge/backend-repo-blue?style=for-the-badge)](https://github.com/QOLQA/backend-qolqa)
[![Live Demo](https://img.shields.io/badge/demo-live-success?style=for-the-badge)](https://qolqadb.vercel.app/)

[Features](#-features) • [Architecture](#-architecture) • [Getting Started](#-getting-started) • [API Docs](#-api-documentation) • [Tech Stack](#-tech-stack)

</div>

---

## 📖 About

The **Qolqa Backend** is a high-performance REST API built with **FastAPI** that powers the Qolqa schema design tool. It provides:

✅ **Schema persistence** using MongoDB's native document model  
✅ **JWT-based authentication** for secure user sessions  
✅ **Versioning management** for multi-schema comparisons  
✅ **Query validation** for metrics calculation  
✅ **Rate limiting** for resource protection

---

## 🎯 Features

### 1. **Authentication & Authorization**

- JWT-based stateless authentication
- Secure password hashing with `bcrypt`
- Token expiration and refresh handling

### 2. **Solution Management**

- Create and manage schema design solutions
- Support for collections, attributes, and relationships
- Nested attribute structures with validation

### 3. **Versioning System**

- Create alternative schema versions
- Branch from existing designs
- Track version history and relationships

### 4. **Query Management**

- Define and validate queries for metric calculation
- Associate queries with specific schema versions
- Support for complex query patterns

---

## 🏗️ Architecture

The backend follows **Clean Architecture** principles with strict layer separation:

```
api/                  → FastAPI controllers (DTOs, request/response handling)
├── controllers/      → Route handlers (auth, solution, version, query)
└── handle_errors.py  → Centralized error handling

application/          → Use cases and orchestration
├── use_cases/        → Business logic orchestration
├── dtos/             → Data Transfer Objects (Pydantic models)
└── repositories/     → Repository interfaces (contracts)

domain/               → Pure business logic (framework-agnostic)
├── entities/         → Domain models (Solution, Version, Query, User)
└── repositories/     → Repository contracts (abstract interfaces)

infrastructure/       → External concerns (database, auth, logging)
├── repositories/     → MongoDB repository implementations
├── documents/        → MongoDB document models
├── mappers/          → Entity ↔ Document conversion
└── audit/            → Logging and monitoring

config/               → Settings, environment, database connection
tests/                → Unit and integration tests
```

**Key architectural decisions:**

- **Strict layer isolation**: Domain layer has ZERO dependencies on infrastructure
- **Dependency Inversion**: Application depends on abstractions (repository interfaces), not concrete implementations
- **DTOs at boundaries**: Pydantic models validate data at API layer, pure entities in domain
- **Clean separation**: Business logic (domain) vs. technical concerns (infrastructure)

---

## 🚀 Getting Started

### Prerequisites

- **Python** 3.8+
- **MongoDB** running locally or remotely
- **Git**

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/QOLQA/backend-qolqa.git
cd backend-qolqa
```

2. **Create and activate a virtual environment**

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

Copy the example file and configure:

```bash
cp .env.example .env
```

**Minimal `.env` configuration:**

```bash
# Database
DATABASE_URL=mongodb://localhost:27017/qolqa_db
TYPE_DB=mongo

# JWT (CHANGE THIS IN PRODUCTION!)
SECRET_KEY=dev-secret-key-CHANGE-THIS-IN-PRODUCTION-min-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=300

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

5. **Run the server**

```bash
uvicorn main:app --reload
```

The API will be available at **http://localhost:8000**

---

## 📚 API Documentation

Once the server is running, interactive API documentation is available:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Main Endpoints

| Endpoint              | Method | Description                      |
| --------------------- | ------ | -------------------------------- |
| `/auth/register`      | POST   | Register a new user              |
| `/auth/login`         | POST   | Login and get JWT token          |
| `/solutions`          | GET    | List all solutions for user      |
| `/solutions`          | POST   | Create a new schema solution     |
| `/solutions/{id}`     | GET    | Get solution details             |
| `/solutions/{id}`     | PUT    | Update solution                  |
| `/solutions/{id}`     | DELETE | Delete solution                  |
| `/versions`           | POST   | Create a new version             |
| `/versions/{id}`      | GET    | Get version details              |
| `/queries`            | POST   | Create a query for metrics       |
| `/queries/{id}`       | DELETE | Delete a query                   |

---

## 🛠️ Tech Stack

| Technology             | Purpose                            |
| ---------------------- | ---------------------------------- |
| **FastAPI**            | Modern Python web framework        |
| **Uvicorn**            | ASGI server for FastAPI            |
| **MongoDB (Motor)**    | Document-oriented database         |
| **Pydantic**           | Data validation and DTOs           |
| **PyJWT**              | JSON Web Token authentication      |
| **bcrypt**             | Secure password hashing            |
| **SlowAPI**            | Rate limiting middleware           |
| **pytest**             | Testing framework                  |

---

## 🧪 Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=. --cov-report=term-missing
```

---

## 🐳 Docker Support

Build and run with Docker:

```bash
docker build -t qolqa-backend .
docker run -p 8000:8000 --env-file .env qolqa-backend
```

---

## 📁 Project Structure

```
backend-qolqa/
├── api/                    # API layer (FastAPI controllers)
│   ├── controllers/        # Route handlers
│   └── handle_errors.py    # Error handling
├── application/            # Application layer (use cases)
│   ├── use_cases/          # Business logic orchestration
│   ├── dtos/               # Data Transfer Objects
│   └── repositories/       # Repository interfaces
├── domain/                 # Domain layer (pure business logic)
│   ├── entities/           # Domain models
│   └── repositories/       # Repository contracts
├── infrastructure/         # Infrastructure layer (MongoDB, auth)
│   ├── repositories/       # Repository implementations
│   ├── documents/          # MongoDB document models
│   ├── mappers/            # Entity ↔ Document mappers
│   └── audit/              # Logging and monitoring
├── config/                 # Settings and configuration
├── tests/                  # Test suite
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
└── Dockerfile              # Docker configuration
```

---

## 🔗 Links

- **Live Demo**: [https://qolqadb.vercel.app/](https://qolqadb.vercel.app/)
- **Frontend Repository**: [https://github.com/QOLQA/frontend-qolqa](https://github.com/QOLQA/frontend-qolqa)
- **Backend Repository**: [https://github.com/QOLQA/backend-qolqa](https://github.com/QOLQA/backend-qolqa)
- **Video Demo**: [https://youtu.be/gD1SmnvSrcI](https://youtu.be/gD1SmnvSrcI)

---

## 🎓 Academic Context

This backend is part of research on **NoSQL database schema design**, providing the infrastructure for metrics-driven design evaluation. The API supports the calculation of four key metrics:

- **Access Pattern (AP)** → Query efficiency
- **Recovery Cost (RC)** → Data reconstruction overhead
- **Redundancy (R)** → Data duplication
- **Completeness (C)** → Query coverage

> **Vera-Olivera, H. & Holanda, M. (2024)**. _Métricas para análise de esquemas em banco de dados NoSQL orientado a documentos_. In Anais do XXXIX Simpósio Brasileiro de Bancos de Dados, pages 381–393, Porto Alegre, RS, Brasil. SBC.

---

## 📄 License

This project is open-source and available for academic and professional use.

---

<div align="center">

**Built with ❤️ for better NoSQL database design**

[⬆ Back to top](#qolqa-backend)

</div>
