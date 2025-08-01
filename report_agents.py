"""
report_agent.py
Central place to define the “Report Agent”.

You can swap the model, tools, or instructions here without ever
touching playground.py again.
"""
import os
from dotenv import load_dotenv          # only needed when you keep keys in a .env

from agno.agent import Agent
from agno.models.google import Gemini   # or agno.models.openai import OpenAI, etc.
from agno.tools.duckduckgo import DuckDuckGoTools

from report_merge_tool import merge_scan_reports

# --------------------------------------------------------------------------- #
# Environment / API keys
# --------------------------------------------------------------------------- #
load_dotenv()                           # pulls GEMINI_API_KEY into the process
# If GOOGLE_API_KEY isn't already set, copy it from GEMINI_API_KEY
GEMINI_KEY = os.getenv("GOOGLE_API_KEY")

# --------------------------------------------------------------------------- #
# Agent definition
# --------------------------------------------------------------------------- #
report_agent = Agent(
    name="Report Agent",
    model=Gemini(
        id="gemini-2.5-flash",
        grounding=True,
        search=True,
    ),
    tools=[
        DuckDuckGoTools(),
        merge_scan_reports,          
    ],
    show_tool_calls=True,
    instructions=[
        "When the user asks to merge or summarise scan outputs, call merge_scan_reports.",
        "Return direct download paths for the PDF and JSON artefacts.",
        "Write clear, concise analytical reports.",
        "Always cite your sources."
    ],
    markdown=True,
)