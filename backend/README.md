# Financial Report Structuring Backend

## Table of Contents
- [Architecture](#architecture)
- [Key Components](#key-components)
  - [Data Models](#data-models)
  - [API Endpoints](#api-endpoints)
  - [Services](#services)
- [Database Schema](#database-schema)
- [Environment Variables](#environment-variables)
- [Development Setup](#development-setup)
  - [Local Development](#local-development)
  - [Docker Development](#docker-development)
- [API Documentation](#api-documentation)
- [Implementation Details](#implementation-details)
  - [OpenAI Integration](#openai-integration)
  - [Data Flow](#data-flow)
- [Implementation Considerations](#implementation-considerations)
- [Assumptions](#assumptions)
- [Limitations / Improvements](#limitations--improvements)
- [AI Usage](#ai-usage)

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
│   ├── logger.py             # Logging configuration
│   ├── constants.py          # Constants
│   └── services/             # Service modules
│       ├── excel_service.py  # Excel file processing
│       └── openai_service.py # OpenAI integration
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
- **PositionType**: Represents standardized financial position types with codes and categories
- **ReportPosition**: Represents a specific financial position with current/previous values

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

- **position_types**: Stores standardized financial position definitions
  - id (PK)
  - code (string, indexed, unique)
  - description (string)
  - category (enum: asset, liability, equity)

- **reports**: Stores metadata about processed reports
  - id (PK)
  - processed_at (timestamp, indexed)
  - file_name (string, indexed)

- **report_positions**: Stores financial position values for reports
  - id (PK)
  - position_type_id (FK to position_types, indexed)
  - report_id (FK to reports, indexed)
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

## Implementation Considerations

#### 1. General
- The service implements exception handling and logging
#### 2. Data extraction / transformation / validation
- Transformations are kept to a minimum as we need to pass empty spaces / rows to the model as well to ensure it understands where the data falls within a spreadsheet
- openpyxl is used in favor of pandas as we only need basic excel loading / parsing
#### 3. LLM usage
- Initially I tried using a two-pass approach:
   1. The first prompt identifies the positions
   2. The second prompt structures the data
- This was changed to use a single pass approach because of the following:
   - Results were comparable, although the two pass approach may be better for accuracy depending on the dataset
   - Reduced token usage / billing / quota limits
   - Reduced latency
- The prompt can be summarized, right now it's quite detailed which may increase the input tokens
- The standard positions are injected in the prompt
- The LLM is forbidden from creating custom financial positions
- The LLM returns 'excluded_positions', this is useful to check the accuracy and understand the model's thinking process i.e. why it rejected certain positions. They are not currently persisted in the DB.
- We may consider using a network request instead of using the OpenAI SDK, this would be helpful if we want to extend support for multiple LLM models
- We may consider using the completions.parse API instead of compeltions.create API, although our curent implementation returns a structured JSON. I need to look further at the OpenAI API documentation to better understand the differences.
#### 4. Database Modelling
- We have DB level validation to ensure the data structure is correct
- Database queries use indexes on frequently queried fields
- The OpenAI client uses retry logic with exponential backoff - If our application was in a production system with users, we would implement application-level rate limiting so we don't go bankrupt
- Initially the standardized positions were a constant. For demo purposes, this is good enough because:
   1. We don't need to query the DB for constants, hence it is performant
   2. We have an assumption that the standard positions will not change frequently
- The above was since changed and now we have normalized the standard positions `position_types`. This means:
   1. We need to query the DB to construct the prompt and verify the data
   2. We get rid of raw strings in our report_positions table and instead have a reference to position_types
   3. We can extend position types with more information (description, category, etc.)
   4. We can add more positions without having to modify the code (Although we will need a migration script)
   5. 'category' could be normalized as well, however having it defined as an Enum should be fine for now

## Assumptions

1. "Current" is whatever the latest year in the spreadsheet, with the "Previous" year being the one that comes before. This is a big assumption only made for test purposes, in reality we would label the year (or period) for which the financial data is related to.
2. Balance sheet positions are "standard" and fall within our predefined categories and position names. The model will be flexible enough to identify which labels fall into our given standard, but it will disregard labels that it determines to be 'far off' from our given specification. This can be changed without modifying code by adding more standard positions in the database, but I have made this assumption so we have some structure for querying report data, as well as ensure a better response from LLM as balance sheet positions are fairly standard.
3. If a balance sheet position in the spreadsheet has multiple values that fall into one of our given standardized position values, then the model uses the one it considers the most relevant. We might want to manually, or through another prompt, look at the 'rejected' values given by the prompt to avoid loss of data in our final report.

## Limitations / Improvements

1. Only the first sheet of the Excel file is processed
2. There is no pagination support for retrieval of reports
3. Unit Tests should be added to ensure each module / service works as expected.

## AI Usage

The following tools were used during development:
   1. **Cursor IDE (claude-3.7-sonnet):**
      - Simple data structure manipulation
      - Lookup certain Python / FastAPI documentation
      - Fix / improve syntax (Make code more 'Pythonic')
   2. **Cursor IDE (claude-3.7-sonnet-thinking):**
      - Prompt Engineering
      - Documentation & comments
      - Code review
      - Discussing improvements & alternate approaches

Challenges encountered:
   1. AI referenced outdated documentation.
   2. AI sometimes did not understand the context correctly.
   3. AI suggested approaches that were not ideal for our use case.
   4. In case of syntax / code changes, AI overly complicated things which were not necessary at all.

In summary, AI was used to aid in development, more so in fixing simple Python / SQLModel / Pydantic / FastAPI syntax issues, and also for reasoning to get feedback on the approach that I wanted to implement.
AI was not relied on solely for development & was used to enhance the reasoning & implementation process and also to improve development speed.