from datetime import datetime
from typing import Optional, List, Dict
from sqlmodel import Field, SQLModel, Relationship
from pydantic import BaseModel, field_validator

STANDARD_POSITIONS = {
    'assets': [
        ("cash_and_equivalents", "Cash, Cash and Cash Equivalents, etc."),
        ("short_term_investments", "Marketable Securities, Short-term Investments, etc."),
        ("accounts_receivable", "Accounts Receivable, Trade Receivables, etc."),
        ("inventory", "Inventory, Merchandise, etc."),
        ("prepaid_expenses", "Prepaid Expenses, Prepayments, etc."),
        ("other_current_assets", "Other Current Assets, etc."),
        ("ppe_gross", "Property Plant and Equipment, Fixed Assets, etc. (gross)"),
        ("accumulated_depreciation", "Accumulated Depreciation, etc."),
        ("ppe_net", "Property Plant and Equipment, Fixed Assets, etc. (net)"),
        ("intangible_assets", "Intangible Assets, Patents, Trademarks, etc."),
        ("goodwill", "Goodwill"),
        ("long_term_investments", "Long-term Investments, etc."),
        ("deferred_tax_liability", "Deferred Tax Liability, etc."),
        ("other_non_current_assets", "Other Non-current Assets, etc."),
        ("other_assets", "Other Assets, etc.")
    ],
    'liabilities': [
        ("accounts_payable", "Accounts Payable, Trade Payables, etc."),
        ("short_term_debt", "Short-term Debt, Short-term Loans, etc."),
        ("current_portion_lt_debt", "Current Portion of Long-term Debt, etc."),
        ("accrued_expenses", "Accrued Expenses, Accrued Liabilities, etc."),
        ("deferred_revenue", "Deferred Revenue, Unearned Revenue, etc."),
        ("income_tax_payable", "Income Tax Payable, Tax Liabilities, etc."),
        ("other_current", "Other Current Liabilities, etc."),
        ("long_term_debt", "Long-term Debt, Long-term Loans, etc."),
        ("deferred_tax_assets", "Deferred Tax Assets, etc."),
        ("pension_obligations", "Pension Obligations, Retirement Benefits, etc."),
        ("other_non_current_liabilities", "Other Non-current Liabilities, etc."),
        ("other_liabilities", "Other Liabilities, etc.")
    ],
    'equity': [
        ("common_stock", "Common Stock, Share Capital, etc."),
        ("preferred_stock", "Preferred Stock, Preference Shares, etc."),
        ("additional_paid_capital", "Additional Paid-in Capital, Share Premium, etc."),
        ("treasury_stock", "Treasury Stock, Treasury Shares, etc."),
        ("retained_earnings", "Retained Earnings, Accumulated Profits, etc."),
        ("accumulated_oci", "Accumulated Other Comprehensive Income, etc."),
        ("non_controlling_interest", "Non-controlling Interest, Minority Interest, etc."),
        ("other_equity", "Other Equity, etc.")
    ]
}

class PositionValue(SQLModel):
    current: Optional[float] = Field(default=None, ge=float('-inf'))
    previous: Optional[float] = Field(default=None, ge=float('-inf'))
class ReportPosition(PositionValue, table=True):
    __tablename__ = "report_positions"
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True)
    report_id: int = Field(foreign_key="reports.id", index=True)
    report: "Report" = Relationship(back_populates="positions")
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        all_positions = [
            pos[0] for category in STANDARD_POSITIONS.values() 
            for pos in category
        ]
        if v not in all_positions:
            raise ValueError(f"Position code '{v}' is not a standard position")
        return v

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
            position.code: PositionValue(
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