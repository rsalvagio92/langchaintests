import os

def create_file(file_path, file_content, repo_path):
    """
    A direct function to create a file without any complex parsing.
    
    Args:
        file_path (str): Path to the file relative to the repo
        file_content (str): Content to write to the file
        repo_path (str): Full path to the repository
    
    Returns:
        str: Status message
    """
    try:
        full_path = os.path.join(repo_path, file_path)
        
        # Create directories if needed
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Write the file
        with open(full_path, 'w') as f:
            f.write(file_content)
            
        return f"File {file_path} created successfully."
    except Exception as e:
        return f"Error creating file: {str(e)}"

def delete_file(file_path, repo_path):
    """
    A direct function to delete a file without any complex parsing.
    
    Args:
        file_path (str): Path to the file relative to the repo
        repo_path (str): Full path to the repository
    
    Returns:
        str: Status message
    """
    try:
        full_path = os.path.join(repo_path, file_path)
        
        if os.path.exists(full_path):
            os.remove(full_path)
            return f"File {file_path} deleted successfully."
        else:
            return f"File {file_path} does not exist."
    except Exception as e:
        return f"Error deleting file: {str(e)}"

def list_files(repo_path):
    """
    A direct function to list all files in the repo.
    
    Args:
        repo_path (str): Full path to the repository
    
    Returns:
        list: List of all files in the repo
    """
    try:
        all_files = []
        for root, dirs, files in os.walk(repo_path):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
                
            for filename in files:
                rel_path = os.path.relpath(os.path.join(root, filename), repo_path)
                all_files.append(rel_path)
                
        return all_files
    except Exception as e:
        return f"Error listing files: {str(e)}"