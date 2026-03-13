# 📊 Conversational AI for Instant BI Dashboards

An enterprise-grade, full-stack Business Intelligence web application that allows non-technical users to generate highly interactive data dashboards simply by asking questions in plain English.

By combining the power of **Google Gemini 2.5 Flash**, **Pandas**, and **Plotly**, this application acts as an 'Agentic Data Analyst'. It securely generates and executes Python code on-the-fly to answer complex business questions from any uploaded CSV dataset.

## ✨ Key Features
- **Data Format Agnostic:** Upload *any* CSV dataset. The application instantly reads the schema and adapts, requiring ZERO hard-coded database logic.
- **Agentic Workflow Analysis:** Instead of LLM hallucinations, the AI strictly generates Pandas/Plotly code which is executed against the real data to ensure 100% mathematical accuracy.
- **Secure User Authentication:** Built-in Login & Sign-up portal using `bcrypt` password hashing and email format validation.
- **Persistent Chat Storage:** Uses a robust **SQLite backend** (`database.py`) to permanently save user chat histories and Plotly chart states.
- **Conversational Memory:** Users can ask follow-up questions (e.g., "Now filter that chart for just the East region") and the AI will remember the previous context.
- **Interactive Dashboards:** All generated charts are fully interactive Plotly objects (Zoom, Pan, Hover tooltips).

## 🛠️ Technology Stack
* **Frontend UI & Web Server:** Streamlit (Python)
* **LLM / AI Engine:** Google Gemini API (`google-generativeai`)
* **Data Engine (In-Memory Database):** Pandas
* **Visualization Engine:** Plotly Express & Graph_Objects
* **Backend Database:** SQLite (`sqlite3`)
* **Security & Auth:** `bcrypt`

---

## 🚀 Local Development Setup

To run this project locally on your own machine:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/conversational-bi.git
   cd conversational-bi
   ```

2. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your API Key:**
   Create a `.env` file in the root directory and add your Google Studio API key:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```

4. **Launch the application & initialize the Database:**
   ```bash
   streamlit run app.py
   ```

## ☁️ Deployment (Render)
This application is fully containerized and production-ready for deployment on Render.com.

1. Push this repository to GitHub.
2. Go to **Render** -> **New Web Service**.
3. Connect your repository.
4. **Build Command:** `pip install -r requirements.txt`
5. **Start Command:** `streamlit run app.py`
6. Add `GEMINI_API_KEY` as an environment variable in Render's dashboard.
7. Deploy!
