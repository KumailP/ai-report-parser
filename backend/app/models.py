from openai import BaseModel
from sqlmodel import Field, SQLModel
from datetime import datetime
from typing import Optional, Dict

class FinancialPosition(BaseModel):
    current: Optional[float] = None
    previous: Optional[float] = None
    # items: Optional[Dict[str, 'FinancialPosition']] = None

# FinancialPosition.model_rebuild()

class FinancialReport(BaseModel):
    data: Dict[str, FinancialPosition]

class GeneratedReport(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
    data: str = Field()
    processed_at: datetime | None = Field(default=datetime.now())
    
class GeneratedReportResponse(BaseModel):
    id: int
    data: Dict[str, FinancialPosition]
    processed_at: datetime