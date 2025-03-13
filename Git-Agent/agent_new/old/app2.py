import os
import streamlit as st
from langchain.agents import initialize_agent, AgentType, Tool
from langchain_openai import OpenAI
from git import Repo
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment
REPO_PATH = os.getenv("LOCAL_REPO_PATH", "local_repo")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_USER = os.getenv("GITHUB_USER")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

#######################################
# Direct Functions (No Parsing)
#######################################

def create_file_direct(file_path, content):
    """Directly create a file without parsing."""
    try:
        # Clean up file path
        if isinstance(file_path, str):
            file_path = file_path.strip()
            if file_path.startswith('"') and file_path.endswith('"'):
                file_path = file_path[1:-1]
            elif file_path.startswith("'") and file_path.endswith("'"):
                file_path = file_path[1:-1]
        
        full_path = os.path.join(REPO_PATH, file_path)
        print(f"Creating file: {full_path}")
        
        # Create directories if needed
        dir_path = os.path.dirname(full_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        with open(full_path, 'w') as f:
            f.write(content)
        
        return f"File {file_path} created successfully."
    except Exception as e:
        return f"Error creating file: {str(e)}"

def delete_file_direct(file_path):
    """Directly delete a file without parsing."""
    try:
        # Clean up file path
        if isinstance(file_path, str):
            file_path = file_path.strip()
            if file_path.startswith('"') and file_path.endswith('"'):
                file_path = file_path[1:-1]
            elif file_path.startswith("'") and file_path.endswith("'"):
                file_path = file_path[1:-1]
        
        full_path = os.path.join(REPO_PATH, file_path)
        print(f"Deleting file: {full_path}")
        
        if os.path.exists(full_path):
            os.remove(full_path)
            return f"File {file_path} deleted successfully."
        else:
            return f"File {file_path} does not exist."
    except Exception as e:
        return f"Error deleting file: {str(e)}"

def list_files_direct():
    """Directly list all files without parsing."""
    try:
        files = []
        for root, dirs, filenames in os.walk(REPO_PATH):
            if '.git' in dirs:
                dirs.remove('.git')
            
            for filename in filenames:
                rel_path = os.path.relpath(os.path.join(root, filename), REPO_PATH)
                files.append(rel_path)
        
        return files if files else "No files found in repository."
    except Exception as e:
        return f"Error listing files: {str(e)}"

def read_file_direct(file_path):
    """Directly read a file without parsing."""
    try:
        # Clean up file path
        if isinstance(file_path, str):
            file_path = file_path.strip()
            if file_path.startswith('"') and file_path.endswith('"'):
                file_path = file_path[1:-1]
            elif file_path.startswith("'") and file_path.endswith("'"):
                file_path = file_path[1:-1]
        
        full_path = os.path.join(REPO_PATH, file_path)
        print(f"Reading file: {full_path}")
        
        if not os.path.exists(full_path):
            return f"File {file_path} does not exist."
        
        with open(full_path, 'r') as f:
            content = f.read()
        
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

#######################################
# Custom Tool Functions
#######################################

def modify_code_tool(agent_input):
    """Custom tool to modify code without parsing issues."""
    print(f"ModifyCode input: {repr(agent_input)}")
    
    # Extract file_path using a simple approach
    file_path = None
    if "file_path" in agent_input:
        start_idx = agent_input.find("file_path") + len("file_path")
        # Find the first = after file_path
        eq_idx = agent_input.find("=", start_idx)
        if eq_idx > -1:
            # Find the first quote after =
            quote_idx = agent_input.find('"', eq_idx)
            if quote_idx > -1:
                # Find the closing quote
                end_quote_idx = agent_input.find('"', quote_idx + 1)
                if end_quote_idx > -1:
                    file_path = agent_input[quote_idx + 1:end_quote_idx]
    
    # Extract new_content using a simpler approach
    new_content = None
    if "new_content" in agent_input:
        start_idx = agent_input.find("new_content") + len("new_content")
        # Find the first = after new_content
        eq_idx = agent_input.find("=", start_idx)
        if eq_idx > -1:
            # Find the first quote after =
            quote_idx = agent_input.find('"', eq_idx)
            if quote_idx > -1:
                # Find the closing quote
                end_quote_idx = agent_input.rfind('"')
                if end_quote_idx > quote_idx:
                    new_content = agent_input[quote_idx + 1:end_quote_idx]
                    # Handle escaped characters
                    new_content = new_content.replace('\\n', '\n').replace('\\t', '\t')
    
    print(f"Extracted file_path: {file_path}")
    print(f"Extracted new_content length: {len(new_content) if new_content else 0}")
    
    # Check if we have both required parameters
    if not file_path:
        return "Error: Missing file_path parameter."
    if not new_content:
        return "Error: Missing new_content parameter."
    
    # Create the file
    return create_file_direct(file_path, new_content)

def delete_file_tool(agent_input):
    """Custom tool to delete files without parsing issues."""
    print(f"DeleteFile input: {repr(agent_input)}")
    
    # Extract file_path using a simple approach
    file_path = None
    if "file_path" in agent_input:
        start_idx = agent_input.find("file_path") + len("file_path")
        # Find the first = after file_path
        eq_idx = agent_input.find("=", start_idx)
        if eq_idx > -1:
            # Find the first quote after =
            quote_idx = agent_input.find('"', eq_idx)
            if quote_idx > -1:
                # Find the closing quote
                end_quote_idx = agent_input.find('"', quote_idx + 1)
                if end_quote_idx > -1:
                    file_path = agent_input[quote_idx + 1:end_quote_idx]
    
    print(f"Extracted file_path: {file_path}")
    
    # Check if we have the required parameter
    if not file_path:
        return "Error: Missing file_path parameter."
    
    # Delete the file
    return delete_file_direct(file_path)

def list_files_tool(agent_input):
    """Custom tool to list files without parsing issues."""
    print(f"ListFiles input: {repr(agent_input)}")
    return list_files_direct()

def read_file_tool(agent_input):
    """Custom tool to read files without parsing issues."""
    print(f"ReadFile input: {repr(agent_input)}")
    
    # Extract file_path using a simple approach
    file_path = None
    if "file_path" in agent_input:
        start_idx = agent_input.find("file_path") + len("file_path")
        # Find the first = after file_path
        eq_idx = agent_input.find("=", start_idx)
        if eq_idx > -1:
            # Find the first quote after =
            quote_idx = agent_input.find('"', eq_idx)
            if quote_idx > -1:
                # Find the closing quote
                end_quote_idx = agent_input.find('"', quote_idx + 1)
                if end_quote_idx > -1:
                    file_path = agent_input[quote_idx + 1:end_quote_idx]
    
    print(f"Extracted file_path: {file_path}")
    
    # Check if we have the required parameter
    if not file_path:
        return "Error: Missing file_path parameter."
    
    # Read the file
    return read_file_direct(file_path)

#######################################
# Streamlit App
#######################################

def main():
    # Page setup
    st.set_page_config(page_title="Simple Developer Assistant", page_icon="💻", layout="wide")
    
    # Session state initialization
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "agent" not in st.session_state:
        # Define tools
        tools = [
            Tool(
                name="ModifyCode",
                func=modify_code_tool,
                description="Creates or modifies a file. Inputs: file_path (str), new_content (str)."
            ),
            Tool(
                name="DeleteFile",
                func=delete_file_tool,
                description="Deletes a file. Input: file_path (str)."
            ),
            Tool(
                name="ListFiles",
                func=list_files_tool,
                description="Lists all files in the repository."
            ),
            Tool(
                name="ReadFile",
                func=read_file_tool,
                description="Reads a file. Input: file_path (str)."
            )
        ]
        
        # Create agent
        llm = OpenAI(temperature=0)
        st.session_state.agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
    
    # Page header
    st.title("💻 Simple Developer Assistant")
    st.markdown("""
    This assistant helps you with file operations in your repository.
    """)
    
    # Display repository info in sidebar
    st.sidebar.title("Repository Info")
    st.sidebar.info(f"Repo: {GITHUB_REPO}")
    st.sidebar.info(f"Path: {REPO_PATH}")
    
    # Get files list
    files = list_files_direct()
    if isinstance(files, list):
        st.sidebar.markdown("### Files:")
        for file in files[:10]:
            st.sidebar.markdown(f"- {file}")
        if len(files) > 10:
            st.sidebar.markdown(f"...and {len(files) - 10} more")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Get user input
    if prompt := st.chat_input("Ask me to help with your code..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Working..."):
                response_container = st.empty()
                try:
                    response = st.session_state.agent.run(prompt)
                    response_container.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    # Update file list in sidebar
                    files = list_files_direct()
                    if isinstance(files, list):
                        st.sidebar.markdown("### Files:")
                        for file in files[:10]:
                            st.sidebar.markdown(f"- {file}")
                        if len(files) > 10:
                            st.sidebar.markdown(f"...and {len(files) - 10} more")
                except Exception as e:
                    error_message = f"Error: {str(e)}"
                    response_container.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})

if __name__ == "__main__":
    main()