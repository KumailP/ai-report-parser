import io
# from typing import Dict, Any
from app.logging import logger
from openpyxl import load_workbook
from fastapi import HTTPException

async def process_excel_file(report: io.BytesIO) -> str:
    try:
        xlsx = io.BytesIO(await report.read())
        wb = load_workbook(xlsx)

        if not wb.sheetnames:
            raise HTTPException(status_code=400, detail="Excel file has no sheets")

        first_sheet = wb.sheetnames[0]
        ws = wb[first_sheet]

        rows = [row for row in ws.iter_rows(values_only=True)]

        logger.info(f"Processed {len(rows)} rows from {first_sheet}")
        
        return rows
    
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error processing Excel file: {str(e)}")