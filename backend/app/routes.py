import json
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.excel_service import process_excel_file
from app.services.openai_service import process_financial_data
from app.models import GeneratedReport, GeneratedReportResponse
from app.logging import logger
from app.database import SessionDep

router = APIRouter(prefix="/api", tags=["Financial Data"])

@router.post("/report", response_model=GeneratedReportResponse)
async def process_report(session: SessionDep, report: UploadFile = File(...)) -> GeneratedReportResponse:
    if report.content_type not in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only .xlsx files are allowed.")

    try:
        raw_report = await process_excel_file(report)
        financial_data = await process_financial_data(raw_report)
        res = GeneratedReport(data=json.dumps(financial_data))
        logger.info(f"Generated report: {res}")
        
        session.add(res)
        session.commit()
        session.refresh(res)

        return GeneratedReportResponse(
            id=res.id,
            data=financial_data,
            processed_at=res.processed_at
        )

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get("/report/{report_id}")
def get_report(report_id: int, session: SessionDep) -> GeneratedReportResponse:
    report = session.get(GeneratedReport, report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    response = GeneratedReportResponse(
        id=report.id,
        data=json.loads(report.data),
        processed_at=report.processed_at
    )
    return response

# @router.get("/prompt-azure")
# def prompt_azure(prompt: str) -> str:
#     response = client.chat.completions.create(
#                     model=os.getenv("DEPLOYMENT_NAME"),
#                     messages=[{
#                         "role": "user",
#                         "content": [{
#                             "type": "text",
#                             "text": prompt
#                         }]
#                     }],
#                     temperature=0.7,
#                     max_tokens=200
#                 )
#     return response.choices[0].message.content

# @router.get("/prompt")
# def prompt(q: str) -> str:
#     try:
#         res = client.chat.completions.create(
#             model="gpt-4o-mini",
#             # store=True,
#             messages=[
#                 {
#                     "role": "user",
#                     "content": q
#                 }
#             ]
#         )
#         print("query: ", q)
#         print("response: ", res.choices[0].message.content)
#         return res.choices[0].message.content
#     except Exception as e:
#         return str(e)