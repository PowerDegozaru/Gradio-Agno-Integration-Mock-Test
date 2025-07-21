"""
playground.py
Very small file whose only job is to expose `report_agent`
via the Playground UI at http://localhost:7777/v1
"""
from agno.playground import Playground
from report_agent import report_agent   # ✅ import the agent you just defined

# Build the Playground with *only* that agent (add more to the list if you wish)
playground_app = Playground(agents=[report_agent])
app = playground_app.get_app()

if __name__ == "__main__":
    # serves FastAPI at http://localhost:7777/v1
    playground_app.serve("playground:app", reload=True)
