import os
import re
import subprocess
import sys
from git import Repo, GitCommandError
from github import Github
from dotenv import load_dotenv
import streamlit as st
from langchain.agents import initialize_agent, AgentType, Tool
from langchain_openai import OpenAI

# Load environment variables
load_dotenv()

# GitHub Authentication
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_USER = os.getenv("GITHUB_USER")
REPO_PATH = os.getenv("LOCAL_REPO_PATH", "local_repo")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Constants
MAX_CONTENT_DISPLAY = 1000  # Maximum characters to display in logs
MAX_FILE_SIZE = 50000  # Maximum file size to process in tools

#######################################
# Direct File Operations
#######################################

def clone_repo(local_path):
    """Clones a GitHub repository locally using authentication."""
    try:
        print(f"Attempting to clone/update repository to {local_path}")
        
        # Construct the authenticated repository URL
        github_repo_url = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git"
        print(f"Using repo URL: {github_repo_url.replace(GITHUB_TOKEN, '***')}")
        
        if not os.path.exists(local_path):
            print(f"Creating directory {local_path}")
            os.makedirs(local_path, exist_ok=True)
            print(f"Cloning {GITHUB_REPO} into {local_path}...")
            Repo.clone_from(github_repo_url, local_path)
            return f"Repository cloned to {local_path}"
        elif os.path.exists(os.path.join(local_path, ".git")):
            print(f"Repository already exists at {local_path}, pulling latest changes")
            repo_local = Repo(local_path)
            repo_local.git.pull()
            return f"Repository already exists locally. Pulled latest changes."
        else:
            print(f"Directory {local_path} exists but is not a git repository. Initializing...")
            try:
                # Remove directory contents if any
                for item in os.listdir(local_path):
                    item_path = os.path.join(local_path, item)
                    if os.path.isfile(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        import shutil
                        shutil.rmtree(item_path)
                
                # Clone the repository
                Repo.clone_from(github_repo_url, local_path)
                return f"Repository initialized and cloned to {local_path}"
            except Exception as e:
                return f"Error initializing repository: {str(e)}"
    except Exception as e:
        return f"Error cloning repository: {str(e)}"

def create_file(file_path, content, repo_path):
    """Create a file with the given content"""
    try:
        # Clean up file path - remove quotes
        if isinstance(file_path, str):
            file_path = file_path.strip()
            if (file_path.startswith('"') and file_path.endswith('"')) or \
               (file_path.startswith("'") and file_path.endswith("'")):
                file_path = file_path[1:-1]
        
        full_path = os.path.join(repo_path, file_path)
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

def delete_file(file_path, repo_path):
    """Delete a file"""
    try:
        # Clean up file path - remove quotes
        if isinstance(file_path, str):
            file_path = file_path.strip()
            if (file_path.startswith('"') and file_path.endswith('"')) or \
               (file_path.startswith("'") and file_path.endswith("'")):
                file_path = file_path[1:-1]
        
        full_path = os.path.join(repo_path, file_path)
        print(f"Deleting file: {full_path}")
        
        if os.path.exists(full_path):
            os.remove(full_path)
            return f"File {file_path} deleted successfully."
        else:
            return f"File {file_path} does not exist."
    except Exception as e:
        return f"Error deleting file: {str(e)}"

def list_files(repo_path, directory_path=""):
    """List all files in the repository or directory"""
    try:
        # Clean up directory path - remove quotes
        if isinstance(directory_path, str):
            directory_path = directory_path.strip()
            if (directory_path.startswith('"') and directory_path.endswith('"')) or \
               (directory_path.startswith("'") and directory_path.endswith("'")):
                directory_path = directory_path[1:-1]
        
        # Determine the directory to list files from
        if not directory_path:
            dir_path = repo_path
        else:
            dir_path = os.path.join(repo_path, directory_path)
        
        print(f"Listing files in: {dir_path}")
        
        if not os.path.exists(dir_path):
            return f"Directory {directory_path} does not exist."
        
        files = []
        for root, dirs, filenames in os.walk(dir_path):
            if '.git' in dirs:
                dirs.remove('.git')
            
            for filename in filenames:
                rel_path = os.path.relpath(os.path.join(root, filename), repo_path)
                # Add file size information
                full_path = os.path.join(root, filename)
                size = os.path.getsize(full_path)
                size_str = f"{size} bytes"
                if size > 1024:
                    size_str = f"{size/1024:.1f} KB"
                if size > 1024*1024:
                    size_str = f"{size/(1024*1024):.1f} MB"
                
                files.append(f"{rel_path} ({size_str})")
        
        return files if files else f"No files found in {directory_path or 'repository'}."
    except Exception as e:
        return f"Error listing files: {str(e)}"

def read_file(file_path, repo_path):
    """Read the content of a file"""
    try:
        # Clean up file path - remove quotes
        if isinstance(file_path, str):
            file_path = file_path.strip()
            if (file_path.startswith('"') and file_path.endswith('"')) or \
               (file_path.startswith("'") and file_path.endswith("'")):
                file_path = file_path[1:-1]
        
        full_path = os.path.join(repo_path, file_path)
        print(f"Reading file: {full_path}")
        
        if not os.path.exists(full_path):
            return f"File {file_path} does not exist."
        
        # Check file size before reading
        file_size = os.path.getsize(full_path)
        if file_size > MAX_FILE_SIZE:
            preview_size = min(5000, file_size // 10)  # Show at most 5000 chars or 10% of file
            with open(full_path, 'r') as f:
                content_preview = f.read(preview_size)
            
            return (f"File {file_path} is too large ({file_size} bytes) to process in full. "
                   f"Here's a preview of the first {preview_size} characters:\n\n"
                   f"{content_preview}\n\n..."
                   f"\n\nPlease use a more specific command to work with sections of this file.")
            
        with open(full_path, 'r') as f:
            content = f.read()
        
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

def commit_and_push(file_path, commit_message, repo_path):
    """Commit and push changes to GitHub"""
    try:
        # Clean up file path - remove quotes
        if isinstance(file_path, str):
            file_path = file_path.strip()
            if (file_path.startswith('"') and file_path.endswith('"')) or \
               (file_path.startswith("'") and file_path.endswith("'")):
                file_path = file_path[1:-1]
        
        print(f"Committing and pushing file: {file_path}")
        
        if not os.path.exists(os.path.join(repo_path, ".git")):
            return f"Error: {repo_path} is not a git repository"
        
        try:
            repo_local = Repo(repo_path)
            repo_local.git.add(file_path)
            repo_local.index.commit(commit_message)
            
            # Push using token authentication
            github_repo_url = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git"
            origin = repo_local.remote(name="origin")
            origin.set_url(github_repo_url)
            origin.push()
            
            return f"Changes pushed: {commit_message}"
        except GitCommandError as e:
            return f"Git error: {e}"
    except Exception as e:
        return f"Error in commit_and_push: {str(e)}"

#######################################
# Tool Wrappers with Simple Parsing
#######################################

def find_closing_quote(s, start_idx, quote_char):
    """Helper to find the closing quote, handling escaped quotes"""
    i = start_idx
    while i < len(s):
        if s[i] == quote_char and (i == start_idx or s[i-1] != '\\'):
            return i
        i += 1
    return -1

def modify_code_wrapper(inputs):
    """Wrapper for create_file - simplified and robust parsing"""
    print(f"ModifyCode received: {repr(inputs)[:MAX_CONTENT_DISPLAY]}")
    
    file_path = None
    new_content = None
    
    # Handle dictionary input
    if not isinstance(inputs, str):
        file_path = inputs.get('file_path')
        new_content = inputs.get('new_content')
    else:
        # Extract file_path from inputs string
        file_path_match = re.search(r'file_path\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
        if file_path_match:
            file_path = file_path_match.group(1)
            print(f"Extracted file_path: {file_path}")
        
        # Extract new_content using custom logic to handle quoted strings
        if "new_content =" in inputs:
            start_idx = inputs.find("new_content =") + len("new_content =")
            content_part = inputs[start_idx:].strip()
            
            if content_part.startswith('"'):
                # Find the closing double quote
                end_idx = find_closing_quote(content_part, 1, '"')
                if end_idx > 0:
                    new_content = content_part[1:end_idx]
            elif content_part.startswith("'"):
                # Find the closing single quote
                end_idx = find_closing_quote(content_part, 1, "'")
                if end_idx > 0:
                    new_content = content_part[1:end_idx]
            
            # If we found content, handle escape sequences
            if new_content:
                new_content = new_content.replace('\\n', '\n').replace('\\t', '\t')
                print(f"Extracted new_content: {new_content[:50]}... (length: {len(new_content)})")
    
    # Validate parameters
    if not file_path:
        return "Error: Missing file_path parameter."
    if not new_content:
        # Try a last resort approach to capture content
        if isinstance(inputs, str) and "new_content =" in inputs:
            parts = inputs.split("new_content =")
            if len(parts) == 2:
                content_str = parts[1].strip()
                if content_str:
                    # Take everything as content
                    new_content = content_str
                    # Remove trailing quotes or commas if present
                    while new_content and new_content[-1] in ['"', "'", ',']: 
                        new_content = new_content[:-1]
                    print(f"Last resort extracted content: {new_content[:50]}... (length: {len(new_content)})")
        
        # If still no content, return error
        if not new_content:            
            return "Error: Missing or invalid new_content parameter."
    
    # Call the function
    return create_file(file_path, new_content, REPO_PATH)

def delete_file_wrapper(inputs):
    """Wrapper for delete_file - simplified parsing"""
    print(f"DeleteFile received: {repr(inputs)[:MAX_CONTENT_DISPLAY]}")
    
    file_path = None
    
    # Handle dictionary input
    if not isinstance(inputs, str):
        file_path = inputs.get('file_path')
    else:
        # Try parameter format
        file_path_match = re.search(r'file_path\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
        if file_path_match:
            file_path = file_path_match.group(1)
        else:
            # Try direct format (just the path)
            file_path = inputs.strip()
            if (file_path.startswith('"') and file_path.endswith('"')) or \
               (file_path.startswith("'") and file_path.endswith("'")):
                file_path = file_path[1:-1]
    
    # Validate parameters
    if not file_path:
        return "Error: Missing file_path parameter."
    
    print(f"Extracted file_path: {file_path}")
    
    # Call the function
    return delete_file(file_path, REPO_PATH)

def list_files_wrapper(inputs):
    """Wrapper for list_files - simplified parsing"""
    print(f"ListFiles received: {repr(inputs)[:MAX_CONTENT_DISPLAY]}")
    
    directory_path = ""
    
    # Handle dictionary or None input
    if not isinstance(inputs, str):
        directory_path = inputs.get('directory_path', "") if inputs else ""
    else:
        # Try parameter format
        dir_path_match = re.search(r'directory_path\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
        if dir_path_match:
            directory_path = dir_path_match.group(1)
        elif inputs.strip():
            # Try direct format (just the path)
            directory_path = inputs.strip()
            if (directory_path.startswith('"') and directory_path.endswith('"')) or \
               (directory_path.startswith("'") and directory_path.endswith("'")):
                directory_path = directory_path[1:-1]
    
    print(f"Extracted directory_path: {directory_path}")
    
    # Call the function
    return list_files(REPO_PATH, directory_path)

def read_file_wrapper(inputs):
    """Wrapper for read_file - simplified parsing"""
    print(f"ReadFile received: {repr(inputs)[:MAX_CONTENT_DISPLAY]}")
    
    file_path = None
    
    # Handle dictionary input
    if not isinstance(inputs, str):
        file_path = inputs.get('file_path')
    else:
        # Try parameter format
        file_path_match = re.search(r'file_path\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
        if file_path_match:
            file_path = file_path_match.group(1)
        else:
            # Try direct format (just the path)
            file_path = inputs.strip()
            if (file_path.startswith('"') and file_path.endswith('"')) or \
               (file_path.startswith("'") and file_path.endswith("'")):
                file_path = file_path[1:-1]
    
    # Validate parameters
    if not file_path:
        return "Error: Missing file_path parameter."
    
    print(f"Extracted file_path: {file_path}")
    
    # Call the function
    return read_file(file_path, REPO_PATH)

def commit_and_push_wrapper(inputs):
    """Wrapper for commit_and_push - simplified parsing"""
    print(f"CommitAndPush received: {repr(inputs)[:MAX_CONTENT_DISPLAY]}")
    
    file_path = None
    commit_message = "Update code"
    
    # Handle dictionary input
    if not isinstance(inputs, str):
        file_path = inputs.get('file_path')
        commit_message = inputs.get('commit_message', "Update code")
    else:
        # Try parameter format for file_path
        file_path_match = re.search(r'file_path\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
        if file_path_match:
            file_path = file_path_match.group(1)
        
        # Try parameter format for commit_message
        commit_msg_match = re.search(r'commit_message\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
        if commit_msg_match:
            commit_message = commit_msg_match.group(1)
        
        # If no parameter format for file_path, try direct format
        if not file_path:
            parts = inputs.split(maxsplit=1)
            if len(parts) >= 1:
                file_path = parts[0].strip()
                if (file_path.startswith('"') and file_path.endswith('"')) or \
                   (file_path.startswith("'") and file_path.endswith("'")):
                    file_path = file_path[1:-1]
                
                if len(parts) > 1:
                    commit_message = parts[1].strip()
                    if (commit_message.startswith('"') and commit_message.endswith('"')) or \
                       (commit_message.startswith("'") and commit_message.endswith("'")):
                        commit_message = commit_message[1:-1]
    
    # Validate parameters
    if not file_path:
        return "Error: Missing file_path parameter."
    
    print(f"Extracted file_path: {file_path}")
    print(f"Extracted commit_message: {commit_message}")
    
    # Call the function
    return commit_and_push(file_path, commit_message, REPO_PATH)

#######################################
# Streamlit Application
#######################################

def initialize_agent_tools():
    """Initialize the agent and tools."""
    # Ensure the repository is cloned before running operations
    with st.spinner("Initializing repository..."):
        clone_status = clone_repo(REPO_PATH)
        st.success(f"Repository status: {clone_status}")
    
    # Define tools for the agent - using our simple wrappers
    tools = [
        Tool(
            name="ModifyCode",
            func=modify_code_wrapper,
            description="Creates or modifies a file in the repository. Inputs: file_path (str), new_content (str).",
        ),
        Tool(
            name="DeleteFile",
            func=delete_file_wrapper,
            description="Deletes a file from the repository. Input: file_path (str).",
        ),
        Tool(
            name="ListFiles",
            func=list_files_wrapper,
            description="Lists files in the repository or a specific directory. Input (optional): directory_path (str).",
        ),
        Tool(
            name="ReadFile",
            func=read_file_wrapper,
            description="Reads the content of a file. Input: file_path (str).",
        ),
        Tool(
            name="CommitAndPush",
            func=commit_and_push_wrapper,
            description="Commits and pushes changes to GitHub. Inputs: file_path (str), commit_message (str, optional).",
        )
    ]
    
    # Initialize LangChain LLM with a smaller token limit
    llm = OpenAI(
        model="gpt-3.5-turbo-instruct", 
        temperature=0,
        max_tokens=1000,  # Limit output tokens
    )
    
    # Create an agent with a more efficient configuration
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5,  # Limit number of thinking steps to avoid token explosion
        max_execution_time=30,  # Limit execution time (seconds)
        early_stopping_method="generate"  # Stop when we have a reasonable answer
    )
    
    return agent

# Set up Streamlit app
def main():
    # Set page configuration
    st.set_page_config(
        page_title="Developer Assistant",
        page_icon="💻",
        layout="wide"
    )
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "initialized" not in st.session_state:
        st.session_state.initialized = False
    
    # Sidebar
    st.sidebar.title("Developer Assistant")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Repository Info")
    st.sidebar.info(f"Repository: {GITHUB_REPO}")
    st.sidebar.info(f"Local path: {REPO_PATH}")
    
    # Main content
    st.title("💻 Developer Assistant")
    st.markdown("""
    This chatbot helps you with coding tasks by interacting with your Git repository. 
    You can ask it to:
    - Create or modify files
    - Delete files
    - List files in the repository
    - Read file contents
    - Commit and push changes
    """)
    
    # Initialize the agent if not already done
    if not st.session_state.initialized:
        with st.spinner("Setting up the developer assistant..."):
            st.session_state.agent = initialize_agent_tools()
            st.session_state.initialized = True
        
        # Display repository info
        repo_files = list_files(REPO_PATH)
        if isinstance(repo_files, list):
            st.sidebar.markdown("**Files in repository:**")
            for file in repo_files[:10]:  # Show only first 10 files
                st.sidebar.markdown(f"- {file}")
            if len(repo_files) > 10:
                st.sidebar.markdown(f"...and {len(repo_files) - 10} more files")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me to help with your code..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response_container = st.empty()
                try:
                    # Limit prompt size to avoid rate limit errors
                    if len(prompt) > 2000:
                        prompt_truncated = prompt[:2000] + "... [truncated for processing]"
                        response = st.session_state.agent.run(prompt_truncated)
                        response = "Note: Your input was truncated due to size limitations.\n\n" + response
                    else:
                        response = st.session_state.agent.run(prompt)
                    
                    response_container.markdown(response)
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    # Update repository info
                    repo_files = list_files(REPO_PATH)
                    if isinstance(repo_files, list):
                        st.sidebar.markdown("**Files in repository:**")
                        for file in repo_files[:10]:  # Show only first 10 files
                            st.sidebar.markdown(f"- {file}")
                        if len(repo_files) > 10:
                            st.sidebar.markdown(f"...and {len(repo_files) - 10} more files")
                except Exception as e:
                    error_message = f"Error: {str(e)}"
                    response_container.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})

if __name__ == "__main__":
    main()