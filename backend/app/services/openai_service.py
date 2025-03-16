from openai import AsyncOpenAI
import json
import os
from typing import Dict, Any
from fastapi import HTTPException
from openai import AsyncOpenAI, AsyncAzureOpenAI

endpoint = os.getenv("ENDPOINT_URL")
deployment = os.getenv("DEPLOYMENT_NAME")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")

model="gpt-4o"
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client_azure = AsyncAzureOpenAI(
    azure_endpoint=endpoint,
    api_key=subscription_key,
    api_version="2024-05-01-preview",
)

async def extract_adaptive_financial_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    prompt = """
    I have a financial spreadsheet containing various financial positions. Please analyze the data and classify each position as part of a balance sheet, income statement, or other financial statement.

    Processing Instructions:
    1. Convert all position names to snake_case (lowercase, spaces replaced with underscores, special characters removed).
    2. Identify whether the data has a flat or hierarchical structure.
    3. If hierarchical, ignore the nested values.
    5. Return null for missing values.

    Expected Output (JSON format):
    {
      "position_name": {
        "current": <value or null>,
        "previous": <value or null>,
      }
    }
    - Flat structures: Directly list positions.
    - Set missing values to null instead of calculating when at the root level.

    Example Input:
    Revenue: $1,000,000
    Expenses: $800,000
    Assets:
      - Non Current Assets: $1,000,000
        - Intangible Assets: $400,000
          - Industrial Property: $200,000
          - Other Intangible Assets: $200,000

    Example Output:
    {
      "revenue": { "current": 1000000, "previous": null },
      "expenses": { "current": 800000, "previous": null },
      "assets": {
        "current": null,
        "previous": null,
      }
    }
    Only extract financial positions, ignore headers and notes and any value that is not a standard financial position (e.g. assets, liabilities, expenses, income, payables, receivables, etc.).
    Please note that the labels may use different wordings, so we need to intelligently identify which to classify as a financial position.
    Important: The data may contain additional information that is not relevant to financial positions. Please focus only on the financial positions.
    Important: The data in the spreadsheet may be not correctly formatted, or positioned in a way that is not standard. Please adapt to these variations.
    """
    
    data_str = json.dumps(raw_data, indent=2)
    
    full_prompt = prompt + "\n" + data_str
    
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "developer", "content": "You are a financial data analyst specialized in extracting structured financial information from spreadsheets with a deep understanding of both flat and hierarchical financial statements."},
            {"role": "user", "content": full_prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    try:
        result_text = response.choices[0].message.content
        result_json = json.loads(result_text)
        
        return result_json
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error parsing OpenAI response: {str(e)}")
