# Backend QOLQA

A FastAPI-based backend service that provides solutions management functionality. This project is built with modern Python practices and supports MongoDB database.

## Features

- FastAPI-based REST API
- Support for MongoDB database
- CORS middleware enabled
- Environment-based configuration
- Structured project layout with clear separation of concerns

## Project Structure

```
backend-qolqa/
├── config/         # Configuration files and settings
├── interfaces/     # Interface definitions
├── models/         # Database models
├── schemas/        # Pydantic schemas
├── solution/       # Solution-related endpoints and logic
├── utils/          # Utility functions
├── main.py         # Application entry point
└── requirements.txt # Project dependencies
```

## Prerequisites

- Python 3.8+
- MongoDB (if using MongoDB as database)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd backend-qolqa
```

2. Create and activate a virtual environment:
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following variables:
```
TYPE_DB=sql  # or mongodb
DATABASE_URL=your_database_url
```

## Running the Application

Start the server with:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Swagger UI documentation at `http://localhost:8000/docs`
- ReDoc documentation at `http://localhost:8000/redoc`

## Dependencies

- FastAPI (0.110.3)
- Uvicorn (0.23.2)
- Motor (3.6.0) - MongoDB driver
- Pydantic Settings (2.6.1)
- Python-dotenv (1.0.0)
- Asyncio (3.4.3)
- Asyncpg (0.30.0)
- SQLAlchemy (2.0.36)

## Development

The project follows a modular structure with clear separation of concerns:
- `config/`: Contains configuration settings and database connections
- `interfaces/`: Defines interfaces and abstract classes
- `models/`: Contains database models
- `schemas/`: Pydantic models for request/response validation
- `solution/`: Business logic and API endpoints for solutions
- `utils/`: Helper functions and utilities

## License

[Add your license information here]
