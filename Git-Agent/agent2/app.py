import os
import streamlit as st
import importlib.util
import pathlib

# Dynamic imports for all modules
current_dir = pathlib.Path(__file__).parent

# Import config
config_path = current_dir / "config.py"
spec = importlib.util.spec_from_file_location("config", config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

GITHUB_TOKEN = config.GITHUB_TOKEN
GITHUB_REPO = config.GITHUB_REPO
GITHUB_USER = config.GITHUB_USER
REPO_PATH = config.REPO_PATH
OPENAI_API_KEY = config.OPENAI_API_KEY

# Import utils module
utils_dir = current_dir / "utils"
file_ops_path = utils_dir / "file_operations.py"
file_ops_spec = importlib.util.spec_from_file_location("file_operations", file_ops_path)
file_operations = importlib.util.module_from_spec(file_ops_spec)
file_ops_spec.loader.exec_module(file_operations)

list_files = file_operations.list_files

# Import components
components_dir = current_dir / "components"
sidebar_path = components_dir / "sidebar.py"
sidebar_spec = importlib.util.spec_from_file_location("sidebar", sidebar_path)
sidebar = importlib.util.module_from_spec(sidebar_spec)
sidebar_spec.loader.exec_module(sidebar)

file_explorer_path = components_dir / "file_explorer.py"
file_explorer_spec = importlib.util.spec_from_file_location("file_explorer", file_explorer_path)
file_explorer = importlib.util.module_from_spec(file_explorer_spec)
file_explorer_spec.loader.exec_module(file_explorer)

render_sidebar = sidebar.render_sidebar
render_file_tree = file_explorer.render_file_tree

# Import agent tools
agent_dir = current_dir / "agent"
tools_path = agent_dir / "tools.py"
tools_spec = importlib.util.spec_from_file_location("tools", tools_path)
tools = importlib.util.module_from_spec(tools_spec)
tools_spec.loader.exec_module(tools)

initialize_agent_tools = tools.initialize_agent_tools

# Set page configuration
st.set_page_config(
    page_title="Developer Assistant",
    page_icon="💻",
    layout="wide"
)

def update_configuration(new_repo_path, new_github_repo, new_github_user, branch="main"):
    """Update the application configuration"""
    st.session_state.repo_path = new_repo_path
    st.session_state.github_repo = new_github_repo
    st.session_state.github_user = new_github_user
    st.session_state.branch = branch
    st.session_state.initialized = False  # Reinitialize the agent
    st.rerun()

def main():
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "initialized" not in st.session_state:
        st.session_state.initialized = False
    
    # Initialize repository configuration
    if "repo_path" not in st.session_state:
        st.session_state.repo_path = REPO_PATH
    
    if "github_repo" not in st.session_state:
        st.session_state.github_repo = GITHUB_REPO
        
    if "github_user" not in st.session_state:
        st.session_state.github_user = GITHUB_USER
        
    if "branch" not in st.session_state:
        st.session_state.branch = "main"
    
    # Render the sidebar
    render_sidebar(
        st.session_state.repo_path,
        st.session_state.github_repo,
        st.session_state.github_user,
        on_config_change=update_configuration
    )
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
            st.session_state.agent = initialize_agent_tools(
                st.session_state.repo_path,
                GITHUB_TOKEN,
                st.session_state.github_repo,
                st.session_state.github_user,
                OPENAI_API_KEY,
                st.session_state.branch
            )
            st.session_state.initialized = True
    
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
                    
                    # Force refresh the file explorer to show changes
                    st.rerun()
                except Exception as e:
                    error_message = f"Error: {str(e)}"
                    response_container.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
    
if __name__ == "__main__":
    main()