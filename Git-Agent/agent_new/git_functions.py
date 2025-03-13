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
    try:
        print(f"Attempting to clone/update repository to {local_path}")
        print(f"Using repo URL: {GITHUB_REPO_URL.replace(GITHUB_TOKEN, '***')}")
        
        if not os.path.exists(local_path):
            print(f"Creating directory {local_path}")
            os.makedirs(local_path, exist_ok=True)
            print(f"Cloning {GITHUB_REPO} into {local_path}...")
            Repo.clone_from(GITHUB_REPO_URL, local_path)
            return f"Repository cloned to {local_path}"
        elif os.path.exists(os.path.join(local_path, ".git")):
            print(f"Repository already exists at {local_path}, pulling latest changes")
            repo_local = Repo(local_path)
            repo_local.git.pull()
            return f"Repository already exists locally. Pulled latest changes."
        else:
            print(f"Directory {local_path} exists but is not a git repository. Initializing...")
            # If the directory exists but is not a git repo, initialize it
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
                Repo.clone_from(GITHUB_REPO_URL, local_path)
                return f"Repository initialized and cloned to {local_path}"
            except Exception as e:
                return f"Error initializing repository: {str(e)}"
    except Exception as e:
        return f"Error cloning repository: {str(e)}"


def list_branches(local_path):
    """Lists all branches in the local repo."""
    try:
        repo_local = Repo(local_path)
        return [branch.name for branch in repo_local.branches]
    except Exception as e:
        return f"Error listing branches: {str(e)}"


def modify_code(file_path: str, new_content: str, local_path: str):
    """Modifies a file in the local repository or creates it if missing."""
    try:
        # Ensure file_path doesn't contain the local_path already
        if local_path in file_path:
            file_full_path = file_path
        else:
            file_full_path = os.path.join(local_path, file_path)

        print(f"Writing to file: {file_full_path}")
        
        # Ensure directory exists
        dir_path = os.path.dirname(file_full_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        # Write new content (create file if it doesn't exist)
        with open(file_full_path, "w") as file:
            file.write(new_content)

        return f"File {file_path} has been modified/created."
    except Exception as e:
        return f"Error modifying file: {str(e)}"


def commit_and_push(file_path, commit_message, local_path):
    """Commits changes and pushes to GitHub using authentication."""
    try:
        print(f"Attempting to commit and push from {local_path}")
        
        # Ensure the repo exists and is valid
        if not os.path.exists(os.path.join(local_path, ".git")):
            return f"Error: {local_path} is not a git repository"
        
        # Normalize file path
        if local_path in file_path:
            relative_path = os.path.relpath(file_path, local_path)
        else:
            relative_path = file_path
            
        print(f"Using relative path for git: {relative_path}")
        
        repo_local = Repo(local_path)
        repo_local.git.add(relative_path)
        repo_local.index.commit(commit_message)
        
        # Push using token authentication
        origin = repo_local.remote(name="origin")
        current_url = origin.url
        print(f"Current remote URL: {current_url.replace(GITHUB_TOKEN if GITHUB_TOKEN in current_url else '', '***')}")
        
        # Set the URL with credentials if needed
        if GITHUB_TOKEN not in current_url:
            print("Setting remote URL with authentication")
            origin.set_url(GITHUB_REPO_URL)
        
        print("Pushing changes...")
        push_info = origin.push()
        print(f"Push result: {push_info}")
        
        return f"Changes pushed: {commit_message}"
    except GitCommandError as e:
        return f"Git error: {e}"
    except Exception as e:
        return f"Error in commit_and_push: {str(e)}"


def create_pull_request(branch_name="feature-branch", title="Update Code", body="Automated update"):
    """Creates a pull request on GitHub."""
    try:
        base_branch = repo.default_branch  # e.g., "main"
        pr = repo.create_pull(title=title, body=body, base=base_branch, head=branch_name)
        return f"Pull Request created: {pr.html_url}"
    except Exception as e:
        return f"Error creating pull request: {str(e)}"


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


### WRAPPER FUNCTIONS FOR LANGCHAIN TOOLS ###
def modify_code_wrapper(inputs, local_path="local_repo"):
    # If we get a string, attempt to parse it into a dictionary.
    if isinstance(inputs, str):
        try:
            inputs = parse_tool_input(inputs)
        except Exception as e:
            return f"Error parsing input string: {str(e)}"

    file_path = inputs.get("file_path", "")
    new_content = inputs.get("new_content", "")
    
    if not file_path or not new_content:
        return "Error: Missing file_path or new_content."
    
    return modify_code(file_path, new_content, local_path)


def commit_and_push_wrapper(inputs, local_path="local_repo"):
    # If we get a string, attempt to parse it into a dictionary.
    if isinstance(inputs, str):
        try:
            inputs = parse_tool_input(inputs)
        except Exception as e:
            return f"Error parsing input string: {str(e)}"

    file_path = inputs.get("file_path", "")
    commit_message = inputs.get("commit_message", "Update code")
    
    if not file_path:
        return "Error: Missing file_path."
    
    return commit_and_push(file_path, commit_message, local_path)


def create_pull_request_wrapper(inputs):
    # If we get a string, attempt to parse it into a dictionary.
    if isinstance(inputs, str):
        try:
            inputs = parse_tool_input(inputs)
        except Exception as e:
            return f"Error parsing input string: {str(e)}"

    branch_name = inputs.get("branch_name", "feature-branch")
    title = inputs.get("title", "Update Code")
    body = inputs.get("body", "Automated update")
    
    return create_pull_request(branch_name, title, body)