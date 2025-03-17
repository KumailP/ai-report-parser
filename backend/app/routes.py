from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.excel_service import process_excel_file
from app.services.openai_service import process_financial_data
from app.logging import logger
from app.database import SessionDep
from app.models import Report, ReportPosition, ReportPublic

router = APIRouter(prefix="/api", tags=["Financial Data"])

@router.post("/report", response_model=ReportPublic)
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

@router.get("/report/{report_id}", response_model=ReportPublic)
def get_report(
    report_id: int, 
    session: SessionDep,
):
    report = session.get(Report, report_id)
    if not report:
        logger.warning(f"Report {report_id} not found")
        raise HTTPException(status_code=404, detail="Report not found")
    
    return ReportPublic.from_report(report)
