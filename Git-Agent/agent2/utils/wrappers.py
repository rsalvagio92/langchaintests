import re
import importlib.util
import pathlib
from utils.dev_operations import *


# Dynamic import for config
config_path = pathlib.Path(__file__).parent.parent / "config.py"
spec = importlib.util.spec_from_file_location("config", config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

MAX_CONTENT_DISPLAY = config.MAX_CONTENT_DISPLAY

# Dynamic import for file_operations and git_operations
current_dir = pathlib.Path(__file__).parent
file_ops_path = current_dir / "file_operations.py"
file_ops_spec = importlib.util.spec_from_file_location("file_operations", file_ops_path)
file_operations = importlib.util.module_from_spec(file_ops_spec)
file_ops_spec.loader.exec_module(file_operations)

git_ops_path = current_dir / "git_operations.py"
git_ops_spec = importlib.util.spec_from_file_location("git_operations", git_ops_path)
git_operations = importlib.util.module_from_spec(git_ops_spec)
git_ops_spec.loader.exec_module(git_operations)

# Import specific functions
create_file = file_operations.create_file
delete_file = file_operations.delete_file
list_files = file_operations.list_files
read_file = file_operations.read_file
commit_and_push = git_operations.commit_and_push

def find_closing_quote(s, start_idx, quote_char):
    """Helper to find the closing quote, handling escaped quotes"""
    i = start_idx
    while i < len(s):
        if s[i] == quote_char and (i == start_idx or s[i-1] != '\\'):
            return i
        i += 1
    return -1

def modify_code_wrapper(inputs, repo_path):
    """Wrapper for create_file - simplified and robust parsing"""
    print(f"ModifyCode received: {repr(inputs)[:MAX_CONTENT_DISPLAY]}")
    
    file_path = None
    new_content = None
    
    # Handle dictionary input
    if not isinstance(inputs, str):
        file_path = inputs.get('file_path')
        new_content = inputs.get('new_content')
    else:
        # Extract file_path from inputs string
        file_path_match = re.search(r'file_path\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
        if file_path_match:
            file_path = file_path_match.group(1)
            print(f"Extracted file_path: {file_path}")
        
        # Extract new_content using custom logic to handle quoted strings
        if "new_content =" in inputs:
            start_idx = inputs.find("new_content =") + len("new_content =")
            content_part = inputs[start_idx:].strip()
            
            if content_part.startswith('"'):
                # Find the closing double quote
                end_idx = find_closing_quote(content_part, 1, '"')
                if end_idx > 0:
                    new_content = content_part[1:end_idx]
            elif content_part.startswith("'"):
                # Find the closing single quote
                end_idx = find_closing_quote(content_part, 1, "'")
                if end_idx > 0:
                    new_content = content_part[1:end_idx]
            
            # If we found content, handle escape sequences
            if new_content:
                new_content = new_content.replace('\\n', '\n').replace('\\t', '\t')
                print(f"Extracted new_content: {new_content[:50]}... (length: {len(new_content)})")
    
    # Validate parameters
    if not file_path:
        return "Error: Missing file_path parameter."
    if not new_content:
        # Try a last resort approach to capture content
        if isinstance(inputs, str) and "new_content =" in inputs:
            parts = inputs.split("new_content =")
            if len(parts) == 2:
                content_str = parts[1].strip()
                if content_str:
                    # Take everything as content
                    new_content = content_str
                    # Remove trailing quotes or commas if present
                    while new_content and new_content[-1] in ['"', "'", ',']: 
                        new_content = new_content[:-1]
                    print(f"Last resort extracted content: {new_content[:50]}... (length: {len(new_content)})")
        
        # If still no content, return error
        if not new_content:            
            return "Error: Missing or invalid new_content parameter."
    
    # Call the function
    return create_file(file_path, new_content, repo_path)

def delete_file_wrapper(inputs, repo_path):
    """Wrapper for delete_file - simplified parsing"""
    print(f"DeleteFile received: {repr(inputs)[:MAX_CONTENT_DISPLAY]}")
    
    file_path = None
    
    # Handle dictionary input
    if not isinstance(inputs, str):
        file_path = inputs.get('file_path')
    else:
        # Try parameter format
        file_path_match = re.search(r'file_path\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
        if file_path_match:
            file_path = file_path_match.group(1)
        else:
            # Try direct format (just the path)
            file_path = inputs.strip()
            if (file_path.startswith('"') and file_path.endswith('"')) or \
               (file_path.startswith("'") and file_path.endswith("'")):
                file_path = file_path[1:-1]
    
    # Validate parameters
    if not file_path:
        return "Error: Missing file_path parameter."
    
    print(f"Extracted file_path: {file_path}")
    
    # Call the function
    return delete_file(file_path, repo_path)

def list_files_wrapper(inputs, repo_path):
    """Wrapper for list_files - simplified parsing"""
    print(f"ListFiles received: {repr(inputs)[:MAX_CONTENT_DISPLAY]}")
    
    directory_path = ""
    
    # Handle dictionary or None input
    if not isinstance(inputs, str):
        directory_path = inputs.get('directory_path', "") if inputs else ""
    else:
        # Try parameter format
        dir_path_match = re.search(r'directory_path\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
        if dir_path_match:
            directory_path = dir_path_match.group(1)
        elif inputs.strip():
            # Try direct format (just the path)
            directory_path = inputs.strip()
            if (directory_path.startswith('"') and directory_path.endswith('"')) or \
               (directory_path.startswith("'") and directory_path.endswith("'")):
                directory_path = directory_path[1:-1]
    
    print(f"Extracted directory_path: {directory_path}")
    
    # Call the function
    return list_files(repo_path, directory_path)

def read_file_wrapper(inputs, repo_path):
    """Wrapper for read_file - simplified parsing"""
    print(f"ReadFile received: {repr(inputs)[:MAX_CONTENT_DISPLAY]}")
    
    file_path = None
    
    # Handle dictionary input
    if not isinstance(inputs, str):
        file_path = inputs.get('file_path')
    else:
        # Try parameter format
        file_path_match = re.search(r'file_path\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
        if file_path_match:
            file_path = file_path_match.group(1)
        else:
            # Try direct format (just the path)
            file_path = inputs.strip()
            if (file_path.startswith('"') and file_path.endswith('"')) or \
               (file_path.startswith("'") and file_path.endswith("'")):
                file_path = file_path[1:-1]
    
    # Validate parameters
    if not file_path:
        return "Error: Missing file_path parameter."
    
    print(f"Extracted file_path: {file_path}")
    
    # Call the function
    return read_file(file_path, repo_path)

def commit_and_push_wrapper(inputs, repo_path, github_token, github_repo, github_user):
    """Wrapper for commit_and_push - simplified parsing"""
    print(f"CommitAndPush received: {repr(inputs)[:MAX_CONTENT_DISPLAY]}")
    
    file_path = None
    commit_message = "Update code"
    
    # Handle dictionary input
    if not isinstance(inputs, str):
        file_path = inputs.get('file_path')
        commit_message = inputs.get('commit_message', "Update code")
    else:
        # Try parameter format for file_path
        file_path_match = re.search(r'file_path\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
        if file_path_match:
            file_path = file_path_match.group(1)
        
        # Try parameter format for commit_message
        commit_msg_match = re.search(r'commit_message\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
        if commit_msg_match:
            commit_message = commit_msg_match.group(1)
        
        # If no parameter format for file_path, try direct format
        if not file_path:
            parts = inputs.split(maxsplit=1)
            if len(parts) >= 1:
                file_path = parts[0].strip()
                if (file_path.startswith('"') and file_path.endswith('"')) or \
                   (file_path.startswith("'") and file_path.endswith("'")):
                    file_path = file_path[1:-1]
                
                if len(parts) > 1:
                    commit_message = parts[1].strip()
                    if (commit_message.startswith('"') and commit_message.endswith('"')) or \
                       (commit_message.startswith("'") and commit_message.endswith("'")):
                        commit_message = commit_message[1:-1]
    
    # Validate parameters
    if not file_path:
        return "Error: Missing file_path parameter."
    
    print(f"Extracted file_path: {file_path}")
    print(f"Extracted commit_message: {commit_message}")
    
    # Call the function
    return commit_and_push(file_path, commit_message, repo_path, github_token, github_repo, github_user)


def run_tests_wrapper(inputs, repo_path):
    """Wrapper for run_tests"""
    print(f"RunTests received: {repr(inputs)[:MAX_CONTENT_DISPLAY]}")
    
    test_path = ""
    
    # Handle dictionary input
    if not isinstance(inputs, str):
        test_path = inputs.get('test_path', "")
    else:
        # Try parameter format
        path_match = re.search(r'test_path\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
        if path_match:
            test_path = path_match.group(1)
        else:
            # Assume the input is the test path
            test_path = inputs.strip()
            if (test_path.startswith('"') and test_path.endswith('"')) or \
               (test_path.startswith("'") and test_path.endswith("'")):
                test_path = test_path[1:-1]
    
    # test_path can be empty to run all tests
    print(f"Running tests in: {test_path or 'all tests'}")
    
    # Call the function
    return run_tests(test_path, repo_path)

def install_dependencies_wrapper(inputs, repo_path):
    """Wrapper for install_dependencies"""
    print(f"InstallDependencies received: {repr(inputs)[:MAX_CONTENT_DISPLAY]}")
    
    requirements_file = "requirements.txt"
    
    # Handle dictionary input
    if not isinstance(inputs, str):
        requirements_file = inputs.get('requirements_file', "requirements.txt")
    else:
        # Try parameter format
        file_match = re.search(r'requirements_file\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
        if file_match:
            requirements_file = file_match.group(1)
        else:
            # Assume the input is the requirements file
            input_str = inputs.strip()
            if input_str:
                if (input_str.startswith('"') and input_str.endswith('"')) or \
                   (input_str.startswith("'") and input_str.endswith("'")):
                    requirements_file = input_str[1:-1]
                else:
                    requirements_file = input_str
    
    print(f"Installing dependencies from: {requirements_file}")
    
    # Call the function
    return install_dependencies(requirements_file, repo_path)

def analyze_code_wrapper(inputs, repo_path):
    """Wrapper for analyze_code"""
    print(f"AnalyzeCode received: {repr(inputs)[:MAX_CONTENT_DISPLAY]}")
    
    file_path = None
    
    # Handle dictionary input
    if not isinstance(inputs, str):
        file_path = inputs.get('file_path')
    else:
        # Try parameter format
        file_match = re.search(r'file_path\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
        if file_match:
            file_path = file_match.group(1)
        else:
            # Assume the input is the file path
            file_path = inputs.strip()
            if (file_path.startswith('"') and file_path.endswith('"')) or \
               (file_path.startswith("'") and file_path.endswith("'")):
                file_path = file_path[1:-1]
    
    # Validate parameters
    if not file_path:
        return "Error: Missing file_path parameter."
    
    print(f"Analyzing code in: {file_path}")
    
    # Call the function
    result = analyze_code(file_path, repo_path)
    
    # Format the result
    if isinstance(result, str):
        return result
    
    formatted_result = f"Analysis results for {file_path}:\n\n"
    
    if "pylint" in result:
        pylint_data = result["pylint"]
        if "issues" in pylint_data:
            formatted_result += f"Pylint found {pylint_data.get('count', 0)} issues\n"
            if isinstance(pylint_data["issues"], list):
                for issue in pylint_data["issues"][:10]:  # Show first 10 issues
                    formatted_result += f"- Line {issue.get('line', '?')}: {issue.get('message', 'Unknown issue')}\n"
                if len(pylint_data["issues"]) > 10:
                    formatted_result += f"... and {len(pylint_data['issues']) - 10} more issues\n"
        elif "raw" in pylint_data:
            formatted_result += f"Pylint output: {pylint_data['raw']}\n"
    
    if "flake8" in result:
        flake8_data = result["flake8"]
        formatted_result += f"\nFlake8 found {flake8_data.get('issues', 0)} issues\n"
        if flake8_data.get("output"):
            issues = flake8_data["output"].splitlines()[:10]  # Show first 10 issues
            for issue in issues:
                formatted_result += f"- {issue}\n"
            if len(flake8_data["output"].splitlines()) > 10:
                formatted_result += f"... and more issues\n"
    
    return formatted_result

def create_pull_request_wrapper(inputs, repo_path, github_token, github_repo):
    """Wrapper for create_pull_request"""
    print(f"CreatePullRequest received: {repr(inputs)[:MAX_CONTENT_DISPLAY]}")
    
    branch = None
    title = "New Pull Request"
    description = ""
    
    # Handle dictionary input
    if not isinstance(inputs, str):
        branch = inputs.get('branch')
        title = inputs.get('title', "New Pull Request")
        description = inputs.get('description', "")
    else:
        # Try to parse from the input
        # Check for JSON-like format
        try:
            if inputs.strip().startswith('{') and inputs.strip().endswith('}'):
                data = json.loads(inputs)
                branch = data.get('branch')
                title = data.get('title', "New Pull Request")
                description = data.get('description', "")
            else:
                # Try parameter format
                branch_match = re.search(r'branch\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
                if branch_match:
                    branch = branch_match.group(1)
                
                title_match = re.search(r'title\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
                if title_match:
                    title = title_match.group(1)
                
                desc_match = re.search(r'description\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
                if desc_match:
                    description = desc_match.group(1)
                
                # If no parameter format for branch, try direct format
                if not branch:
                    # Try to extract branch from first word
                    parts = inputs.split(maxsplit=1)
                    if parts:
                        branch = parts[0].strip()
                        if (branch.startswith('"') and branch.endswith('"')) or \
                           (branch.startswith("'") and branch.endswith("'")):
                            branch = branch[1:-1]
        except:
            return "Error: Unable to parse input."
    
    # Validate parameters
    if not branch:
        return "Error: Missing branch parameter."
    
    print(f"Creating PR from branch: {branch}")
    print(f"PR title: {title}")
    
    # Call the function
    return create_pull_request(branch, title, description, repo_path, github_token, github_repo)

def lint_code_wrapper(inputs, repo_path):
    """Wrapper for lint_code"""
    print(f"LintCode received: {repr(inputs)[:MAX_CONTENT_DISPLAY]}")
    
    path = None
    
    # Handle dictionary input
    if not isinstance(inputs, str):
        path = inputs.get('path')
    else:
        # Try parameter format
        path_match = re.search(r'path\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
        if path_match:
            path = path_match.group(1)
        else:
            # Assume the input is the path (can be empty)
            if inputs.strip():
                path = inputs.strip()
                if (path.startswith('"') and path.endswith('"')) or \
                   (path.startswith("'") and path.endswith("'")):
                    path = path[1:-1]
    
    print(f"Linting code in: {path or 'entire repository'}")
    
    # Call the function
    result = lint_code(repo_path, path)
    
    # Format the result
    if isinstance(result, str):
        return result
    
    formatted_result = "Linting results:\n\n"
    
    if "flake8" in result:
        flake8_data = result["flake8"]
        formatted_result += f"Flake8: Found {flake8_data.get('issues', 0)} issues\n"
        if flake8_data.get("output"):
            issues = flake8_data["output"].splitlines()[:10]  # Show first 10 issues
            for issue in issues:
                formatted_result += f"- {issue}\n"
            if len(flake8_data["output"].splitlines()) > 10:
                formatted_result += f"... and {len(flake8_data['output'].splitlines()) - 10} more issues\n"
        formatted_result += "\n"
    
    if "pylint" in result:
        pylint_data = result["pylint"]
        formatted_result += f"Pylint output:\n{pylint_data.get('output', 'No output')}\n"
        if pylint_data.get("error"):
            formatted_result += f"Pylint error: {pylint_data['error']}\n"
    
    return formatted_result

def stash_changes_wrapper(inputs, repo_path):
    """Wrapper for stash_changes"""
    print(f"StashChanges received: {repr(inputs)[:MAX_CONTENT_DISPLAY]}")
    
    pop = False
    message = None
    
    # Handle dictionary input
    if not isinstance(inputs, str):
        pop = inputs.get('pop', False)
        message = inputs.get('message')
    else:
        # Check for "pop" in the input
        if inputs.strip().lower() == "pop":
            pop = True
        else:
            # Try parameter format
            pop_match = re.search(r'pop\s*=\s*(true|false)', inputs, re.IGNORECASE)
            if pop_match:
                pop = pop_match.group(1).lower() == "true"
            
            message_match = re.search(r'message\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
            if message_match:
                message = message_match.group(1)
            elif not pop:
                # Assume the input is the stash message
                message = inputs.strip()
                if (message.startswith('"') and message.endswith('"')) or \
                   (message.startswith("'") and message.endswith("'")):
                    message = message[1:-1]
    
    print(f"Stash operation: {'pop' if pop else 'push'}")
    if message and not pop:
        print(f"Stash message: {message}")
    
    # Call the function
    return stash_changes(repo_path, pop, message)

def get_repo_status_wrapper(inputs, repo_path):
    """Wrapper for get_repo_status"""
    print(f"GetRepoStatus received: {repr(inputs)[:MAX_CONTENT_DISPLAY]}")
    
    # Call the function
    result = get_repo_status(repo_path)
    
    # Format the result
    if isinstance(result, str):
        return result
    
    formatted_result = "Repository Status:\n\n"
    
    formatted_result += f"Current branch: {result['current_branch']}\n"
    formatted_result += f"Available branches: {', '.join(result['branches'])}\n\n"
    
    if result['last_commit']:
        commit = result['last_commit']
        formatted_result += f"Last commit:\n"
        formatted_result += f"  Hash: {commit['hash']}\n"
        formatted_result += f"  Author: {commit['author']}\n"
        formatted_result += f"  Date: {commit['date']}\n"
        formatted_result += f"  Message: {commit['message']}\n\n"
    
    if result['has_changes']:
        formatted_result += f"Changes ({len(result['status'])} files):\n"
        for change in result['status']:
            formatted_result += f"  {change['type']}: {change['path']}\n"
    else:
        formatted_result += "Working tree clean\n"
    
    return formatted_result

def generate_diff_wrapper(inputs, repo_path):
    """Wrapper for generate_diff"""
    print(f"GenerateDiff received: {repr(inputs)[:MAX_CONTENT_DISPLAY]}")
    
    file_path = None
    
    # Handle dictionary input
    if not isinstance(inputs, str):
        file_path = inputs.get('file_path')
    else:
        # Try parameter format
        file_match = re.search(r'file_path\s*=\s*[\'\"]([^\'\"]+)[\'\"]', inputs)
        if file_match:
            file_path = file_match.group(1)
        elif inputs.strip():
            # Assume the input is the file path
            file_path = inputs.strip()
            if (file_path.startswith('"') and file_path.endswith('"')) or \
               (file_path.startswith("'") and file_path.endswith("'")):
                file_path = file_path[1:-1]
    
    # file_path can be None to get diff for all changes
    if file_path:
        print(f"Generating diff for file: {file_path}")
    else:
        print("Generating diff for all changes")
    
    # Call the function
    return generate_diff(repo_path, file_path)