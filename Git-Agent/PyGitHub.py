from github import Github
import os
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("No GITHUB_TOKEN variable")

repo_name = "rsalvagio92/Wild-Nomad"


# Authenticate (replace with your token)
g = Github(GITHUB_TOKEN)

# Get a repository
def get_repo(repo_name):
    return g.get_repo(repo_name)

# List all repositories of the authenticated user
def list_repos():
    return [repo.full_name for repo in g.get_user().get_repos()]

# Create a new repository
def create_repo(repo_name, private=True):
    user = g.get_user()
    return user.create_repo(name=repo_name, private=private)

# Get all branches of a repository
def list_repo_branches(repo_name):
    repo = get_repo(repo_name)
    return [branch.name for branch in repo.get_branches()]

# Create an issue
def create_issue(repo_name, title="Issue title", body="Issue body"):
    repo = get_repo(repo_name)
    return repo.create_issue(title=title, body=body)

# List issues
def list_issues(repo_name):
    repo = get_repo(repo_name)
    return [(issue.number, issue.title) for issue in repo.get_issues()]

# Get the latest commit of a branch
def get_latest_commit(repo_name, branch="main"):
    repo = get_repo(repo_name)
    return repo.get_branch(branch).commit.sha

# Create a pull request
def create_pull_request(repo_name, base="main", head="feature-branch", title="New PR", body="Description"):
    repo = get_repo(repo_name)
    return repo.create_pull(title=title, body=body, base=base, head=head)

# Merge a pull request
def merge_pull_request(repo_name, pr_number):
    repo = get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    return pr.merge()

# Delete a repository
def delete_repo(repo_name):
    repo = get_repo(repo_name)
    repo.delete()

branches=list_repo_branches(repo_name)
print("Branches:", branches)