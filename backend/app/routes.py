from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.excel_service import process_excel_file
from app.services.openai_service import process_financial_data
from app.logging import logger
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
    description="""
        Accept a financial report file, process it with OpenAI, and save the result to the database.
        Returns the processed report as a ReportPublic object.
    """)
async def process_report(session: SessionDep, report: UploadFile = File(...)):
    try:
        logger.info(f"Starting to process report file: {report.filename}")
        
        pre_processed_data = await process_excel_file(report)
        logger.info("Excel file processed successfully, starting financial data extraction")
        
        financial_data = await process_financial_data(pre_processed_data)
        logger.info("Financial data processed and standardized successfully")
        
        positions = [
            ReportPosition(
                code=code,
                current=data.current,
                previous=data.previous
            )
            for code, data in financial_data.items()
        ]
        db_report = Report(positions=positions)
        
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
    description="""
        Retrieve report(s) by ID or filter by parameters.
        If report_id is provided, returns that specific report.
        Otherwise, returns reports matching the filter criteria.
    """)
def get_report(
    session: SessionDep,
    report_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    position_code: Optional[str] = None,
    min_current_value: Optional[float] = None,
    max_current_value: Optional[float] = None,
    min_previous_value: Optional[float] = None,
    max_previous_value: Optional[float] = None
):
    if report_id is None and position_code is None:
        logger.warning("Request missing required parameters: either report_id or position_code must be provided")
        raise HTTPException(
            status_code=400, 
            detail="Either report_id or position_code must be provided"
        )
    
    query = select(Report).options(selectinload(Report.positions))
    
    if report_id is not None:
        report = session.exec(query.where(Report.id == report_id)).first()
        if not report:
            logger.warning(f"Report {report_id} not found")
            raise HTTPException(status_code=404, detail="Report not found")
        return [ReportPublic.from_report(report)]
    
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
