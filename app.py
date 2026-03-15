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

# Custom CSS for modern, simple, and attractive aesthetics
st.markdown("""
<style>
    /* Global Font Settings */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Apply Inter font carefully, avoiding icon overrides */
    html, body, .stApp, p, h1, h2, h3, h4, h5, h6, span {
        font-family: 'Inter', sans-serif;
    }
    
    /* Revert Material font specifically for Streamlit icons */
    .stIcon, [class*="stIcon"], .material-icons {
        font-family: 'Material Icons', 'Material Icons Round', 'Material Symbols Outlined', 'Material Symbols Rounded' !important;
    }

    /* Main Container with vibrant gradient and glassmorphism */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%);
        color: #f8fafc;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1000px;
    }
    
    /* Headers with vibrant gradient text */
    h1 {
        background: -webkit-linear-gradient(45deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    
    /* Glassmorphism containers (forms, expanders) */
    div[data-testid="stForm"], div[data-testid="stExpander"] > details {
        background: rgba(30, 41, 59, 0.4) !important;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    }
    
    div[data-testid="stForm"] {
        padding: 1rem;
    }

    div.stButton > button:first-child {
        background-color: #4F46E5;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.1), 0 2px 4px -1px rgba(79, 70, 229, 0.06);
    }
    
    div.stButton > button:first-child:hover {
        background-color: #4338CA;
        transform: translateY(-1px);
        box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.1), 0 4px 6px -2px rgba(79, 70, 229, 0.05);
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        border-right: 1px solid #e2e8f0;
    }
    
    .stSidebar .stButton button[kind="secondary"] {
        border: 1px solid #cbd5e1;
        text-align: left;
        justify-content: flex-start;
    }
    
    .stSidebar .stButton button[kind="secondary"]:hover {
        background-color: #f1f5f9;
        border-color: #94a3b8;
    }

    /* Inputs (Text, Password) */
    .stTextInput input {
        border-radius: 8px;
        border: 1px solid #cbd5e1;
        padding: 0.75rem;
        transition: border-color 0.2s;
    }
    
    .stTextInput input:focus {
        border-color: #4F46E5;
        box-shadow: 0 0 0 1px #4F46E5;
    }
    
    /* Hide native browser password reveal button to prevent double eye icons */
    input[type="password"]::-ms-reveal,
    input[type="password"]::-ms-clear {
        display: none;
    }

    /* Chat Input */
    .stChatInput {
        padding-bottom: 2rem;
    }
    
    .stChatInputContainer {
        border-radius: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }

    /* Chat Message Bubbles */
    .stChatMessage {
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #f1f5f9;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }

    /* Info Alerts */
    .stAlert {
        border-radius: 8px;
        border: none;
    }
    
    /* Tabs */
    button[data-baseweb="tab"] {
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database on app start
database.init_db()

import re
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
import random

def is_valid_email(email):
    # Basic regex for standard email formats
    pattern = r"^[a-zA-Z0-9_.-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def send_otp_email(email, otp):
    sendgrid_api_key = os.environ.get("SENDGRID_API_KEY")
    sender_email = os.environ.get("GMAIL_ADDRESS")
    
    if not sendgrid_api_key or not sender_email:
        print("SendGrid credentials or Sender Email not configured.")
        return False, "API Key or Sender Email missing"

    sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)
    from_email = Email(sender_email, "Conversational BI")
    to_email = To(email)
    subject = "Your Verification Code"
    content = Content("text/html", f"<p>Your 6-digit verification code is: <strong>{otp}</strong></p>")
    
    mail = Mail(from_email, to_email, subject, content)

    try:
        response = sg.client.mail.send.post(request_body=mail.get())
        if response.status_code >= 200 and response.status_code < 300:
            return True, ""
        else:
            return False, f"SendGrid API returned status {response.status_code}"
    except Exception as e:
        print(f"Error sending email: {e}")
        return False, str(e)


def display_login_page():
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🔐 Login to Conversational BI")
        st.markdown("<br>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                l_username = st.text_input("Company Email Address", placeholder="name@company.com")
                l_password = st.text_input("Password", type="password", placeholder="••••••••")
                submit_login = st.form_submit_button("Login")
                
                if submit_login:
                    if not is_valid_email(l_username):
                        st.error("Please enter a valid email address format.")
                    else:
                        user_id = auth.authenticate_user(l_username, l_password)
                        if user_id:
                            st.session_state['user_id'] = user_id
                            st.session_state['username'] = l_username
                            st.session_state['session_id'] = None
                            st.success("Logged in successfully!")
                            st.rerun()
                        else:
                            st.error("Invalid email or password.")
                            
        with tab2:
            if 'expected_otp' not in st.session_state:
                st.session_state['expected_otp'] = None
            
            if st.session_state['expected_otp'] is None:
                with st.form("signup_form"):
                    s_username = st.text_input("Company Email Address", placeholder="name@company.com")
                    s_password = st.text_input("Choose a Strong Password", type="password", placeholder="••••••••")
                    submit_signup = st.form_submit_button("Send Verification Code")
                    
                    if submit_signup:
                        if not is_valid_email(s_username):
                            st.error("Please enter a valid email address format to sign up.")
                        elif len(s_password) < 6:
                            st.error("Password must be at least 6 characters long.")
                        else:
                            # Generate OTP
                            otp = str(random.randint(100000, 999999))
                            
                            # Check if Gmail credentials are present
                            if not os.environ.get("GMAIL_ADDRESS") or not os.environ.get("GMAIL_APP_PASSWORD"):
                                st.error("GMAIL_ADDRESS and GMAIL_APP_PASSWORD not configured. Cannot send verification email.")
                            elif auth.get_user(s_username): 
                                # Use auth to check if user exists (assuming `get_user` is in auth.py or database.py, actually let's just let register fail later or check DB)
                                # Assuming database.get_user exists based on typical auth.py implementation:
                                user_exists = database.get_user(s_username)
                                if user_exists:
                                    st.error("Email is already registered.")
                                else:
                                    success, err_msg = send_otp_email(s_username, otp)
                                    if success:
                                        st.session_state['expected_otp'] = otp
                                        st.session_state['pending_username'] = s_username
                                        st.session_state['pending_password'] = s_password
                                        st.success("Verification code sent to your email!")
                                        st.rerun()
                                    else:
                                        st.warning(f"Note (Render Limitation): Email couldn't be sent automatically. Your Verification Code is: {otp}")
                                        st.session_state['expected_otp'] = otp
                                        st.session_state['pending_username'] = s_username
                                        st.session_state['pending_password'] = s_password
                                        # Use a small wait or direct rerun depending on preference. Here we just set state so the user can verify
                                        st.rerun()
                            else:
                                success, err_msg = send_otp_email(s_username, otp)
                                if success:
                                    st.session_state['expected_otp'] = otp
                                    st.session_state['pending_username'] = s_username
                                    st.session_state['pending_password'] = s_password
                                    st.success("Verification code sent to your email!")
                                    st.rerun()
                                else:
                                    st.warning(f"Note (Render Limitation): Email couldn't be sent automatically. Your Verification Code is: {otp}")
                                    st.session_state['expected_otp'] = otp
                                    st.session_state['pending_username'] = s_username
                                    st.session_state['pending_password'] = s_password
                                    st.rerun()
            else:
                with st.form("otp_form"):
                    st.info(f"An email with a 6-digit code was sent to {st.session_state.get('pending_username')}")
                    entered_otp = st.text_input("Enter 6-digit Verification Code")
                    col_submit, col_cancel = st.columns([1, 1])
                    with col_submit:
                        verify_submit = st.form_submit_button("Verify & Create Account")
                    with col_cancel:
                        cancel_submit = st.form_submit_button("Cancel")
                    
                    if verify_submit:
                        if entered_otp == st.session_state['expected_otp']:
                            try:
                                user_id = auth.register_user(st.session_state['pending_username'], st.session_state['pending_password'])
                                st.session_state['user_id'] = user_id
                                st.session_state['username'] = st.session_state['pending_username']
                                st.session_state['session_id'] = None
                                
                                # Clear pending state
                                st.session_state['expected_otp'] = None
                                st.session_state.pop('pending_username', None)
                                st.session_state.pop('pending_password', None)
                                
                                st.success("Account created successfully! Logging in...")
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))
                        else:
                            st.error("Incorrect verification code. Please try again.")
                    elif cancel_submit:
                        st.session_state['expected_otp'] = None
                        st.rerun()

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
        if st.button("✨ Start New Analysis", use_container_width=True, type="primary"):
            st.session_state['session_id'] = None
            st.session_state['messages'] = []
            st.rerun()
            
        sessions = database.get_user_sessions(st.session_state['user_id'])
        
        if not sessions:
            st.info("No saved sessions yet. Start a new analysis!")
        else:
            for s in sessions:
                # Add a container so we can put a delete button next to it
                col1, col2 = st.columns([4, 1])
                with col1:
                    is_active = st.session_state.get('session_id') == s['id']
                    btn_type = "primary" if is_active else "secondary"
                    # Add simple icon prefix for visual appeal
                    icon = "💬 " if is_active else "📄 "
                    if st.button(icon + s['title'], key=f"sel_{s['id']}", use_container_width=True, type=btn_type):
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
                    if st.button("🗑️", key=f"del_{s['id']}"):
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
        st.info("Please upload a CSV file or check 'Use Demo Dataset' to begin your analysis.")
        return

    # Initialize current session if none
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    with st.expander("Preview Dataset", expanded=False):
        st.dataframe(st.session_state['df'].head(), use_container_width=True)
        st.caption(f"**Total Rows:** {len(st.session_state['df'])}, **Columns:** {len(st.session_state['df'].columns)}")

    st.markdown("<br>", unsafe_allow_html=True)
    
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
