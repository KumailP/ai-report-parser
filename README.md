# Financial Report Structuring Microservice

A robust microservice that processes Excel-based financial reports and transforms them into standardized JSON data using AI.

## Project Overview

This project is a solution to the Financial Report Structuring challenge, implementing a FastAPI backend service that:

1. Accepts Excel files containing financial report data
2. Processes and interprets the varying structure using OpenAI's GPT-4o
3. Transforms raw data into a standardized JSON format
4. Stores processed reports in a database
5. Provides RESTful API endpoints for upload and retrieval

## Features

- **File Upload & Processing**: Validates and extracts data from Excel files
- **AI-Powered Data Structuring**: Uses GPT-4o to intelligently interpret and standardize financial data
- **RESTful API**: Comprehensive endpoints with Swagger documentation
- **Database Integration**: SQLite with SQLModel ORM for efficient data storage and retrieval
- **Containerization**: Docker and docker-compose setup for easy deployment

## Technical Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLite with SQLModel
- **Excel Processing**: openpyxl
- **AI Integration**: OpenAI API (GPT-4o)
- **Containerization**: Docker, docker-compose

## Getting Started

### Prerequisites

- Docker and docker-compose
- OpenAI API key

### Setup and Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Configure OpenAI API key:
   - Copy the sample environment file in the backend directory
   - Add your OpenAI API key to the `.env` file:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

3. Start the application:
   ```bash
   docker-compose up
   ```

4. Access the API:
   - API: http://localhost:8000/api
   - Swagger Documentation: http://localhost:8000/docs

## API Usage

### Upload a Financial Report

```bash
curl -X 'POST' \
  'http://localhost:8000/api/report' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'report=@path/to/your/financial_report.xlsx'
```

### Retrieve Reports

```bash
# Get all reports
curl -X 'GET' 'http://localhost:8000/api/report' -H 'accept: application/json'

# Get a specific report by ID
curl -X 'GET' 'http://localhost:8000/api/report?report_id=1' -H 'accept: application/json'

# Filter reports by various parameters
curl -X 'GET' 'http://localhost:8000/api/report?file_name=quarterly_report.xlsx' -H 'accept: application/json'
```

## Development

For further details on the backend implementation, please refer to the [Backend README](backend/README.md).

## AI Integration Details

The project integrates OpenAI's GPT-4o model to:
1. Analyze the structure of uploaded Excel reports
2. Identify financial data regardless of format variations
3. Extract and standardize balance sheet positions
4. Map raw data to a consistent output schema

The AI integration provides resilience against varying report formats, making the system adaptable to different financial report structures without requiring manual template mapping.

## Docker Deployment

The application is containerized for easy deployment:

- `docker-compose.yml` sets up the API service
- The backend Dockerfile builds a Python environment with all dependencies
- Volumes are configured for development convenience

## License

[Your License Here]