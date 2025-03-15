import os
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from openai import OpenAI, AzureOpenAI

load_dotenv()

endpoint = os.getenv("ENDPOINT_URL")
deployment = os.getenv("DEPLOYMENT_NAME")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client_azure = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=subscription_key,
    api_version="2024-05-01-preview",
)

app = FastAPI()

@app.get("/")
def root(q: str) -> dict:
    return {"message:": "Hello World!"}

@app.get("/prompt-azure")
def prompt_azure(prompt: str) -> str:
    response = client.chat.completions.create(
                    model=deployment,
                    messages=[{
                        "role": "user",
                        "content": [{
                            "type": "text",
                            "text": prompt
                        }]
                    }],
                    temperature=0.7,
                    max_tokens=200
                )
    return response.choices[0].message.content

@app.get("/prompt")
def prompt(q: str) -> str:
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            # store=True,
            messages=[
                {
                    "role": "user",
                    "content": q
                }
            ]
        )
        print("query: ", q)
        print("response: ", res.choices[0].message.content)
        return res.choices[0].message.content
    except Exception as e:
        return str(e)

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename}

@app.get("/get-report")
def get_report():
    return {"message": "Hello World!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)