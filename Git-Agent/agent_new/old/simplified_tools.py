from direct_file_ops import create_file, delete_file, list_files

def direct_modify_code_wrapper(inputs, local_path="local_repo"):
    """
    Simplified wrapper for modify_code that skips complex parsing.
    
    Just extracts file_path and new_content directly.
    """
    print(f"ModifyCode received inputs: {repr(inputs)}")
    
    # Try to parse in a very basic way
    try:
        # Check if it's a string or dict
        if isinstance(inputs, str):
            # Find the file_path
            if 'file_path' in inputs:
                # Very basic extraction - find the file path between quotes
                start = inputs.find('file_path') + len('file_path') + 1
                # Find the first quote after file_path =
                while start < len(inputs) and inputs[start] not in ['"', "'"]:
                    start += 1
                if start < len(inputs):
                    start += 1  # Skip the quote
                    end = inputs.find(inputs[start-1], start)
                    if end > start:
                        file_path = inputs[start:end].strip()
                    else:
                        file_path = None
                else:
                    file_path = None
                
                # Find the new_content - everything after new_content =
                if 'new_content' in inputs:
                    start = inputs.find('new_content') + len('new_content') + 1
                    # Find the first quote after new_content =
                    while start < len(inputs) and inputs[start] not in ['"', "'"]:
                        start += 1
                    if start < len(inputs):
                        start += 1  # Skip the quote
                        end = inputs.find(inputs[start-1], start)
                        if end > start:
                            new_content = inputs[start:end].strip()
                            # Handle escaped newlines
                            new_content = new_content.replace('\\n', '\n')
                            new_content = new_content.replace('\\t', '\t')
                        else:
                            new_content = None
                    else:
                        new_content = None
                else:
                    new_content = None
            else:
                file_path = None
                new_content = None
        else:
            # It's a dict
            file_path = inputs.get('file_path')
            new_content = inputs.get('new_content')
    except Exception as e:
        print(f"Error in basic parsing: {str(e)}")
        file_path = None
        new_content = None
    
    print(f"Extracted file_path: {repr(file_path)}")
    print(f"Extracted new_content: {repr(new_content)}")
    
    # Validate parameters
    if not file_path:
        return "Error: Missing file_path parameter."
    if not new_content:
        return "Error: Missing new_content parameter."
    
    # Call the direct function
    return create_file(file_path, new_content, local_path)

def direct_delete_file_wrapper(inputs, local_path="local_repo"):
    """
    Simplified wrapper for delete_file that skips complex parsing.
    
    Just extracts file_path directly.
    """
    print(f"DeleteFile received inputs: {repr(inputs)}")
    
    # Try to parse in a very basic way
    try:
        # Check if it's a string or dict
        if isinstance(inputs, str):
            # If it's just a plain string without = chars, treat it as the file path
            if '=' not in inputs:
                file_path = inputs.strip()
                # Remove quotes if present
                if (file_path.startswith('"') and file_path.endswith('"')) or \
                   (file_path.startswith("'") and file_path.endswith("'")):
                    file_path = file_path[1:-1]
            # Otherwise try to extract file_path
            elif 'file_path' in inputs:
                # Very basic extraction - find the file path between quotes
                start = inputs.find('file_path') + len('file_path') + 1
                # Find the first quote after file_path =
                while start < len(inputs) and inputs[start] not in ['"', "'"]:
                    start += 1
                if start < len(inputs):
                    start += 1  # Skip the quote
                    end = inputs.find(inputs[start-1], start)
                    if end > start:
                        file_path = inputs[start:end].strip()
                    else:
                        file_path = None
                else:
                    file_path = None
            else:
                file_path = None
        else:
            # It's a dict
            file_path = inputs.get('file_path')
    except Exception as e:
        print(f"Error in basic parsing: {str(e)}")
        file_path = None
    
    print(f"Extracted file_path: {repr(file_path)}")
    
    # Validate parameters
    if not file_path:
        return "Error: Missing file_path parameter."
    
    # Call the direct function
    return delete_file(file_path, local_path)

def direct_list_files_wrapper(inputs, local_path="local_repo"):
    """
    Simplified wrapper for list_files that skips complex parsing.
    """
    print(f"ListFiles called with local_path: {local_path}")
    return list_files(local_path)