import streamlit as st
import pandas as pd
import os
import uuid
from dotenv import load_dotenv
import plotly.io as pio

# Import custom modules
import database
import auth

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Conversational BI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better aesthetics
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1 {
        color: #1E3A8A;
        font-family: 'Inter', sans-serif;
    }
    .stChatInput {
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database on app start
database.init_db()

def display_login_page():
    st.title("🔐 Login to Conversational BI")
    st.markdown("Please log in or sign up to access your secure, permanent chat sessions.")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            l_username = st.text_input("Username")
            l_password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login")
            
            if submit_login:
                user_id = auth.authenticate_user(l_username, l_password)
                if user_id:
                    st.session_state['user_id'] = user_id
                    st.session_state['username'] = l_username
                    st.session_state['session_id'] = None
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
                    
    with tab2:
        with st.form("signup_form"):
            s_username = st.text_input("Choose a Username")
            s_password = st.text_input("Choose a Password", type="password")
            submit_signup = st.form_submit_button("Create Account")
            
            if submit_signup:
                try:
                    user_id = auth.register_user(s_username, s_password)
                    st.session_state['user_id'] = user_id
                    st.session_state['username'] = s_username
                    st.session_state['session_id'] = None
                    st.success("Account created successfully! Logging in...")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

def render_sidebar():
    with st.sidebar:
        st.header(f"👋 Welcome, {st.session_state['username']}")
        if st.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()
            
        st.divider()
        st.header("⚙️ Configuration")
        st.success("Gemini API Connected Securely")
        
        st.divider()
        st.header("🕒 Your Chat Sessions")
        
        # New Chat Button
        if st.button("Start New Analysis", use_container_width=True, type="primary"):
            st.session_state['session_id'] = None
            st.session_state['messages'] = []
            st.rerun()
            
        sessions = database.get_user_sessions(st.session_state['user_id'])
        
        if not sessions:
            st.info("No saved sessions yet.")
        else:
            for s in sessions:
                # Add a container so we can put a delete button next to it
                col1, col2 = st.columns([4, 1])
                with col1:
                    is_active = st.session_state.get('session_id') == s['id']
                    btn_type = "primary" if is_active else "secondary"
                    if st.button(s['title'], key=f"sel_{s['id']}", use_container_width=True, type=btn_type):
                        st.session_state['session_id'] = s['id']
                        # Load messages
                        msgs = database.get_session_messages(s['id'])
                        for m in msgs:
                            if 'chart_json' in m and m['chart_json']:
                                try:
                                    m['figure'] = pio.from_json(m['chart_json'])
                                except Exception as e:
                                    print(e)
                                    m['figure'] = None
                        st.session_state['messages'] = msgs
                        st.rerun()
                with col2:
                    if st.button("x", key=f"del_{s['id']}"):
                        database.delete_chat_session(s['id'])
                        if st.session_state.get('session_id') == s['id']:
                            st.session_state['session_id'] = None
                            st.session_state['messages'] = []
                        st.rerun()
                        
        st.divider()
        st.header("📁 Data Source")
        uploaded_file = st.file_uploader("Upload dataset (CSV)", type=['csv'])
        use_default = st.checkbox("Use Demo Dataset", value=True)
        return uploaded_file, use_default

def display_main_app():
    uploaded_file, use_default = render_sidebar()
    
    st.title("📊 Conversational AI for Instant BI")
    
    # Load data
    if uploaded_file is not None:
        try:
            st.session_state['df'] = pd.read_csv(uploaded_file, encoding='utf-8')
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            st.session_state['df'] = pd.read_csv(uploaded_file, encoding='latin1')
    elif use_default:
        try:
            st.session_state['df'] = pd.read_csv("demo_sales_data.csv", encoding='utf-8')
        except:
             st.warning("Could not load demo dataset. Please upload one.")

    if 'df' not in st.session_state:
        st.info("Please upload a CSV file or check 'Use Demo Dataset' to begin.")
        return

    # Initialize current session if none
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    with st.expander("Preview Dataset"):
        st.dataframe(st.session_state['df'].head())
        st.caption(f"Total Rows: {len(st.session_state['df'])}, Columns: {len(st.session_state['df'].columns)}")

    st.divider()
    
    # Render historical messages in UI
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "figure" in message and message["figure"] is not None:
                st.plotly_chart(message["figure"], use_container_width=True)
                
    if prompt := st.chat_input("E.g., Which region has the highest sales?"):
        # Create session if it doesn't exist yet on first message
        if st.session_state.get('session_id') is None:
            new_id = str(uuid.uuid4())
            title = prompt[:30] + "..." if len(prompt) > 30 else prompt
            database.create_chat_session(new_id, st.session_state['user_id'], title=title)
            st.session_state['session_id'] = new_id

        # Update UI memory
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Save to DB memory
        database.save_message(st.session_state['session_id'], "user", prompt)
        
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            st.info("I am analyzing the data...")
            
            if not os.environ.get("GEMINI_API_KEY"):
                st.error("Please enter a Gemini API Key in the sidebar.")
                st.stop()
                
            import google.generativeai as genai
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            history_text = "No previous history."
            if len(st.session_state.messages) > 1:
                history_lines = []
                for msg in st.session_state.messages[:-1]:
                    content = msg["content"]
                    if msg["role"] == "assistant" and len(content) > 200:
                        content = content[:200] + "... [truncated]"
                    history_lines.append(f"{msg['role'].capitalize()}: {content}")
                history_text = "\n".join(history_lines)
                
            schema_context = get_dataframe_schema(st.session_state['df'])
            system_prompt = f"""
You are a Python data wizard. The user wants to analyze a pandas DataFrame named `df`.
Here is the schema of the DataFrame:
{schema_context}

---
PREVIOUS CONVERSATION HISTORY:
{history_text}
---

The user's CURRENT question is: "{prompt}"

Write a Python script that:
1. Takes the existing DataFrame `df`.
2. Performs data manipulation to answer the CURRENT question, taking into account the PREVIOUS CONVERSATION HISTORY if the current question is a follow-up (e.g., "Now filter that by East").
3. Uses `plotly.express` (imported as `px`) or `plotly.graph_objects` (imported as `go`) to create a helpful chart (assign the figure to a variable named `fig`). ONLY do this if a chart makes sense for the CURRENT question, otherwise leave `fig` as None.
4. Creates a string containing a short, simple business insight based on the answer (assign to a variable named `insight`).
  
Return ONLY the raw python code to be executed, no markdown formatting or text around it. E.g:
import plotly.express as px
grouped_df = df.groupby('Category')['Sales'].sum().reset_index()
fig = px.bar(grouped_df, x='Category', y='Sales')
insight = "The Technology category had the highest sales."
"""
            try:
                response = model.generate_content(system_prompt)
                code_to_execute = response.text.strip()
                if code_to_execute.startswith("```python"): code_to_execute = code_to_execute[9:]
                elif code_to_execute.startswith("```"): code_to_execute = code_to_execute[3:]
                if code_to_execute.endswith("```"): code_to_execute = code_to_execute[:-3]
                code_to_execute = code_to_execute.strip()
                
                local_vars = {'df': st.session_state['df'], 'pd': pd}
                import plotly.express as px
                import plotly.graph_objects as go
                local_vars['px'] = px
                local_vars['go'] = go
                
                exec(code_to_execute, globals(), local_vars)
                
                insight_text = local_vars.get('insight', "Here is the result of your query.")
                fig = local_vars.get('fig', None)
                
                st.markdown(insight_text)
                fig_json = None
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    fig_json = fig.to_json()
                    
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": insight_text,
                    "figure": fig if fig else None
                })
                
                # Save assistant to DB memory
                database.save_message(st.session_state['session_id'], "assistant", insight_text, chart_json=fig_json)
                
            except Exception as e:
                st.error(f"Error during analysis: {e}")
                st.code(code_to_execute, language="python")

def get_dataframe_schema(df):
    schema = []
    for col in df.columns:
        col_type = str(df[col].dtype)
        unique_vals = df[col].nunique()
        sample_vals = df[col].dropna().sample(min(3, unique_vals)).tolist() if unique_vals > 0 else []
        schema.append(f"- Column '{col}': Type {col_type}, Example values: {sample_vals}")
    return "\n".join(schema)

def main():
    if 'user_id' not in st.session_state:
        display_login_page()
    else:
        display_main_app()

if __name__ == "__main__":
    main()
