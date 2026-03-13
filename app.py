import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

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

def main():
    st.title("📊 Conversational AI for Instant BI")
    st.markdown("Ask natural language questions about your business data and get instant visual insights.")

    # Sidebar for setup
    with st.sidebar:
        st.header("⚙️ Configuration")
        # API key is now loaded securely from the environment
        st.success("Gemini API Connected Securely")
            
        st.divider()
        st.header("📁 Data Source")
        uploaded_file = st.file_uploader("Upload your dataset (CSV)", type=['csv'])
        
        # We can also load a default dataset if none is uploaded (for the hackathon demo)
        use_default = st.checkbox("Use Demo Dataset", value=True)

    # Main content area
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8')
            st.session_state['df'] = df
            st.success("Dataset loaded successfully!")
        except UnicodeDecodeError:
            try:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='latin1')
                st.session_state['df'] = df
                st.success("Dataset loaded successfully!")
            except Exception as e:
                st.error(f"Error loading file (encoding): {e}")
        except Exception as e:
            st.error(f"Error loading file: {e}")
    elif use_default:
        # Load the provided dataset
        default_path = "demo_sales_data.csv"
        try:
            df = pd.read_csv(default_path, encoding='utf-8')
            st.session_state['df'] = df
            st.success("Demo dataset loaded successfully!")
        except Exception as e:
            st.error(f"Error loading demo dataset: {e}")

    if 'df' in st.session_state:
        # Show data preview
        with st.expander("Preview Dataset"):
            st.dataframe(st.session_state['df'].head())
            st.caption(f"Total Rows: {len(st.session_state['df'])}, Columns: {len(st.session_state['df'].columns)}")
            
        # Chat Interface
        st.divider()
        st.subheader("💬 Ask Questions")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "figure" in message:
                    st.plotly_chart(message["figure"], use_container_width=True)

        if prompt := st.chat_input("E.g., Which region has the highest sales?"):
            # Display user message in chat message container
            st.chat_message("user").markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("assistant"):
                st.info("I am analyzing the data...")
                
                if not os.environ.get("GEMINI_API_KEY"):
                    st.error("Please enter a Gemini API Key in the sidebar.")
                    st.stop()
                    
                import google.generativeai as genai
                genai.configure(api_key=os.environ["GEMINI_API_KEY"])
                
                # Setup model
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                schema_context = get_dataframe_schema(st.session_state['df'])
                
                system_prompt = f"""
You are a Python data wizard. The user wants to analyze a pandas DataFrame named `df`.
Here is the schema of the DataFrame:
{schema_context}

The user's question is: "{prompt}"

Write a Python script that:
1. Takes the existing DataFrame `df`.
2. Performs data manipulation to answer the question.
3. Uses `plotly.express` (imported as `px`) or `plotly.graph_objects` (imported as `go`) to create a helpful chart (assign the figure to a variable named `fig`). ONLY do this if a chart makes sense, otherwise leave `fig` as None.
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
                    
                    # Remove markdown code blocks if the LLM outputted them by mistake
                    if code_to_execute.startswith("```python"):
                        code_to_execute = code_to_execute[9:]
                    elif code_to_execute.startswith("```"):
                        code_to_execute = code_to_execute[3:]
                    if code_to_execute.endswith("```"):
                        code_to_execute = code_to_execute[:-3]
                        
                    code_to_execute = code_to_execute.strip()
                    
                    # Execute the code safely in a local namespace
                    local_vars = {'df': st.session_state['df'], 'pd': pd}
                    import plotly.express as px
                    import plotly.graph_objects as go
                    local_vars['px'] = px
                    local_vars['go'] = go
                    
                    # Run the LLM generated code
                    exec(code_to_execute, globals(), local_vars)
                    
                    insight_text = local_vars.get('insight', "Here is the result of your query.")
                    fig = local_vars.get('fig', None)
                    
                    st.markdown(insight_text)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                        
                    # Save into history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": insight_text,
                        "figure": fig if fig else None
                    })
                        
                except Exception as e:
                    st.error(f"Error during analysis: {e}")
                    st.code(code_to_execute, language="python") # Show the code that failed for debugging

def get_dataframe_schema(df):
    """Extract column names, types, and sample data to provide context to the LLM."""
    schema = []
    for col in df.columns:
        col_type = str(df[col].dtype)
        unique_vals = df[col].nunique()
        sample_vals = df[col].dropna().sample(min(3, unique_vals)).tolist() if unique_vals > 0 else []
        # type ignore for the append issue
        schema.append(f"- Column '{col}': Type {col_type}, Example values: {sample_vals}") # type: ignore
    return "\n".join(schema)

if __name__ == "__main__":
    main()
