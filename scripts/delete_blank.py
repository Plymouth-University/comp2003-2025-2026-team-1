import yaml

def get_yaml_data(file_path: str):
    """
    Reads a YAML file from the specified file path and returns its contents as a dictionary.
    Parameters:
        file_path (str): The path to the YAML file to be read.
    Returns:
        dict: The contents of the YAML file as a dictionary.
    """
    with open(file_path, 'r') as file:
        data = dict(yaml.safe_load(file))

    return data

def save_yaml_data(data: dict, file_path: str):
    """
    Saves the provided data to a YAML file at the specified file path.
    Parameters:
        data (dict): The data to be saved to the YAML file.
        file_path (str): The path where the YAML file will be saved.
    """

    with open(file_path, 'w') as file:
        yaml.dump(data, file)

def format_yaml_data(yaml_data: dict, grid: str, grid_objects: dict):
    """
    Updates the yaml_data dictionary with the modified grid and grid_objects.

    Parameters:
        yaml_data (dict): The original YAML data loaded from the file.
        grid (str): The modified grid string after removing deleted keys.
        grid_objects (dict): The modified grid_objects dictionary after removing entries with empty lists.

    Returns:
        dict: The updated YAML data with the modified grid and grid_objects.
    """

    yaml_data['grid'] = grid
    yaml_data['gridObjects'] = grid_objects

    return yaml_data

def delete_blank_grid(grid: str, deleted_keys: list):
    """
    Removes occurrences of deleted keys from the grid string by replacing them with an empty string.
    Parameters:
        grid (str): The original grid string.
        deleted_keys (list): A list of keys that have been deleted from the grid_objects dictionary and need to be removed from the grid.
    Returns:
        str: The modified grid string with the deleted keys removed.
    """

    for key in deleted_keys:
        if key in grid:
            grid = grid.replace(key, '__')  # Replace the key with an 'empty' string in the grid

    return grid

def delete_blank_grid_objects(grid_objects: dict):
    """
    Removes entries from the grid_objects dictionary where the value is an empty list.
    Also collects the keys of the deleted entries to update the grid accordingly.
    Parameters:
        grid_objects (dict): A dictionary representing grid objects, where keys are object identifiers and values are lists of properties.
    Returns:
        tuple: A tuple containing the modified grid_objects dictionary and a list of deleted keys.
    """

    deleted_keys = []

    for key in grid_objects.keys():
        if grid_objects[key] == []:
            deleted_keys.append(key)
            del grid_objects[key]
    
    return grid_objects, deleted_keys

def delete_blank(input_path: str, output_path='formatted_level.yaml'):
    """
    Reads a YAML level file, removes empty grid objects, and updates the corresponding grid positions.
    Saves the modified data to a new YAML file.

    Parameters:
        input_path (str): Path to the input YAML file.
        output_path (str): Path to the output YAML file.

    Returns:
        str: An error message if an exception occurs, otherwise None.
    """

    try:
        yaml_data = get_yaml_data(input_path)
        level_grid = yaml_data['grid']
        level_objects = yaml_data['gridObjects']

        level_objects, deleted_keys = delete_blank_grid_objects(level_objects)
        level_grid = delete_blank_grid(level_grid, deleted_keys)

        formatted_yaml_data = format_yaml_data(yaml_data, level_grid, level_objects)
        save_yaml_data(formatted_yaml_data, output_path)
        return

    except Exception as e:
        return f"[ERROR] An error occurred while deleting blank data: {e}"

if __name__ == "__main__":
    error = delete_blank('blank_level.yaml', 'blank_level_deleted.yaml')
    if error:
        print(error)
    else:
        print("Blank data deleted successfully.")