import streamlit as st
import importlib.util
import pathlib

# Dynamic import for file_operations
utils_dir = pathlib.Path(__file__).parent.parent / "utils"
file_ops_path = utils_dir / "file_operations.py"
file_ops_spec = importlib.util.spec_from_file_location("file_operations", file_ops_path)
file_operations = importlib.util.module_from_spec(file_ops_spec)
file_ops_spec.loader.exec_module(file_operations)

list_files = file_operations.list_files

def render_file_tree(repo_path):
    """
    Render a collapsible file explorer for the repository
    
    Args:
        repo_path (str): Path to the repository
    """
    st.sidebar.markdown("### Repository Files")
    
    # Get the file tree structure
    file_tree = list_files(repo_path, get_tree=True)
    
    if isinstance(file_tree, str):
        # Error message from list_files
        st.sidebar.warning(file_tree)
    elif not file_tree:
        st.sidebar.info("No files found in repository.")
    else:
        # Render the tree structure
        render_directory("", file_tree, 0, st.sidebar)

def render_directory(path_prefix, directory, depth, container):
    """
    Recursively render a directory and its contents
    
    Args:
        path_prefix (str): Path prefix for this directory
        directory (dict): Directory structure
        depth (int): Current depth in the tree
        container: The streamlit container to render in
    """
    # Sort entries: directories first, then files
    sorted_entries = sorted(
        directory.items(),
        key=lambda x: (0 if x[0] == "__type" or x[0] == "__files" or x[0] == "__size" or x[0] == "__path" 
                        else (1 if x[1].get("__type") == "directory" else 2), x[0])
    )
    
    for name, info in sorted_entries:
        # Skip metadata keys
        if name in ["__type", "__files", "__size", "__path"]:
            continue
        
        # Check if this is a directory or file
        is_directory = info.get("__type") == "directory"
        
        if is_directory:
            # Calculate the full path for this directory
            dir_path = f"{path_prefix}/{name}" if path_prefix else name
            
            # Create an expander for this directory
            with container.expander(f"📁 {name}", expanded=depth < 1):
                # Render the contents of this directory in a new container to avoid nesting expanders
                render_directory(dir_path, info.get("__files", {}), depth + 1, container)
        else:
            # This is a file
            file_size = info.get("__size", "")
            file_path = info.get("__path", "")
            
            # Display the file with its size
            container.markdown(f"📄 **{name}** ({file_size})")
            
            # Add a button to view the file content
            if container.button(f"View", key=f"view_{file_path}"):
                # Create a main area container to show the file content
                st.subheader(f"File: {name}")
                try:
                    import os
                    full_path = os.path.join(st.session_state.repo_path, file_path)
                    if os.path.exists(full_path):
                        with open(full_path, 'r') as f:
                            content = f.read()
                        st.code(content)
                    else:
                        st.warning(f"File not found: {file_path}")
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")