from datetime import datetime
from typing import Optional, List, Dict
from sqlmodel import Field, SQLModel, Relationship
from pydantic import BaseModel
from enum import Enum

# Defines the categories for financial positions
class PositionCategory(Enum):
    asset = "asset"
    liability = "liability"
    equity = "equity"

# Database model for types of financial positions (e.g., cash, accounts_receivable)
class PositionType(SQLModel, table=True):
    __tablename__ = "position_types"
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    description: str
    category: PositionCategory = Field()
    
# Base model for financial position values with current and previous period amounts
class PositionValue(SQLModel):
    current: Optional[float] = Field(default=None, ge=float('-inf'))
    previous: Optional[float] = Field(default=None, ge=float('-inf'))

# Junction model connecting position types to reports with their values
class ReportPosition(PositionValue, table=True):
    __tablename__ = "report_positions"
    id: Optional[int] = Field(default=None, primary_key=True)
    position_type_id: int = Field(foreign_key="position_types.id", index=True)
    position_type: PositionType = Relationship()
    report_id: int = Field(foreign_key="reports.id", index=True)
    report: "Report" = Relationship(back_populates="positions")

# Financial report model that contains multiple positions
class Report(SQLModel, table=True):
    __tablename__ = "reports"
    id: Optional[int] = Field(default=None, primary_key=True)
    processed_at: datetime = Field(default_factory=datetime.now, index=True)
    file_name: str = Field(index=True)
    positions: List[ReportPosition] = Relationship(back_populates="report")

# API response model for reports with simplified position data structure
class ReportPublic(BaseModel):
    id: int
    processed_at: datetime
    data: Dict[str, PositionValue]
    
    @classmethod
    def from_report(cls, report: Report) -> "ReportPublic":
        # Transform database model to API response format by creating a dictionary
        # of position codes mapped to their values
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