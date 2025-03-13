import os
import re
from git import Repo, GitCommandError
from github import Github
from dotenv import load_dotenv
import subprocess

# Load .env file
load_dotenv()

# GitHub Authentication
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_USER = os.getenv("GITHUB_USER")
local_path = "C:\\Users\\r.salvagio\\OneDrive - Reply\\Desktop\\Experiments\\Wild-Nomads"


if not GITHUB_TOKEN or not GITHUB_REPO or not GITHUB_USER:
    raise ValueError("GitHub token, user, or repository not set in environment variables.")

# Construct the authenticated repository URL
GITHUB_REPO_URL = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git"

# Initialize GitHub API client
github_client = Github(GITHUB_TOKEN)
repo = github_client.get_repo(GITHUB_REPO)


### LOCAL GIT FUNCTIONS ###
def clone_repo(local_path):
    """Clones a GitHub repository locally using authentication."""
    if not os.path.exists(local_path):
        print(f"Cloning {GITHUB_REPO_URL} into {local_path}...")
        Repo.clone_from(GITHUB_REPO_URL, local_path)
        return f"Repository cloned to {local_path}"
    return "Repository already exists locally."


def list_branches(local_path):
    """Lists all branches in the local repo."""
    repo_local = Repo(local_path)
    return [branch.name for branch in repo_local.branches]


def modify_code(file_path: str, new_content: str, local_path):
    """Modifies a file in the local repository or creates it if missing, then commits and pushes changes."""
    file_full_path = os.path.join(local_path, file_path)

    # Ensure directory exists
    os.makedirs(os.path.dirname(file_full_path), exist_ok=True)

    # Write new content (create file if it doesn't exist)
    with open(file_full_path, "w") as file:
        file.write(new_content)

    return commit_and_push(file_path, f"Updated {file_path}", local_path)


def commit_and_push(file_path, commit_message, local_path):
    """Commits changes and pushes to GitHub using authentication."""
    try:
        repo_local = Repo(local_path)
        repo_local.git.add(file_path)
        repo_local.index.commit(commit_message)
        
        # Push using token authentication
        origin = repo_local.remote(name="origin")
        origin.set_url(GITHUB_REPO_URL)  # Ensure we're using the correct URL
        origin.push()
        
        return f"Changes pushed: {commit_message}"
    except GitCommandError as e:
        return f"Git error: {e}"


def create_pull_request(branch_name="feature-branch", title="Update Code", body="Automated update"):
    """Creates a pull request on GitHub."""
    base_branch = repo.default_branch  # e.g., "main"
    pr = repo.create_pull(title=title, body=body, base=base_branch, head=branch_name)
    return f"Pull Request created: {pr.html_url}"


### HELPER FUNCTION TO PARSE STRING INPUT ###
def parse_tool_input(input_str: str) -> dict:
    """
    Parses a string like:
      "file_path = 'app.py', new_content = 'print(\"Hello AI\")', local_path = None"
    into a dictionary.
    """
    result = {}
    # Split the string on commas that are not inside quotes
    parts = re.split(r",\s*(?=(?:[^'\"]|'[^']*'|\"[^\"]*\")*$)", input_str)
    for part in parts:
        if "=" in part:
            key, value = part.split("=", 1)
            key = key.strip()
            value = value.strip()
            # Remove quotes if present
            if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
                value = value[1:-1]
            elif value.lower() == "none":
                value = None
            result[key] = value
    return result


### WRAPPER FUNCTION FOR LANGCHAIN TOOL ###
def modify_code_wrapper(inputs):
    # If we get a string, attempt to parse it into a dictionary.
    if isinstance(inputs, str):
        try:
            inputs = parse_tool_input(inputs)
        except Exception as e:
            return f"Error parsing input string: {str(e)}"

    file_path = inputs.get("file_path", "")
    new_content = inputs.get("new_content", "")
    local_path = inputs.get("local_path", "local_repo")
    if not local_path:
        local_path = "local_repo"
    
    if not file_path or not new_content:
        return "Error: Missing file_path or new_content."
    
    return modify_code(file_path, new_content, local_path)
