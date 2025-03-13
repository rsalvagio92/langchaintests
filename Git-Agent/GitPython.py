from git import Repo
import os
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("No GITHUB_TOKEN variable")

REPO_NAME = "rsalvagio92/Wild-Nomad"


# Initialize a new repo or open an existing one
def init_repo(path="."):
    return Repo.init(path)

# Clone a remote repository
def clone_repo(url, local_path):
    return Repo.clone_from(url, local_path)

# Get the current branch
def get_current_branch(repo_path="."):
    repo = Repo(repo_path)
    return repo.active_branch.name

# List all branches
def list_branches(repo_path="."):
    repo = Repo(repo_path)
    return [branch.name for branch in repo.branches]

# Add files to staging
def add_files(repo_path=".", files=["."]):
    repo = Repo(repo_path)
    repo.index.add(files)
    repo.index.write()

# Commit changes
def commit_changes(repo_path=".", message="Update"):
    repo = Repo(repo_path)
    repo.index.commit(message)

# Push changes
def push_changes(repo_path=".", remote_name="origin", branch="main"):
    repo = Repo(repo_path)
    remote = repo.remote(name=remote_name)
    remote.push(branch)

# Pull latest changes
def pull_changes(repo_path=".", remote_name="origin", branch="main"):
    repo = Repo(repo_path)
    remote = repo.remote(name=remote_name)
    remote.pull(branch)

# Create a new branch
def create_branch(repo_path=".", branch_name="new-branch"):
    repo = Repo(repo_path)
    new_branch = repo.create_head(branch_name)
    new_branch.checkout()

# Merge branches
def merge_branches(repo_path=".", source_branch="feature", target_branch="main"):
    repo = Repo(repo_path)
    repo.git.checkout(target_branch)
    repo.git.merge(source_branch)
