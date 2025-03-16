import json
import os
from typing import Any, Dict, List
from fastapi import HTTPException
from openai import AsyncOpenAI
from app.logging import logger

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4o"

async def extract_raw_financial_data(sheet_data: List[List[Any]]) -> Dict[str, Any]:
    extraction_prompt = """
    You are a financial data analyst examining spreadsheet data converted to rows. Extract all financial positions with their current and previous values.
    RULES:
    Identify financial positions by looking for accounting terms (assets, liabilities, revenue, etc.)
    For each position, extract:
    The exact position name as it appears (preserve capitalization and format)
    Current period value (if available)
    Previous period value (if available)
    In case there is data for multiple years, "Current" year is whatever the latest year in the spreadsheet, with the "Previous" year being the one before it.
    Handle hierarchical structures by identifying parent positions
    Set missing or empty values to null (don't represent as 0 or empty string)
    Ignore non-financial data (headers, notes, dates)
    Preserve the exact labels from the spreadsheet for matching against standardized terms later
    Analyze the data row by row. Values may be formatted with currency symbols, commas, or parentheses (for negative values).
    Note that the values are not in a standardized format, i.e. we could have a header "Assets" and the value for that could be later in the file next to something like "Total Assets"
    OUTPUT FORMAT:
    Return a JSON object where keys are the exact position names from the spreadsheet and values are objects with "current" and "previous" fields.
    """
    data_str = json.dumps(sheet_data, indent=2)
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a financial data extraction specialist with exceptional pattern recognition. Extract raw financial data exactly as it appears."
            },
            {
                "role": "user",
                "content": extraction_prompt + "\n\nSpreadsheet data:\n" + data_str
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.1
    )
    try:
        result = json.loads(response.choices[0].message.content)
        return result
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response from OpenAI during extraction step")
        raise HTTPException(status_code=500, detail="Failed to extract financial data")

async def standardize_financial_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    standardization_prompt = """
    Standardize the raw financial data into the required format with prefixed position names.
    STANDARDIZATION RULES:
    Map financial positions to standard column names with appropriate prefixes (a_, l_, e_)
    Convert all values to numbers (float/int) or null
    Empty or missing values must be represented as null, not 0 or empty string
    Ensure negative values are properly represented (not in parentheses)
    Attempt to match each raw label to a standard label based on meaning, not just exact text match
    If a raw label doesn't clearly match any standard label, preserve it with a generic prefix based on its category
    If multiple raw positions map to the same standard position, sum their values
    DO NOT include any total or subtotal positions - we will calculate these programmatically
    Return the output in a standard JSON format, excluding all values that are null
    STANDARD BALANCE SHEET POSITIONS:
    Assets (prefix: a_):
    a_cash_and_equivalents # Cash, Cash and Cash Equivalents, etc.
    a_short_term_investments # Marketable Securities, Short-term Investments, etc.
    a_accounts_receivable # Accounts Receivable, Trade Receivables, etc.
    a_inventory # Inventory, Merchandise, etc.
    a_prepaid_expenses # Prepaid Expenses, Prepayments, etc.
    a_other_current_assets # Other Current Assets, etc.
    a_ppe_gross # Property Plant and Equipment, Fixed Assets, etc. (gross)
    a_accumulated_depreciation # Accumulated Depreciation, etc.
    a_ppe_net # Property Plant and Equipment, Fixed Assets, etc. (net)
    a_intangible_assets # Intangible Assets, Patents, Trademarks, etc.
    a_goodwill # Goodwill
    a_long_term_investments # Long-term Investments, etc.
    a_deferred_tax # Deferred Tax Assets, etc.
    a_other_non_current # Other Non-current Assets, etc.
    Liabilities (prefix: l_):
    l_accounts_payable # Accounts Payable, Trade Payables, etc.
    l_short_term_debt # Short-term Debt, Short-term Loans, etc.
    l_current_portion_lt_debt # Current Portion of Long-term Debt, etc.
    l_accrued_expenses # Accrued Expenses, Accrued Liabilities, etc.
    l_deferred_revenue # Deferred Revenue, Unearned Revenue, etc.
    l_income_tax_payable # Income Tax Payable, Tax Liabilities, etc.
    l_other_current # Other Current Liabilities, etc.
    l_long_term_debt # Long-term Debt, Long-term Loans, etc.
    l_deferred_tax # Deferred Tax Liabilities, etc.
    l_pension_obligations # Pension Obligations, Retirement Benefits, etc.
    l_other_non_current # Other Non-current Liabilities, etc.
    Equity (prefix: e_):
    e_common_stock # Common Stock, Share Capital, etc.
    e_preferred_stock # Preferred Stock, Preference Shares, etc.
    e_additional_paid_capital # Additional Paid-in Capital, Share Premium, etc.
    e_treasury_stock # Treasury Stock, Treasury Shares, etc.
    e_retained_earnings # Retained Earnings, Accumulated Profits, etc.
    e_accumulated_oci # Accumulated Other Comprehensive Income, etc.
    e_non_controlling_interest # Non-controlling Interest, Minority Interest, etc.
    CATEGORY MATCHING GUIDANCE:
    For items that appear to be assets but don't match a standard asset position, use prefix "a_other_"
    For items that appear to be liabilities but don't match a standard liability position, use prefix "l_other_"
    For items that appear to be equity but don't match a standard equity position, use prefix "e_other_"
    Ignore any total or subtotal values - these will be calculated programmatically
    REQUIRED OUTPUT FORMAT:
    {
    "standard_column_name": {
      "current": <number or null>,
      "previous": <number or null>
    },
    ...additional positions...
    }
    """
    raw_data_str = json.dumps(raw_data, indent=2)
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a financial data standardization expert who ensures data consistency. You carefully map financial labels to standard formats and combine related positions."
            },
            {
                "role": "user",
                "content": standardization_prompt + "\n\nRaw financial data:\n" + raw_data_str
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.1
    )
    try:
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Standardized financial data: {result}")
        
        for position, values in result.items():
            if "current" in values and values["current"] == "":
                values["current"] = None
            if "previous" in values and values["previous"] == "":
                values["previous"] = None
        
        return result
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response from OpenAI during standardization step")
        raise HTTPException(status_code=500, detail="Failed to standardize financial data")

async def process_financial_data(sheet_data: List[List[Any]]) -> Dict[str, Any]:
    raw_data = await extract_raw_financial_data(sheet_data)
    standardized_data = await standardize_financial_data(raw_data)
    return standardized_data