import os
import sys
from git import Repo, GitCommandError
from github import Github
import importlib.util
import pathlib

def clone_repo(local_path, github_token, github_repo, github_user, branch="main"):
    """Clones a GitHub repository locally using authentication."""
    try:
        print(f"Attempting to clone/update repository to {local_path}")
        
        # Construct the authenticated repository URL
        github_repo_url = f"https://{github_user}:{github_token}@github.com/{github_repo}.git"
        print(f"Using repo URL: {github_repo_url.replace(github_token, '***')}")
        
        if not os.path.exists(local_path):
            print(f"Creating directory {local_path}")
            os.makedirs(local_path, exist_ok=True)
            print(f"Cloning {github_repo} into {local_path}...")
            
            # Clone the repository
            repo = Repo.clone_from(github_repo_url, local_path)
            
            # Switch to the specified branch if not main
            if branch != "main" and branch != "master":
                try:
                    print(f"Switching to branch {branch}")
                    # Check if branch exists
                    for remote_ref in repo.remote().refs:
                        if remote_ref.name == f"origin/{branch}":
                            # Create tracking branch
                            repo.git.checkout(branch, b=True)
                            break
                    else:
                        # If branch wasn't found but no error was raised
                        print(f"Branch {branch} not found. Staying on default branch.")
                except Exception as e:
                    print(f"Error switching branch: {str(e)}")
            
            return f"Repository cloned to {local_path} on branch {branch}"
        elif os.path.exists(os.path.join(local_path, ".git")):
            print(f"Repository already exists at {local_path}, pulling latest changes")
            repo_local = Repo(local_path)
            
            # Switch branch if needed
            try:
                current_branch = repo_local.active_branch.name
                if current_branch != branch:
                    print(f"Switching from branch {current_branch} to {branch}")
                    # Check if branch exists locally
                    branch_exists = branch in [b.name for b in repo_local.branches]
                    
                    if branch_exists:
                        # Switch to existing branch
                        repo_local.git.checkout(branch)
                    else:
                        # Try to find it in remotes
                        for remote_ref in repo_local.remote().refs:
                            if remote_ref.name == f"origin/{branch}":
                                # Create tracking branch
                                repo_local.git.checkout(branch, b=True)
                                break
                        else:
                            print(f"Branch {branch} not found. Staying on {current_branch}.")
            except Exception as e:
                print(f"Error switching branch: {str(e)}")
            
            # Pull latest changes
            repo_local.git.pull()
            current_branch = repo_local.active_branch.name
            return f"Repository already exists locally. Pulled latest changes on branch {current_branch}."
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
                repo = Repo.clone_from(github_repo_url, local_path)
                
                # Switch to the specified branch if not main
                if branch != "main" and branch != "master":
                    try:
                        print(f"Switching to branch {branch}")
                        # Check if branch exists
                        for remote_ref in repo.remote().refs:
                            if remote_ref.name == f"origin/{branch}":
                                # Create tracking branch
                                repo.git.checkout(branch, b=True)
                                break
                        else:
                            # If branch wasn't found but no error was raised
                            print(f"Branch {branch} not found. Staying on default branch.")
                    except Exception as e:
                        print(f"Error switching branch: {str(e)}")
                
                return f"Repository initialized and cloned to {local_path} on branch {branch}"
            except Exception as e:
                return f"Error initializing repository: {str(e)}"
    except Exception as e:
        return f"Error cloning repository: {str(e)}"

def commit_and_push(file_path, commit_message, repo_path, github_token, github_repo, github_user):
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
            github_repo_url = f"https://{github_user}:{github_token}@github.com/{github_repo}.git"
            origin = repo_local.remote(name="origin")
            origin.set_url(github_repo_url)
            origin.push()
            
            return f"Changes pushed: {commit_message}"
        except GitCommandError as e:
            return f"Git error: {e}"
    except Exception as e:
        return f"Error in commit_and_push: {str(e)}"