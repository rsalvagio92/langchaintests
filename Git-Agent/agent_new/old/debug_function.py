import os

def list_all_files(repo_path):
    """A direct simple function to list all files in the repo path."""
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

def direct_delete_file(file_path, repo_path):
    """A direct function to delete a file without any complex parsing."""
    try:
        full_path = os.path.join(repo_path, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return f"File {file_path} deleted successfully."
        else:
            return f"File {file_path} does not exist."
    except Exception as e:
        return f"Error deleting file: {str(e)}"