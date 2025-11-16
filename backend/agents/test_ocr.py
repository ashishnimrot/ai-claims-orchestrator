# backend/agents/test_ocr.py

import os
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.agents.document_analyzer import DocumentAnalyzerAgent
from backend.models.schemas import AgentResult

# ---------------------------------------------------------------------
# 1. Load .env and Gemini key
# ---------------------------------------------------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in .env or environment!")

# LLM for LangChain agent
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=GEMINI_API_KEY,
)

# ---------------------------------------------------------------------
# 2. Build absolute paths to /backend/samples
# ---------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]   # -> backend/
SAMPLES_DIR = BASE_DIR / "samples"

documents = [
    str(SAMPLES_DIR / "accident_photo.JPG"),   # note: .JPG (capital)
    str(SAMPLES_DIR / "medical_receipt.jpg"),
    str(SAMPLES_DIR / "prescription.png"),
    str(SAMPLES_DIR / "repair_estimate.jpg"),
    str(SAMPLES_DIR / "police_report.pdf"),
    str(SAMPLES_DIR / "hospital_bill.pdf"),
]

# Simple fake claim data for testing
claim_data = {
    "claim_type": "auto",
    "claim_amount": 2200,
    "incident_date": "2025-11-13",
    "claimant_name": "Arjun Mehta",
    "description": "Rear bumper damage from minor car accident, "
                   "with wrist injury treated at City Orthopedic Clinic.",
    "documents": documents,
}

# ---------------------------------------------------------------------
# 3. Run the DocumentAnalyzerAgent
# ---------------------------------------------------------------------
async def main():
    agent = DocumentAnalyzerAgent(llm=llm, gemini_api_key=GEMINI_API_KEY)
    result: AgentResult = await agent.analyze(claim_data, documents=documents)

    print("STATUS:", result.status)
    print("CONFIDENCE:", result.confidence)
    print("FINDINGS:", result.findings)
    print("RECOMMENDATIONS:", result.recommendations)
    print("METADATA:", result.metadata)


if __name__ == "__main__":
    asyncio.run(main())
