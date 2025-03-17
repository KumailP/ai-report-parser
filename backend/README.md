# Financial Report Structuring Backend

This directory contains the FastAPI backend service for the Financial Report Structuring microservice.

## Architecture

The backend is structured as follows:

```
backend/
├── app/                      # Application code
│   ├── __init__.py
│   ├── main.py               # FastAPI application entry point
│   ├── routes.py             # API endpoints
│   ├── models.py             # Data models (SQLModel & Pydantic)
│   ├── database.py           # Database connection and session
│   ├── logging.py            # Logging configuration
│   └── services/             # Service modules
│       ├── excel_service.py  # Excel file processing
│       └── openai_service.py # OpenAI integration
├── example_files/            # Sample financial reports
├── sqlite/                   # SQLite database files
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container definition
├── .env                      # Environment variables
└── .dockerignore             # Docker ignore file
```

## Key Components

### Data Models

The application uses SQLModel to define both ORM models and API schemas:

- **Report**: Represents a processed financial report with metadata
- **ReportPosition**: Represents a specific financial position with current/previous values
- **STANDARD_POSITIONS**: Dictionary defining standardized financial position codes and descriptions

### API Endpoints

- **POST /api/report**: Uploads and processes a financial report
- **GET /api/report**: Retrieves processed reports with optional filtering

### Services

#### Excel Service

The `excel_service.py` module handles:
- File validation
- Excel parsing using openpyxl
- Data extraction from spreadsheets

#### OpenAI Service

The `openai_service.py` module provides:
- Integration with OpenAI's API
- Prompt engineering for financial data extraction
- Mapping between extracted data and standardized positions
- Error handling and retry logic

## Database Schema

The application uses SQLite with SQLModel ORM:

- **reports**: Stores metadata about processed reports
  - id (PK)
  - processed_at (timestamp)
  - file_name (string)

- **report_positions**: Stores standardized financial positions
  - id (PK)
  - report_id (FK to reports)
  - code (string)
  - current (float, nullable)
  - previous (float, nullable)

## Environment Variables

Configure the application using the following environment variables in `.env`:

```
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=sqlite:///sqlite/db.sqlite
```

## Development Setup

### Local Development

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate     # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env  # Then edit with your API key
   ```

4. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker Development

Run with hot-reloading for development:

```bash
docker-compose up
```

## API Documentation

When running, access the Swagger UI at:
- http://localhost:8000/docs
- http://localhost:8000/redoc (ReDoc alternative UI)

## Implementation Details

### OpenAI Integration

The service uses GPT-4o to:

1. Parse Excel data converted to rows
2. Extract financial positions and their values
3. Map extracted positions to standardized codes
4. Return a structured JSON response

The prompt engineering includes detailed instructions to guide the model in:
- Identifying financial terms regardless of labeling
- Extracting current and previous year values
- Handling hierarchical data structures
- Standardizing output format

The service implements robust error handling with exponential backoff retry logic for API failures.

### Data Flow

1. Client uploads Excel file to `/api/report`
2. `excel_service.py` validates and extracts raw data
3. `openai_service.py` processes data with GPT to extract standardized positions
4. Data is stored in the database
5. Processed report is returned to the client

## Performance Considerations

- The service implements proper exception handling and logging
- Database queries use indexes on frequently queried fields
- The OpenAI client uses retry logic with exponential backoff
- Excel processing extracts only necessary data 