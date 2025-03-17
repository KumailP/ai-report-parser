from datetime import datetime
from typing import Optional, List, Dict
from sqlmodel import Field, SQLModel, Relationship
from pydantic import BaseModel
from enum import Enum

class PositionCategory(Enum):
    asset = "asset"
    liability = "liability"
    equity = "equity"

class PositionType(SQLModel, table=True):
    __tablename__ = "position_types"
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    description: str
    category: PositionCategory = Field()
    
class PositionValue(SQLModel):
    current: Optional[float] = Field(default=None, ge=float('-inf'))
    previous: Optional[float] = Field(default=None, ge=float('-inf'))
class ReportPosition(PositionValue, table=True):
    __tablename__ = "report_positions"
    id: Optional[int] = Field(default=None, primary_key=True)
    position_type_id: int = Field(foreign_key="position_types.id", index=True)
    position_type: PositionType = Relationship()
    report_id: int = Field(foreign_key="reports.id", index=True)
    report: "Report" = Relationship(back_populates="positions")

class Report(SQLModel, table=True):
    __tablename__ = "reports"
    id: Optional[int] = Field(default=None, primary_key=True)
    processed_at: datetime = Field(default_factory=datetime.now, index=True)
    file_name: str = Field(index=True)
    positions: List[ReportPosition] = Relationship(back_populates="report")

class ReportPublic(BaseModel):
    id: int
    processed_at: datetime
    data: Dict[str, PositionValue]
    
    @classmethod
    def from_report(cls, report: Report) -> "ReportPublic":
        positions_dict = {
            position.position_type.code: PositionValue(
                current=position.current,
                previous=position.previous
            )
            for position in report.positions
        }
        
        return cls(
            id=report.id,
            processed_at=report.processed_at,
            data=positions_dict
        )