import os
import re
import sys
import subprocess
from git import Repo, GitCommandError
from github import Github
from dotenv import load_dotenv
import streamlit as st
from langchain.agents import initialize_agent, AgentType, Tool
from langchain_openai import OpenAI

# Load .env file
load_dotenv()

# GitHub Authentication
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_USER = os.getenv("GITHUB_USER")
REPO_PATH = os.getenv("LOCAL_REPO_PATH", "local_repo")

# Simple direct file operations
def create_file(file_path, content):
    """Create a file with the given content"""
    try:
        full_path = os.path.join(REPO_PATH, file_path)
        
        # Create directories if needed
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w') as f:
            f.write(content)
        
        return f"File {file_path} created successfully."
    except Exception as e:
        return f"Error creating file: {str(e)}"

def delete_file(file_path):
    """Delete a file"""
    try:
        full_path = os.path.join(REPO_PATH, file_path)
        
        if os.path.exists(full_path):
            os.remove(full_path)
            return f"File {file_path} deleted successfully."
        else:
            return f"File {file_path} does not exist."
    except Exception as e:
        return f"Error deleting file: {str(e)}"

def list_files():
    """List all files in the repository"""
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

# Tool wrappers
def modify_code_wrapper(inputs):
    """Create/modify a file - simple extraction"""
    print(f"ModifyCode input: {inputs}")
    
    if isinstance(inputs, str):
        # Extract file_path
        file_path_match = re.search(r'file_path\s*=\s*[\'"]([^\'"]+)[\'"]', inputs)
        file_path = file_path_match.group(1) if file_path_match else None
        
        # Extract new_content - look for everything between the first and last quote after new_content =
        if 'new_content' in inputs:
            new_content_part = inputs.split('new_content =')[1].strip()
            quote_char = new_content_part[0] if new_content_part and new_content_part[0] in ['"', "'"] else None
            if quote_char:
                # Find the matching closing quote, considering escaped quotes
                i = 1
                while i < len(new_content_part):
                    if new_content_part[i] == quote_char and new_content_part[i-1] != '\\':
                        break
                    i += 1
                if i < len(new_content_part):
                    new_content = new_content_part[1:i]
                    # Handle escaped chars
                    new_content = new_content.replace('\\n', '\n').replace('\\t', '\t')
                else:
                    new_content = None
            else:
                new_content = None
        else:
            new_content = None
    else:
        # If it's a dictionary
        file_path = inputs.get('file_path')
        new_content = inputs.get('new_content')
    
    print(f"Extracted file_path: {file_path}")
    print(f"Extracted new_content type: {type(new_content)}")
    
    if not file_path:
        return "Error: Missing file_path."
    if not new_content:
        return "Error: Missing new_content."
    
    return create_file(file_path, new_content)

def delete_file_wrapper(inputs):
    """Delete a file - simple extraction"""
    print(f"DeleteFile input: {inputs}")
    
    if isinstance(inputs, str):
        # Try to extract file_path
        if '=' not in inputs:
            # It's just the file path
            file_path = inputs.strip()
            if file_path.startswith('"') and file_path.endswith('"'):
                file_path = file_path[1:-1]
            elif file_path.startswith("'") and file_path.endswith("'"):
                file_path = file_path[1:-1]
        else:
            # Extract file_path from key=value format
            file_path_match = re.search(r'file_path\s*=\s*[\'"]([^\'"]+)[\'"]', inputs)
            file_path = file_path_match.group(1) if file_path_match else None
    else:
        # If it's a dictionary
        file_path = inputs.get('file_path')
    
    print(f"Extracted file_path: {file_path}")
    
    if not file_path:
        return "Error: Missing file_path."
    
    return delete_file(file_path)

# Streamlit app
def main():
    st.title("Simple Developer Assistant")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "agent" not in st.session_state:
        # Set up tools
        tools = [
            Tool(
                name="ModifyCode",
                func=modify_code_wrapper,
                description="Creates or modifies a file. Inputs: file_path (str), new_content (str).",
            ),
            Tool(
                name="DeleteFile",
                func=delete_file_wrapper,
                description="Deletes a file. Input: file_path (str).",
            ),
            Tool(
                name="ListFiles",
                func=lambda x: list_files(),
                description="Lists all files in the repository.",
            )
        ]
        
        # Initialize agent
        llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0)
        st.session_state.agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Get user input
    if prompt := st.chat_input("Ask me to help with your code..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Working..."):
                try:
                    response = st.session_state.agent.run(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()