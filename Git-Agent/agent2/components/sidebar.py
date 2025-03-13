import streamlit as st
import os
import importlib.util
import pathlib
from git import Repo, GitCommandError

# Dynamic import for file_operations
utils_dir = pathlib.Path(__file__).parent.parent / "utils"
file_ops_path = utils_dir / "file_operations.py"
file_ops_spec = importlib.util.spec_from_file_location("file_operations", file_ops_path)
file_operations = importlib.util.module_from_spec(file_ops_spec)
file_ops_spec.loader.exec_module(file_operations)

list_files = file_operations.list_files

def get_branches(repo_path):
    """Get list of branches in the repository"""
    try:
        if os.path.exists(os.path.join(repo_path, ".git")):
            repo = Repo(repo_path)
            branches = []
            for ref in repo.references:
                if ref.name.startswith("origin/"):
                    branch_name = ref.name.split("origin/")[1]
                    branches.append(branch_name)
                elif not ref.name.startswith("HEAD"):
                    branches.append(ref.name)
            
            # Remove duplicates and sort
            branches = sorted(list(set(branches)))
            return branches
        return ["main"]  # Default branch
    except Exception as e:
        print(f"Error getting branches: {str(e)}")
        return ["main"]  # Default branch if error

def render_sidebar(repo_path, github_repo, github_user, on_config_change=None):
    """
    Render the sidebar with repository information and configuration options
    
    Args:
        repo_path (str): Current repository path
        github_repo (str): Current GitHub repository
        github_user (str): Current GitHub user
        on_config_change (function): Callback function when configuration is changed
    """
    st.sidebar.title("Developer Assistant")
    st.sidebar.markdown("---")
    
    with st.sidebar.expander("Repository Configuration", expanded=False):
        # Repository configuration form
        with st.form("repo_config_form"):
            # Repository path input with validation
            new_repo_path = st.text_input(
                "Local Repository Path", 
                value=repo_path,
                help="Path where the repository will be cloned locally"
            )
            
            # GitHub repository input
            new_github_repo = st.text_input(
                "GitHub Repository", 
                value=github_repo,
                help="Format: username/repository"
            )
            
            # GitHub user input
            new_github_user = st.text_input(
                "GitHub Username", 
                value=github_user
            )
            
            # Branch selection
            branches = get_branches(repo_path)
            branch = st.selectbox(
                "Branch", 
                options=branches,
                index=0 if "main" not in branches else branches.index("main"),
                help="Select branch to work with"
            )
            
            # Submit button for the form
            submitted = st.form_submit_button("Update Configuration")
            
            if submitted and callable(on_config_change):
                # Check if something changed
                if (new_repo_path != repo_path or 
                    new_github_repo != github_repo or 
                    new_github_user != github_user):
                    
                    # Call the callback function
                    on_config_change(new_repo_path, new_github_repo, new_github_user, branch)
    
    # Repository info display (current values)
    st.sidebar.markdown("### Repository Info")
    st.sidebar.info(f"Repository: {github_repo}")
    st.sidebar.info(f"Local path: {repo_path}")
    
    # Get current branch
    if "branch" in st.session_state:
        st.sidebar.info(f"Branch: {st.session_state.branch}")
    
    # Return the current configuration values
    return {
        "repo_path": repo_path,
        "github_repo": github_repo,
        "github_user": github_user
    }