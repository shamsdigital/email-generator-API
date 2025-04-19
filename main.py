# email-generator-api/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import random
import requests
import os

app = FastAPI()

# Load dataset from file
with open("dataset.json", "r") as f:
    EMAIL_DATASET = json.load(f)

# API Key for OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class SummaryRequest(BaseModel):
    summary: str

# 🔍 Find matching service from summary
def detect_service(summary: str):
    services = EMAIL_DATASET.keys()
    for service in services:
        if service.lower() in summary.lower():
            return service
    return None

# 🧠 Use OpenRouter LLM to generate email
def generate_email(service: str, summary: str):
    examples = EMAIL_DATASET.get(service, [])
    example = random.choice(examples) if examples else "We offer quality services in this domain."

    prompt = f"""
You are a helpful assistant that writes cold outreach emails for digital services.

Context summary from a website:
\"\"\"
{summary}
\"\"\"

Based on the summary, write a short personalized cold email offering our service: {service}.
Use this style as reference:
\"\"\"
{example}
\"\"\"
Make sure it's friendly, relevant, and value-driven.
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

@app.post("/generate-email")
def generate_email_api(request: SummaryRequest):
    summary = request.summary
    service = detect_service(summary)

    if not service:
        raise HTTPException(status_code=400, detail="No matching service found in summary.")

    try:
        email = generate_email(service, summary)
        return {"service": service, "email": email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "Welcome to the Personalized Email Generator API!"}
