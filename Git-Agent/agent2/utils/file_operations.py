import os
import sys
import importlib.util
import pathlib

# Dynamic import for config
config_path = pathlib.Path(__file__).parent.parent / "config.py"
spec = importlib.util.spec_from_file_location("config", config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

MAX_FILE_SIZE = config.MAX_FILE_SIZE

def create_file(file_path, content, repo_path):
    """Create a file with the given content"""
    try:
        # Clean up file path - remove quotes
        if isinstance(file_path, str):
            file_path = file_path.strip()
            if (file_path.startswith('"') and file_path.endswith('"')) or \
               (file_path.startswith("'") and file_path.endswith("'")):
                file_path = file_path[1:-1]
        
        full_path = os.path.join(repo_path, file_path)
        print(f"Creating file: {full_path}")
        
        # Create directories if needed
        dir_path = os.path.dirname(full_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        with open(full_path, 'w') as f:
            f.write(content)
        
        return f"File {file_path} created successfully."
    except Exception as e:
        return f"Error creating file: {str(e)}"

def delete_file(file_path, repo_path):
    """Delete a file"""
    try:
        # Clean up file path - remove quotes
        if isinstance(file_path, str):
            file_path = file_path.strip()
            if (file_path.startswith('"') and file_path.endswith('"')) or \
               (file_path.startswith("'") and file_path.endswith("'")):
                file_path = file_path[1:-1]
        
        full_path = os.path.join(repo_path, file_path)
        print(f"Deleting file: {full_path}")
        
        if os.path.exists(full_path):
            os.remove(full_path)
            return f"File {file_path} deleted successfully."
        else:
            return f"File {file_path} does not exist."
    except Exception as e:
        return f"Error deleting file: {str(e)}"

def list_files(repo_path, directory_path="", get_tree=False):
    """
    List all files in the repository or directory
    
    Args:
        repo_path (str): Path to the repository
        directory_path (str): Relative path to list files from
        get_tree (bool): Whether to return a tree structure for the file explorer
    
    Returns:
        If get_tree=True: Returns a nested dictionary with the directory structure
        If get_tree=False: Returns a list of relative file paths
    """
    try:
        # Clean up directory path - remove quotes
        if isinstance(directory_path, str):
            directory_path = directory_path.strip()
            if (directory_path.startswith('"') and directory_path.endswith('"')) or \
               (directory_path.startswith("'") and directory_path.endswith("'")):
                directory_path = directory_path[1:-1]
        
        # Determine the directory to list files from
        if not directory_path:
            dir_path = repo_path
        else:
            dir_path = os.path.join(repo_path, directory_path)
        
        print(f"Listing files in: {dir_path}")
        
        if not os.path.exists(dir_path):
            return f"Directory {directory_path} does not exist."
        
        # For tree structure
        if get_tree:
            file_tree = {}
            
            for root, dirs, filenames in os.walk(dir_path):
                if '.git' in dirs:
                    dirs.remove('.git')
                
                # Get the relative path from the repo root
                rel_root = os.path.relpath(root, repo_path)
                if rel_root == ".":
                    rel_root = ""
                
                # Create path components
                path_parts = rel_root.split(os.path.sep) if rel_root else []
                
                # Build the nested dictionary
                current = file_tree
                for part in path_parts:
                    if part:
                        if part not in current:
                            current[part] = {"__type": "directory", "__files": {}}
                        current = current[part]["__files"]
                
                # Add files to the current level
                for filename in filenames:
                    full_path = os.path.join(root, filename)
                    size = os.path.getsize(full_path)
                    size_str = f"{size} bytes"
                    if size > 1024:
                        size_str = f"{size/1024:.1f} KB"
                    if size > 1024*1024:
                        size_str = f"{size/(1024*1024):.1f} MB"
                    
                    current[filename] = {
                        "__type": "file",
                        "__size": size_str,
                        "__path": os.path.join(rel_root, filename) if rel_root else filename
                    }
            
            return file_tree
        
        # For flat list
        else:
            files = []
            for root, dirs, filenames in os.walk(dir_path):
                if '.git' in dirs:
                    dirs.remove('.git')
                
                for filename in filenames:
                    rel_path = os.path.relpath(os.path.join(root, filename), repo_path)
                    # Add file size information
                    full_path = os.path.join(root, filename)
                    size = os.path.getsize(full_path)
                    size_str = f"{size} bytes"
                    if size > 1024:
                        size_str = f"{size/1024:.1f} KB"
                    if size > 1024*1024:
                        size_str = f"{size/(1024*1024):.1f} MB"
                    
                    files.append(f"{rel_path} ({size_str})")
            
            return files if files else f"No files found in {directory_path or 'repository'}."
    except Exception as e:
        return f"Error listing files: {str(e)}"

def read_file(file_path, repo_path):
    """Read the content of a file"""
    try:
        # Clean up file path - remove quotes
        if isinstance(file_path, str):
            file_path = file_path.strip()
            if (file_path.startswith('"') and file_path.endswith('"')) or \
               (file_path.startswith("'") and file_path.endswith("'")):
                file_path = file_path[1:-1]
        
        full_path = os.path.join(repo_path, file_path)
        print(f"Reading file: {full_path}")
        
        if not os.path.exists(full_path):
            return f"File {file_path} does not exist."
        
        # Check file size before reading
        file_size = os.path.getsize(full_path)
        if file_size > MAX_FILE_SIZE:
            preview_size = min(5000, file_size // 10)  # Show at most 5000 chars or 10% of file
            with open(full_path, 'r') as f:
                content_preview = f.read(preview_size)
            
            return (f"File {file_path} is too large ({file_size} bytes) to process in full. "
                   f"Here's a preview of the first {preview_size} characters:\n\n"
                   f"{content_preview}\n\n..."
                   f"\n\nPlease use a more specific command to work with sections of this file.")
            
        with open(full_path, 'r') as f:
            content = f.read()
        
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"