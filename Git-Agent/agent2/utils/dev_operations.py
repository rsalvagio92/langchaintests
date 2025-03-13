import os
import sys
import subprocess
import pathlib
import json
from git import Repo, GitCommandError

def run_command(command, repo_path, timeout=60):
    """
    Run a shell command in the repository directory
    
    Args:
        command (str or list): Command to run
        repo_path (str): Path to the repository
        timeout (int): Maximum time to wait for command to complete
        
    Returns:
        dict: Result of the command with stdout, stderr, and return code
    """
    try:
        # Ensure the command is a list
        if isinstance(command, str):
            command = command.split()
        
        # Run the command in the repository directory
        result = subprocess.run(
            command, 
            cwd=repo_path, 
            capture_output=True, 
            text=True,
            timeout=timeout
        )
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "returncode": -1,
            "success": False
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": f"Error executing command: {str(e)}",
            "returncode": -1,
            "success": False
        }

def create_branch(branch_name, repo_path):
    """
    Create a new branch
    
    Args:
        branch_name (str): Name of the branch to create
        repo_path (str): Path to the repository
        
    Returns:
        str: Result message
    """
    try:
        repo = Repo(repo_path)
        
        # Check if branch already exists
        if branch_name in [b.name for b in repo.branches]:
            return f"Branch '{branch_name}' already exists"
        
        # Create a new branch from current HEAD
        repo.git.checkout('-b', branch_name)
        return f"Created new branch '{branch_name}' and switched to it"
    except Exception as e:
        return f"Error creating branch: {str(e)}"

def search_code(query, repo_path, file_pattern="*"):
    """
    Search for code matching the query in the repository
    
    Args:
        query (str): Search query
        repo_path (str): Path to the repository
        file_pattern (str): File pattern to search in (e.g., "*.py")
        
    Returns:
        dict: Search results with matched files and lines
    """
    try:
        # Use grep for searching
        command = ['grep', '-r', '--include', file_pattern, '-n', query, '.']
        result = run_command(command, repo_path)
        
        if not result["success"]:
            if "No such file or directory" in result["stderr"]:
                return f"No files matching pattern '{file_pattern}' found"
            else:
                return f"Error searching code: {result['stderr']}"
        
        # No results
        if not result["stdout"].strip():
            return f"No matches found for '{query}'"
        
        # Process results
        matches = []
        for line in result["stdout"].splitlines():
            parts = line.split(':', 2)
            if len(parts) >= 3:
                file_path, line_num, matched_text = parts
                matches.append({
                    "file": file_path,
                    "line": line_num,
                    "text": matched_text.strip()
                })
                
        return {
            "query": query,
            "matches": matches,
            "count": len(matches)
        }
    except Exception as e:
        return f"Error searching code: {str(e)}"

def run_tests(test_path, repo_path):
    """
    Run tests in the repository
    
    Args:
        test_path (str): Path to tests to run (relative to repo root)
        repo_path (str): Path to the repository
        
    Returns:
        str: Test results
    """
    try:
        # Check if pytest is available
        try_pytest = run_command(["pytest", "--version"], repo_path)
        
        if try_pytest["success"]:
            # Run tests with pytest
            if test_path:
                command = ["pytest", test_path, "-v"]
            else:
                command = ["pytest", "-v"]
        else:
            # Try with unittest
            if test_path:
                if test_path.endswith(".py"):
                    command = ["python", "-m", "unittest", test_path]
                else:
                    command = ["python", "-m", "unittest", "discover", test_path]
            else:
                command = ["python", "-m", "unittest", "discover"]
        
        result = run_command(command, repo_path, timeout=120)
        
        if result["success"]:
            return f"Tests passed:\n{result['stdout']}"
        else:
            return f"Tests failed:\n{result['stdout']}\n{result['stderr']}"
    except Exception as e:
        return f"Error running tests: {str(e)}"

def install_dependencies(requirements_file, repo_path):
    """
    Install dependencies from requirements.txt
    
    Args:
        requirements_file (str): Path to requirements file (relative to repo root)
        repo_path (str): Path to the repository
        
    Returns:
        str: Installation results
    """
    try:
        # Check if requirements file exists
        full_path = os.path.join(repo_path, requirements_file)
        if not os.path.exists(full_path):
            return f"Requirements file '{requirements_file}' not found"
        
        # Install requirements
        command = ["pip", "install", "-r", requirements_file]
        result = run_command(command, repo_path, timeout=300)
        
        if result["success"]:
            return f"Dependencies installed successfully:\n{result['stdout']}"
        else:
            return f"Error installing dependencies:\n{result['stderr']}"
    except Exception as e:
        return f"Error installing dependencies: {str(e)}"

def analyze_code(file_path, repo_path):
    """
    Analyze code for issues and complexity
    
    Args:
        file_path (str): Path to file to analyze (relative to repo root)
        repo_path (str): Path to the repository
        
    Returns:
        dict: Analysis results
    """
    try:
        # Check if file exists
        full_path = os.path.join(repo_path, file_path)
        if not os.path.exists(full_path):
            return f"File '{file_path}' not found"
        
        results = {}
        
        # Try pylint
        pylint_result = run_command(["pylint", file_path, "--output-format=json"], repo_path)
        if pylint_result["success"] or pylint_result["returncode"] > 0 and pylint_result["stdout"]:
            try:
                pylint_data = json.loads(pylint_result["stdout"])
                results["pylint"] = {
                    "issues": pylint_data,
                    "count": len(pylint_data)
                }
            except json.JSONDecodeError:
                results["pylint"] = {
                    "raw": pylint_result["stdout"],
                    "error": "Could not parse pylint output"
                }
        
        # Try flake8
        flake8_result = run_command(["flake8", file_path], repo_path)
        if flake8_result["returncode"] >= 0:
            results["flake8"] = {
                "output": flake8_result["stdout"],
                "issues": len(flake8_result["stdout"].splitlines()) if flake8_result["stdout"] else 0
            }
        
        return results
    except Exception as e:
        return f"Error analyzing code: {str(e)}"

def create_pull_request(branch, title, description, repo_path, github_token, github_repo):
    """
    Create a pull request
    
    Args:
        branch (str): Branch to create PR from
        title (str): PR title
        description (str): PR description
        repo_path (str): Path to the repository
        github_token (str): GitHub token
        github_repo (str): GitHub repository (owner/repo)
        
    Returns:
        str: Result of the PR creation
    """
    try:
        # Ensure branch exists
        repo = Repo(repo_path)
        branches = [b.name for b in repo.branches]
        
        if branch not in branches:
            return f"Branch '{branch}' does not exist"
        
        # Determine default branch (typically main or master)
        default_branch = "main"
        for candidate in ["main", "master"]:
            if candidate in branches:
                default_branch = candidate
                break
        
        # Create PR using GitHub CLI if available
        gh_result = run_command(["gh", "--version"], repo_path)
        
        if gh_result["success"]:
            # Set GitHub token for gh command
            env = os.environ.copy()
            env["GITHUB_TOKEN"] = github_token
            
            # Create the PR
            command = [
                "gh", "pr", "create",
                "--base", default_branch,
                "--head", branch,
                "--title", title,
                "--body", description
            ]
            
            result = subprocess.run(
                command, 
                cwd=repo_path, 
                capture_output=True, 
                text=True,
                env=env
            )
            
            if result.returncode == 0:
                return f"Pull request created successfully:\n{result.stdout}"
            else:
                return f"Error creating pull request:\n{result.stderr}"
        else:
            # Use API directly
            return f"GitHub CLI not available. Please install GitHub CLI (gh) or implement API-based PR creation."
    except Exception as e:
        return f"Error creating pull request: {str(e)}"

def lint_code(repo_path, path=None):
    """
    Run linting across the repository or a specific path
    
    Args:
        repo_path (str): Path to the repository
        path (str): Path to lint (relative to repo root, None for entire repo)
        
    Returns:
        str: Linting results
    """
    try:
        commands = []
        results = {}
        
        # Path to lint (default to repo root)
        target = path or "."
        
        # Try flake8
        flake8_result = run_command(["flake8", target], repo_path)
        if flake8_result["returncode"] >= 0:  # flake8 returns non-zero if issues found
            results["flake8"] = {
                "output": flake8_result["stdout"],
                "issues": len(flake8_result["stdout"].splitlines()) if flake8_result["stdout"] else 0
            }
        
        # Try pylint
        pylint_target = target
        if target == ".":
            # For the whole repo, find all Python files
            py_files_result = run_command(["find", ".", "-name", "*.py", "-not", "-path", "*/\.*"], repo_path)
            if py_files_result["success"] and py_files_result["stdout"]:
                pylint_target = py_files_result["stdout"].splitlines()
            else:
                pylint_target = []
        
        if pylint_target:
            if isinstance(pylint_target, list):
                pylint_result = run_command(["pylint"] + pylint_target, repo_path)
            else:
                pylint_result = run_command(["pylint", pylint_target], repo_path)
                
            if pylint_result["returncode"] >= 0:
                results["pylint"] = {
                    "output": pylint_result["stdout"],
                    "error": pylint_result["stderr"] if pylint_result["stderr"] else None
                }
        
        return results
    except Exception as e:
        return f"Error running linting: {str(e)}"

def stash_changes(repo_path, pop=False, message=None):
    """
    Stash or pop stashed changes
    
    Args:
        repo_path (str): Path to the repository
        pop (bool): Whether to pop the stash
        message (str): Stash message
        
    Returns:
        str: Result message
    """
    try:
        repo = Repo(repo_path)
        
        if pop:
            result = repo.git.stash("pop")
            return f"Popped stashed changes:\n{result}"
        else:
            command = ["stash", "push"]
            if message:
                command.extend(["-m", message])
            
            result = repo.git.execute(command)
            if "No local changes to save" in result:
                return "No changes to stash"
            else:
                return f"Stashed changes:\n{result}"
    except Exception as e:
        return f"Error with stash operation: {str(e)}"

def get_repo_status(repo_path):
    """
    Get repository status
    
    Args:
        repo_path (str): Path to the repository
        
    Returns:
        dict: Repository status information
    """
    try:
        repo = Repo(repo_path)
        
        # Get current branch
        try:
            current_branch = repo.active_branch.name
        except Exception:
            current_branch = "DETACHED_HEAD"
        
        # Get list of branches
        branches = [b.name for b in repo.branches]
        
        # Get status (modified, added, deleted files)
        status = repo.git.status("--porcelain")
        status_list = []
        
        for line in status.splitlines():
            if line:
                status_code = line[:2].strip()
                file_path = line[3:].strip()
                status_type = ""
                
                if status_code == "M":
                    status_type = "modified"
                elif status_code == "A":
                    status_type = "added"
                elif status_code == "D":
                    status_type = "deleted"
                elif status_code == "??":
                    status_type = "untracked"
                elif status_code == "R":
                    status_type = "renamed"
                else:
                    status_type = status_code
                
                status_list.append({
                    "type": status_type,
                    "path": file_path
                })
        
        # Get last commit info
        last_commit = None
        if repo.heads:
            last_commit = {
                "hash": repo.head.commit.hexsha[:7],
                "message": repo.head.commit.message.strip(),
                "author": repo.head.commit.author.name,
                "date": repo.head.commit.authored_datetime.strftime("%Y-%m-%d %H:%M:%S")
            }
        
        return {
            "current_branch": current_branch,
            "branches": branches,
            "status": status_list,
            "last_commit": last_commit,
            "has_changes": len(status_list) > 0
        }
    except Exception as e:
        return f"Error getting repository status: {str(e)}"

def generate_diff(repo_path, file_path=None):
    """
    Generate diff for the current changes
    
    Args:
        repo_path (str): Path to the repository
        file_path (str): Path to specific file to get diff for
        
    Returns:
        str: Diff output
    """
    try:
        repo = Repo(repo_path)
        
        if file_path:
            if not os.path.exists(os.path.join(repo_path, file_path)):
                return f"File '{file_path}' not found"
            
            diff = repo.git.diff(file_path)
        else:
            # Get diff for all changes
            diff = repo.git.diff()
        
        if not diff:
            if file_path:
                # Check if the file is untracked
                untracked = repo.untracked_files
                if file_path in untracked:
                    return f"File '{file_path}' is untracked. Use 'git add {file_path}' to stage it."
                
                # Check if it's staged
                staged_diff = repo.git.diff("--staged", file_path)
                if staged_diff:
                    return f"File '{file_path}' has staged changes:\n{staged_diff}"
                
                return f"No changes in '{file_path}'"
            else:
                # Check for staged changes
                staged_diff = repo.git.diff("--staged")
                if staged_diff:
                    return f"There are staged changes:\n{staged_diff}"
                
                return "No changes in the repository"
        
        return diff
    except Exception as e:
        return f"Error generating diff: {str(e)}"