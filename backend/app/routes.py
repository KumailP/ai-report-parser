from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Path
from app.services.excel_service import process_excel_file
from app.services.openai_service import process_financial_data
from app.logger import logger
from app.database import SessionDep
from app.models import Report, ReportPosition, ReportPublic
from sqlmodel import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api", tags=["Financial Data"])

@router.post(
    "/report",
    response_model=ReportPublic,
    summary="Process Financial Report",
    description="""
        Accept a financial report file, process it with OpenAI, and save the result to the database.
        Returns the processed report as a ReportPublic object.
    """,
    status_code=201,
    responses={
        201: {"description": "Report created successfully"},
        400: {"description": "Invalid file format"},
        500: {"description": "Processing error"}
    }
)
async def process_report(
    session: SessionDep, 
    report: UploadFile = File(
        ...,
        description="Excel file containing financial report data. Supported formats: .xlsx, .xls",
    )
):
    try:
        logger.info(f"Starting to process report file: {report.filename}")
        
        pre_processed_data = await process_excel_file(report)
        logger.info("Excel file processed successfully, starting financial data extraction")
        
        processed_positions = await process_financial_data(pre_processed_data, session)
        logger.info("Financial data processed and standardized successfully")
        
        db_report = Report(
            file_name=report.filename,
            positions=processed_positions
        )
        
        logger.info(f"Inserting report to DB with {len(db_report.positions)} positions")
        
        session.add(db_report)
        session.commit()
        session.refresh(db_report)
        
        logger.info(f"Report created successfully with ID: {db_report.id}")
        
        return ReportPublic.from_report(db_report)

    except Exception as e:
        logger.error(f"Error processing file {report.filename}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/report",
    response_model=List[ReportPublic],
    summary="Retrieve Financial Reports",
    description="""
        Retrieve report(s) by ID or filter by parameters.
        If report_id is provided, returns that specific report.
        Otherwise, returns reports matching the filter criteria.
    """,
    responses={
        200: {
            "description": "Reports retrieved successfully",
            "content": {
                "application/json": {
                    "example": [{
                        "id": 1,
                        "processed_at": "2025-03-17T10:30:00",
                        "data": {
                            "intangible_assets": {"current": 10000.0, "previous": 8500.0},
                            "accounts_receivable": {"current": 5000.0, "previous": 4800.0}
                        }
                    }]
                }
            }
        },
        400: {"description": "Missing required parameters"},
        404: {"description": "Report not found"}
    }
)
def get_report(
    session: SessionDep,
    report_id: Optional[int] = Query(
        None, 
        description="Unique identifier for a specific report",
        example=1
    ),
    file_name: Optional[str] = Query(
        None, 
        description="Name of the uploaded file"
    ),
    start_date: Optional[datetime] = Query(
        None, 
        description="Filter reports processed after this date (ISO 8601 format: YYYY-MM-DDTHH:MM:SS)",
    ),
    end_date: Optional[datetime] = Query(
        None, 
        description="Filter reports processed before this date (ISO 8601 format: YYYY-MM-DDTHH:MM:SS)",
    ),
    position_code: Optional[str] = Query(
        None, 
        description="Filter by specific financial position code. Financial codes are standardized and follow snake_case naming convention."
    ),
    min_current_value: Optional[float] = Query(
        None, 
        description="Minimum value for current period"
    ),
    max_current_value: Optional[float] = Query(
        None, 
        description="Maximum value for current period"
    ),
    min_previous_value: Optional[float] = Query(
        None, 
        description="Minimum value for previous period"
    ),
    max_previous_value: Optional[float] = Query(
        None, 
        description="Maximum value for previous period"
    )
):
    if report_id is None and position_code is None and file_name is None:
        logger.warning("Request missing required parameters: either report_id, file_name, or position_code must be provided")
        raise HTTPException(
            status_code=400, 
            detail="Either report_id, file_name, or position_code must be provided"
        )
    
    query = select(Report).options(selectinload(Report.positions))
    
    if report_id is not None:
        report = session.exec(query.where(Report.id == report_id)).first()
        if not report:
            logger.warning(f"Report {report_id} not found")
            raise HTTPException(status_code=404, detail="Report not found")
        return [ReportPublic.from_report(report)]
    
    if file_name is not None:
        query = query.where(Report.file_name == file_name)
    
    if start_date:
        query = query.where(Report.processed_at >= start_date)
    if end_date:
        query = query.where(Report.processed_at <= end_date)
    
    has_value_filters = any([
        min_current_value is not None,
        max_current_value is not None,
        min_previous_value is not None,
        max_previous_value is not None
    ])
    
    query = query.join(ReportPosition)
    query = query.where(ReportPosition.code == position_code)
    
    if min_current_value is not None:
        query = query.where(ReportPosition.current >= min_current_value)
    if max_current_value is not None:
        query = query.where(ReportPosition.current <= max_current_value)
    if min_previous_value is not None:
        query = query.where(ReportPosition.previous >= min_previous_value)
    if max_previous_value is not None:
        query = query.where(ReportPosition.previous <= max_previous_value)
    
    query = query.distinct()
    
    reports = session.exec(query).all()
    
    if not reports:
        filter_desc = " with position_code filter"
        if has_value_filters or start_date or end_date:
            filter_desc += " and additional filters"
        logger.info(f"No reports found{filter_desc}")
    else:
        logger.info(f"Found {len(reports)} reports")
    
    return [ReportPublic.from_report(report) for report in reports]
