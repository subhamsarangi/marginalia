"""
Check Gemini quota status by sending a minimal test prompt.
Usage: uv run python check_gemini.py
"""
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash", temperature=0)
try:
    r = llm.invoke([HumanMessage(content="say ok")])
    print(f"✅ Gemini available. Response: {r.content}")
except Exception as e:
    print(f"❌ Gemini unavailable: {e}")
