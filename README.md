# Conversational AI for Instant BI

A Streamlit application that allows business users to upload CSV datasets and generate interactive charts and insights using plain English through the Google Gemini API.

## Local Setup
1. Clone the repository or download the ZIP.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file and add your `GEMINI_API_KEY`.
4. Run the application:
   ```bash
   streamlit run app.py
   ```

## Deployment on Render
To deploy this project to Render:
1. Push this repository to GitHub.
2. Go to [Render](https://render.com/), sign in, and click **New > Web Service**.
3. Connect your GitHub repository.
4. Use the following settings:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py`
5. In Render's **Environment** tab, add your `GEMINI_API_KEY` as a secret environment variable.
6. Click **Deploy**!
