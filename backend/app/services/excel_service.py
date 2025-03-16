import io
# from typing import Dict, Any
from app.logging import logger
from openpyxl import load_workbook
from fastapi import HTTPException

async def process_excel_file(report: io.BytesIO) -> dict:
    try:
        xlsx = io.BytesIO(await report.read())
        wb = load_workbook(xlsx)

        if not wb.sheetnames:
            raise HTTPException(status_code=400, detail="Excel file has no sheets")

        first_sheet = wb.sheetnames[0]
        ws = wb[first_sheet]

        rows = [
            tuple(cell.value if cell.value is not None else "" for cell in row) 
            for row in ws.iter_rows()
        ]

        sheet_data = {
            "rows": rows,
            "merged_cells": [str(cell_range) for cell_range in ws.merged_cells.ranges]
        }
        
        logger.info(f"Processed {len(rows)} rows from {first_sheet}")
        
        return sheet_data
    
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=422, detail=f"Error processing Excel file: {str(e)}")