import streamlit as st
from langchain.agents import initialize_agent, AgentType, Tool
from langchain_openai import OpenAI
import importlib.util
import pathlib

# Dynamic import for utils modules
current_dir = pathlib.Path(__file__).parent
utils_dir = current_dir.parent / "utils"

git_ops_path = utils_dir / "git_operations.py"
git_ops_spec = importlib.util.spec_from_file_location("git_operations", git_ops_path)
git_operations = importlib.util.module_from_spec(git_ops_spec)
git_ops_spec.loader.exec_module(git_operations)

wrappers_path = utils_dir / "wrappers.py"
wrappers_spec = importlib.util.spec_from_file_location("wrappers", wrappers_path)
wrappers = importlib.util.module_from_spec(wrappers_spec)
wrappers_spec.loader.exec_module(wrappers)

# Import specific functions
clone_repo = git_operations.clone_repo
modify_code_wrapper = wrappers.modify_code_wrapper
delete_file_wrapper = wrappers.delete_file_wrapper
list_files_wrapper = wrappers.list_files_wrapper
read_file_wrapper = wrappers.read_file_wrapper
commit_and_push_wrapper = wrappers.commit_and_push_wrapper
create_branch_wrapper = wrappers.create_branch_wrapper
get_repo_status_wrapper = wrappers.get_repo_status_wrapper
generate_diff_wrapper = wrappers.generate_diff_wrapper
stash_changes_wrapper = wrappers.stash_changes_wrapper
create_pull_request_wrapper = wrappers.create_pull_request_wrapper
run_command_wrapper = wrappers.run_command_wrapper
run_tests_wrapper = wrappers.run_tests_wrapper
search_code_wrapper = wrappers.search_code_wrapper
install_dependencies_wrapper = wrappers.install_dependencies_wrapper
analyze_code_wrapper = wrappers.analyze_code_wrapper
lint_code_wrapper = wrappers.lint_code_wrapper

def initialize_agent_tools(repo_path, github_token, github_repo, github_user, openai_api_key, branch="main"):
    """Initialize the agent and tools."""
    # Ensure the repository is cloned before running operations
    with st.spinner("Initializing repository..."):
        clone_status = clone_repo(repo_path, github_token, github_repo, github_user, branch)
        st.success(f"Repository status: {clone_status}")
    
    # Define tools for the agent - using our simple wrappers
    tools = [
        # File operations
        Tool(
            name="ModifyCode",
            func=lambda inputs: modify_code_wrapper(inputs, repo_path),
            description="Creates or modifies a file in the repository. Inputs: file_path (str), new_content (str).",
        ),
        Tool(
            name="DeleteFile",
            func=lambda inputs: delete_file_wrapper(inputs, repo_path),
            description="Deletes a file from the repository. Input: file_path (str).",
        ),
        Tool(
            name="ListFiles",
            func=lambda inputs: list_files_wrapper(inputs, repo_path),
            description="Lists files in the repository or a specific directory. Input (optional): directory_path (str).",
        ),
        Tool(
            name="ReadFile",
            func=lambda inputs: read_file_wrapper(inputs, repo_path),
            description="Reads the content of a file. Input: file_path (str).",
        ),
        
        # Git operations
        Tool(
            name="CommitAndPush",
            func=lambda inputs: commit_and_push_wrapper(inputs, repo_path, github_token, github_repo, github_user),
            description="Commits and pushes changes to GitHub. Inputs: file_path (str), commit_message (str, optional).",
        ),
        Tool(
            name="CreateBranch",
            func=lambda inputs: create_branch_wrapper(inputs, repo_path),
            description="Creates a new branch and switches to it. Input: branch_name (str).",
        ),
        Tool(
            name="GetRepoStatus",
            func=lambda inputs: get_repo_status_wrapper(inputs, repo_path),
            description="Gets the status of the repository including current branch, changes, and last commit.",
        ),
        Tool(
            name="GenerateDiff",
            func=lambda inputs: generate_diff_wrapper(inputs, repo_path),
            description="Generates a diff for current changes. Input (optional): file_path (str) to limit diff to a specific file.",
        ),
        Tool(
            name="StashChanges",
            func=lambda inputs: stash_changes_wrapper(inputs, repo_path),
            description="Stashes or pops stashed changes. Inputs: pop (bool, default=false), message (str, optional).",
        ),
        Tool(
            name="CreatePullRequest",
            func=lambda inputs: create_pull_request_wrapper(inputs, repo_path, github_token, github_repo),
            description="Creates a pull request. Inputs: branch (str), title (str, optional), description (str, optional).",
        ),
        
        # Development operations
        Tool(
            name="RunCommand",
            func=lambda inputs: run_command_wrapper(inputs, repo_path),
            description="Runs a shell command in the repository. Input: command (str), timeout (int, optional, default=60).",
        ),
        Tool(
            name="SearchCode",
            func=lambda inputs: search_code_wrapper(inputs, repo_path),
            description="Searches for code matching a query. Inputs: query (str), file_pattern (str, optional, default='*').",
        ),
        Tool(
            name="RunTests",
            func=lambda inputs: run_tests_wrapper(inputs, repo_path),
            description="Runs tests in the repository. Input (optional): test_path (str) to specify which tests to run.",
        ),
        Tool(
            name="InstallDependencies",
            func=lambda inputs: install_dependencies_wrapper(inputs, repo_path),
            description="Installs dependencies from a requirements file. Input (optional): requirements_file (str, default='requirements.txt').",
        ),
        Tool(
            name="AnalyzeCode",
            func=lambda inputs: analyze_code_wrapper(inputs, repo_path),
            description="Analyzes code for issues and complexity. Input: file_path (str).",
        ),
        Tool(
            name="LintCode",
            func=lambda inputs: lint_code_wrapper(inputs, repo_path),
            description="Runs linting across the repository or a specific path. Input (optional): path (str).",
        )
    ]
    
    # Initialize LangChain LLM with a smaller token limit
    llm = OpenAI(
        model="gpt-3.5-turbo-instruct", 
        temperature=0,
        max_tokens=1000,  # Limit output tokens
        api_key=openai_api_key
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