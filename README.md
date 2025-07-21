pip install -r requirements.txt

pip install audioop-lts

python app.py

Open http://localhost:7860 in your browser





Agno

python -m venv ~/.venvs/agno
source ~/.venvs/agno/Scripts/activate

pip install -U agno fastapi[standard] duckduckgo-search yfinance sqlalchemy
pip install -U agno google-genai
pip install markdown weasyprint 

For Local run agno ui
npx create-agent-ui@latest

cd agent-ui
npm install
npm run dev
