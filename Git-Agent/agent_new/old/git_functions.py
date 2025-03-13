#git_functions.py
import os
import re
import glob
import subprocess
from git import Repo, GitCommandError
from github import Github
from dotenv import load_dotenv

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


def create_branch(branch_name, local_path):
    """Creates a new branch in the local repo."""
    try:
        repo_local = Repo(local_path)
        current_branch = repo_local.active_branch.name
        repo_local.git.checkout('-b', branch_name)
        return f"Created and switched to new branch '{branch_name}' from '{current_branch}'"
    except GitCommandError as e:
        return f"Git error creating branch: {e}"
    except Exception as e:
        return f"Error creating branch: {str(e)}"


def checkout_branch(branch_name, local_path):
    """Switches to another branch."""
    try:
        repo_local = Repo(local_path)
        current_branch = repo_local.active_branch.name
        repo_local.git.checkout(branch_name)
        return f"Switched from branch '{current_branch}' to '{branch_name}'"
    except GitCommandError as e:
        return f"Git error switching branch: {e}"
    except Exception as e:
        return f"Error switching branch: {str(e)}"


def pull_changes(local_path):
    """Pulls the latest changes from the remote repository."""
    try:
        repo_local = Repo(local_path)
        repo_local.git.pull()
        return "Successfully pulled latest changes"
    except GitCommandError as e:
        return f"Git error pulling changes: {e}"
    except Exception as e:
        return f"Error pulling changes: {str(e)}"


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

def modify_code_wrapper(inputs, local_path="local_repo"):
    """Wrapper for modify_code function that handles different input formats."""
    print(f"ModifyCode received inputs: {repr(inputs)}")  # Debug line
    
    # If we get a string, attempt to parse it into a dictionary
    if isinstance(inputs, str):
        try:
            # Handle the case where the input might be misformatted
            if '=' not in inputs and '\n' in inputs:
                # Might be a direct content submission without proper formatting
                return "Error: Input must include file_path and new_content parameters."
                
            parsed_inputs = parse_tool_input(inputs)
            print(f"Parsed inputs: {parsed_inputs}")  # Debug line
            
            # Check if parsing worked correctly
            if not parsed_inputs:
                return "Error: Failed to parse input string correctly."
                
            file_path = parsed_inputs.get("file_path")
            new_content = parsed_inputs.get("new_content")
        except Exception as e:
            print(f"Error parsing input: {str(e)}")  # Debug line
            return f"Error parsing input string: {str(e)}"
    else:
        # It's already a dictionary
        file_path = inputs.get("file_path")
        new_content = inputs.get("new_content")
    
    print(f"Extracted file_path: {repr(file_path)}")  # Debug line
    print(f"Extracted new_content: {repr(new_content)}")  # Debug line
    
    # Validate parameters
    if not file_path:
        return "Error: Missing file_path parameter."
    if not new_content:
        return "Error: Missing new_content parameter."
    
    # Call the actual function
    result = modify_code(file_path, new_content, local_path)
    return result

def delete_file(file_path: str, local_path: str):
    """Deletes a file from the local repository."""
    try:
        # Clean up file path - remove quotes
        if file_path and isinstance(file_path, str):
            file_path = file_path.strip()
            if (file_path.startswith('"') and file_path.endswith('"')) or \
               (file_path.startswith("'") and file_path.endswith("'")):
                file_path = file_path[1:-1]
        
        # Ensure file_path doesn't contain the local_path already
        if local_path in file_path:
            file_full_path = file_path
        else:
            file_full_path = os.path.join(local_path, file_path)

        print(f"Attempting to delete file: {file_full_path}")
        
        if not os.path.exists(file_full_path):
            return f"Error: File {file_path} does not exist."
            
        # Delete the file
        os.remove(file_full_path)
        return f"File {file_path} has been deleted."
    except Exception as e:
        return f"Error deleting file: {str(e)}"
    
def delete_file_wrapper(inputs, local_path="local_repo"):
    """Wrapper for delete_file function that handles different input formats."""
    print(f"DeleteFile received inputs: {repr(inputs)}")
    
    # If we get a string, attempt to parse it into a dictionary
    if isinstance(inputs, str):
        # Handle the case where input might just be a file path
        if inputs.strip() and "=" not in inputs:
            file_path = inputs.strip()
            if file_path.startswith('"') and file_path.endswith('"'):
                file_path = file_path[1:-1]
            elif file_path.startswith("'") and file_path.endswith("'"):
                file_path = file_path[1:-1]
        else:
            try:
                parsed_inputs = parse_tool_input(inputs)
                print(f"Parsed inputs: {parsed_inputs}")
                file_path = parsed_inputs.get("file_path")
            except Exception as e:
                print(f"Error parsing input: {str(e)}")
                return f"Error parsing input string: {str(e)}"
    else:
        # It's already a dictionary
        file_path = inputs.get("file_path")
    
    print(f"Final file_path for deletion: {repr(file_path)}")
    
    # Validate parameters
    if not file_path:
        return "Error: Missing file_path parameter."
    
    # Call the actual function
    return delete_file(file_path, local_path)

def read_file(file_path: str, local_path: str):
    """Reads the content of a file."""
    try:
        # Ensure file_path doesn't contain the local_path already
        if local_path in file_path:
            file_full_path = file_path
        else:
            file_full_path = os.path.join(local_path, file_path)

        if not os.path.exists(file_full_path):
            return f"Error: File {file_path} does not exist."

        with open(file_full_path, "r") as file:
            content = file.read()

        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


def list_files(directory_path: str, local_path: str):
    """Lists all files in a specified directory of the repository."""
    try:
        # Clean up directory path - remove quotes
        if directory_path and isinstance(directory_path, str):
            directory_path = directory_path.strip()
            if (directory_path.startswith('"') and directory_path.endswith('"')) or \
               (directory_path.startswith("'") and directory_path.endswith("'")):
                directory_path = directory_path[1:-1]
        
        # If no directory path is specified, use the repository root
        if not directory_path or directory_path.strip() == "":
            dir_full_path = local_path
        # Handle special keywords
        elif directory_path.lower() in [".", "current", "current_directory", "root"]:
            dir_full_path = local_path
        # Ensure directory_path doesn't contain the local_path already
        elif local_path in directory_path:
            dir_full_path = directory_path
        else:
            dir_full_path = os.path.join(local_path, directory_path)
        
        print(f"Listing files in directory: {dir_full_path}")

        if not os.path.exists(dir_full_path):
            # Try to list files at the repo root as a fallback
            print(f"Directory {dir_full_path} does not exist, trying repository root")
            return list_files("", local_path)

        # Get all files recursively
        files = []
        for root, dirs, filenames in os.walk(dir_full_path):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
            
            for filename in filenames:
                rel_path = os.path.relpath(os.path.join(root, filename), local_path)
                files.append(rel_path)

        if not files:
            return f"No files found in {directory_path or 'repository root'}."
            
        return files
    except Exception as e:
        return f"Error listing files: {str(e)}"
    
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


def search_code(search_pattern, local_path):
    """Searches for a pattern in the repository code."""
    try:
        results = []
        for root, dirs, files in os.walk(local_path):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
                
            for filename in files:
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if search_pattern in content:
                            rel_path = os.path.relpath(file_path, local_path)
                            line_number = None
                            for i, line in enumerate(content.split('\n')):
                                if search_pattern in line:
                                    line_number = i + 1
                                    break
                            results.append({
                                'file': rel_path,
                                'line': line_number,
                                'snippet': line.strip() if line_number else None
                            })
                except Exception as e:
                    # Skip files that can't be read as text
                    continue
        
        if not results:
            return f"No matches found for '{search_pattern}'"
        
        return results
    except Exception as e:
        return f"Error searching code: {str(e)}"


def install_dependency(package_name):
    """Installs a Python dependency using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return f"Successfully installed {package_name}"
    except subprocess.CalledProcessError as e:
        return f"Error installing {package_name}: {e}"
    except Exception as e:
        return f"Error: {str(e)}"


def run_tests(test_path, local_path):
    """Runs tests in the repository."""
    try:
        # Default to running all tests if no specific path is provided
        if not test_path:
            # Try to find test directories
            test_dirs = [
                os.path.join(local_path, "tests"),
                os.path.join(local_path, "test")
            ]
            
            for test_dir in test_dirs:
                if os.path.exists(test_dir):
                    test_path = test_dir
                    break
            
            if not test_path:
                return "No test directory found. Please specify a test path."
        
        # Normalize path
        if not local_path in test_path:
            full_test_path = os.path.join(local_path, test_path)
        else:
            full_test_path = test_path
            
        # Check if path exists
        if not os.path.exists(full_test_path):
            return f"Test path {test_path} does not exist."
            
        # Determine how to run tests
        if os.path.isfile(full_test_path) and full_test_path.endswith('.py'):
            # Run single test file
            result = subprocess.run(
                [sys.executable, full_test_path],
                capture_output=True,
                text=True
            )
        else:
            # Try pytest first then unittest as fallback
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", full_test_path],
                    capture_output=True,
                    text=True
                )
            except Exception:
                result = subprocess.run(
                    [sys.executable, "-m", "unittest", "discover", full_test_path],
                    capture_output=True,
                    text=True
                )
                
        # Return test results
        if result.returncode == 0:
            return f"Tests passed!\n\n{result.stdout}"
        else:
            return f"Tests failed with code {result.returncode}.\n\nOutput:\n{result.stdout}\n\nErrors:\n{result.stderr}"
    except Exception as e:
        return f"Error running tests: {str(e)}"


### HELPER FUNCTION TO PARSE STRING INPUT ###
def parse_tool_input(input_str: str) -> dict:
    """
    Parses a string like:
      'file_path = "app.py", new_content = "print(\'Hello AI\')"'
    into a dictionary.
    """
    print(f"Parsing input string: {repr(input_str)}")
    result = {}
    
    # Handle empty input
    if not input_str or input_str.strip() == '':
        return result
    
    # For ModifyCode specifically - most common use case
    if 'file_path' in input_str:
        # Extract file_path
        file_path_match = re.search(r'file_path\s*=\s*[\'"]([^\'"]+)[\'"]', input_str)
        if file_path_match:
            result['file_path'] = file_path_match.group(1)
            print(f"Extracted file_path: {result['file_path']}")
        
        # Check for new_content
        if 'new_content' in input_str:
            # Extract new_content - this is trickier due to potential nested quotes and code
            content_match = re.search(r'new_content\s*=\s*[\'"](.+?)[\'"](?=\s*(?:,|$))', input_str, re.DOTALL)
            if content_match:
                content = content_match.group(1)
                # Unescape any escaped quotes
                content = content.replace("\\'", "'").replace('\\"', '"')
                result['new_content'] = content
                print(f"Extracted new_content: {result['new_content']}")
        
        return result
    
    # General case for other tools
    try:
        # First, handle quoted values with potential commas inside them
        # Replace commas inside quotes temporarily
        processed_str = input_str
        quoted_parts = re.findall(r'[\'"](.+?)[\'"]', processed_str)
        for part in quoted_parts:
            if ',' in part:
                processed_str = processed_str.replace(part, part.replace(',', '##COMMA##'))
        
        # Now split by actual commas
        parts = processed_str.split(',')
        
        # Process each part
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
                    value = value[1:-1]
                    # Restore commas if necessary
                    value = value.replace('##COMMA##', ',')
                elif value.lower() == 'none':
                    value = None
                
                result[key] = value
                print(f"Parsed key-value: {key}={repr(value)}")
    except Exception as e:
        print(f"Error in general parsing: {str(e)}")
    
    return result




### WRAPPER FUNCTIONS FOR LANGCHAIN TOOLS ###
def modify_code_wrapper(inputs, local_path="local_repo"):
    """Wrapper for modify_code function that handles different input formats."""
    print(f"ModifyCode received inputs: {repr(inputs)}")
    
    # If we get a string, attempt to parse it into a dictionary
    if isinstance(inputs, str):
        try:
            parsed_inputs = parse_tool_input(inputs)
            print(f"Parsed inputs: {parsed_inputs}")
            
            file_path = parsed_inputs.get("file_path")
            new_content = parsed_inputs.get("new_content")
        except Exception as e:
            print(f"Error parsing input: {str(e)}")
            return f"Error parsing input string: {str(e)}"
    else:
        # It's already a dictionary
        file_path = inputs.get("file_path")
        new_content = inputs.get("new_content")
    
    print(f"Final file_path: {repr(file_path)}")
    print(f"Final new_content: {repr(new_content)}")
    
    # Validate parameters
    if not file_path:
        return "Error: Missing file_path parameter."
    if new_content is None:  # Allow empty string content
        return "Error: Missing new_content parameter."
    
    # Call the actual function
    return modify_code(file_path, new_content, local_path)

def read_file_wrapper(inputs, local_path="local_repo"):
    # If we get a string, attempt to parse it into a dictionary.
    if isinstance(inputs, str):
        try:
            inputs = parse_tool_input(inputs)
        except Exception as e:
            return f"Error parsing input string: {str(e)}"

    # Handle the case where the input is just a file path string
    if not inputs and isinstance(inputs, str) and inputs.strip() != "":
        file_path = inputs.strip()
    else:
        file_path = inputs.get("file_path", "")
    
    if not file_path:
        return "Error: Missing file_path."
    
    return read_file(file_path, local_path)


def list_files_wrapper(inputs, local_path="local_repo"):
    """Wrapper for list_files function that handles different input formats."""
    print(f"ListFiles received inputs: {repr(inputs)}")
    
    # Empty input or None means list all files in the repo
    if not inputs or (isinstance(inputs, str) and inputs.strip() == ""):
        directory_path = ""
    elif isinstance(inputs, str):
        # If it's just a string without '=', treat it as the directory path
        if "=" not in inputs:
            directory_path = inputs.strip()
            if directory_path.startswith('"') and directory_path.endswith('"'):
                directory_path = directory_path[1:-1]
            elif directory_path.startswith("'") and directory_path.endswith("'"):
                directory_path = directory_path[1:-1]
        else:
            try:
                parsed_inputs = parse_tool_input(inputs)
                print(f"Parsed inputs: {parsed_inputs}")
                directory_path = parsed_inputs.get("directory_path", "")
            except Exception as e:
                print(f"Error parsing input: {str(e)}")
                # If parsing fails, treat the input as the directory path
                directory_path = inputs
    else:
        # It's a dictionary
        directory_path = inputs.get("directory_path", "")
    
    print(f"Final directory_path: {repr(directory_path)}")
    return list_files(directory_path, local_path)

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


def create_file(file_path, content, local_repo_path="local_repo"):
    """
    A simple utility to create a file directly.
    Use this as a backup if the Agent's tools aren't working.
    """
    import os
    
    # Ensure file_path doesn't contain the local_path already
    if local_repo_path in file_path:
        file_full_path = file_path
    else:
        file_full_path = os.path.join(local_repo_path, file_path)
    
    print(f"Creating file: {file_full_path}")
    
    # Ensure directory exists
    dir_path = os.path.dirname(file_full_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    
    # Write content to file
    with open(file_full_path, "w") as file:
        file.write(content)
    
    return f"File {file_path} has been created successfully."


def create_branch_wrapper(inputs, local_path="local_repo"):
    # If we get a string, attempt to parse it into a dictionary.
    if isinstance(inputs, str):
        if inputs.strip() and "=" not in inputs:
            # It's just the branch name
            branch_name = inputs.strip()
        else:
            try:
                inputs = parse_tool_input(inputs)
                branch_name = inputs.get("branch_name", "")
            except Exception as e:
                return f"Error parsing input string: {str(e)}"
    else:
        branch_name = inputs.get("branch_name", "")
    
    if not branch_name:
        return "Error: Missing branch_name."
    
    return create_branch(branch_name, local_path)


def checkout_branch_wrapper(inputs, local_path="local_repo"):
    # If we get a string, attempt to parse it into a dictionary.
    if isinstance(inputs, str):
        if inputs.strip() and "=" not in inputs:
            # It's just the branch name
            branch_name = inputs.strip()
        else:
            try:
                inputs = parse_tool_input(inputs)
                branch_name = inputs.get("branch_name", "")
            except Exception as e:
                return f"Error parsing input string: {str(e)}"
    else:
        branch_name = inputs.get("branch_name", "")
    
    if not branch_name:
        return "Error: Missing branch_name."
    
    return checkout_branch(branch_name, local_path)


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


def search_code_wrapper(inputs, local_path="local_repo"):
    # If we get a string, attempt to parse it into a dictionary.
    if isinstance(inputs, str):
        if inputs.strip() and "=" not in inputs:
            # It's just the search pattern
            search_pattern = inputs.strip()
        else:
            try:
                inputs = parse_tool_input(inputs)
                search_pattern = inputs.get("search_pattern", "")
            except Exception as e:
                return f"Error parsing input string: {str(e)}"
    else:
        search_pattern = inputs.get("search_pattern", "")
    
    if not search_pattern:
        return "Error: Missing search_pattern."
    
    return search_code(search_pattern, local_path)


def install_dependency_wrapper(inputs):
    # If we get a string, attempt to parse it into a dictionary.
    if isinstance(inputs, str):
        if inputs.strip() and "=" not in inputs:
            # It's just the package name
            package_name = inputs.strip()
        else:
            try:
                inputs = parse_tool_input(inputs)
                package_name = inputs.get("package_name", "")
            except Exception as e:
                return f"Error parsing input string: {str(e)}"
    else:
        package_name = inputs.get("package_name", "")
    
    if not package_name:
        return "Error: Missing package_name."
    
    return install_dependency(package_name)


def run_tests_wrapper(inputs, local_path="local_repo"):
    # If we get a string, attempt to parse it into a dictionary.
    test_path = ""
    if isinstance(inputs, str):
        if inputs.strip() == "":
            # Empty input means run all tests
            test_path = ""
        elif "=" not in inputs:
            # It's just the test path
            test_path = inputs.strip()
        else:
            try:
                inputs = parse_tool_input(inputs)
                test_path = inputs.get("test_path", "")
            except Exception as e:
                return f"Error parsing input string: {str(e)}"
    else:
        test_path = inputs.get("test_path", "")
    
    return run_tests(test_path, local_path)