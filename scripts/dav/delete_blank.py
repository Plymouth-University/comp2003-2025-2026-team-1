import yaml

"""
DO NOT EDIT THIS CONFIG SECTION UNLESS YOU KNOW WHAT YOU ARE DOING.
This section contains custom YAML representers and a custom Dumper to ensure that the output YAML file is formatted in a specific way,
including adding blank lines between top-level keys, representing lists in flow style, and representing strings as literal block scalars where necessary.
Modifying this section without understanding its purpose may lead to unintended consequences in the formatting of the output YAML file.
"""

class SpacedDumper(yaml.Dumper):

    def write_line_break(self, data=None):
        super().write_line_break(data)

        # Add blank line between top-level keys
        if len(self.indents) == 1:
            super().write_line_break()

class FlowList(list):
    pass

def flow_list_representer(dumper, data):
    return dumper.represent_sequence(
        'tag:yaml.org,2002:seq',
        data,
        flow_style=True
    )

class LiteralStr(str):
    pass

def literal_str_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

def none_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:null', '')

class FlowDict(dict):
    pass

def flow_dict_representer(dumper, data):
    return dumper.represent_mapping(
        'tag:yaml.org,2002:map',
        data,
        flow_style=True
    )

yaml.add_representer(FlowList, flow_list_representer) # Use the custom representer for FlowList to ensure it dumps in flow style (e.g., [p1, p2] and not as a block list - p1\n- p2)
yaml.add_representer(LiteralStr, literal_str_representer) # Use the custom representer for LiteralStr to ensure it dumps as a literal block scalar (using |) for grid
yaml.add_representer(type(None), none_representer) # Use the custom representer for None to represent it as an empty string in YAML instead of 'null' appearing in the output yaml file
yaml.add_representer(FlowDict, flow_dict_representer) # Use the custom representer for FlowDict to ensure it dumps in flow style (e.g., {key1: value1, key2: value2} and not as a block mapping - key1: value1\nkey2: value2)

"""
END OF CONFIG SECTION
"""

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
    yaml_text = yaml.dump(
            data,
            Dumper=SpacedDumper, # Use the custom SpacedDumper to add blank lines between top-level keys
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
            width=1000
        )

    # Ensure blank line between grid block and gridObjects
    yaml_text = yaml_text.replace("\ngridObjects:", "\n\ngridObjects:")

    with open(file_path, "w") as file:
        file.write(yaml_text)

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

    # force include to inline list
    if 'include' in yaml_data and isinstance(yaml_data['include'], list):
        yaml_data['include'] = FlowList(yaml_data['include'])
    
    # cameraSettings.postProcessing.depthOfField is a dict that we want to force to be inline, so we convert it to a FlowDict if it exists
    try:
        dof = yaml_data["cameraSettings"]["postProcessing"]["depthOfField"]
        yaml_data["cameraSettings"]["postProcessing"]["depthOfField"] = FlowDict(dof)
    except KeyError:
        pass

    yaml_data['grid'] = LiteralStr(grid)

    # Convert lists to FlowList so they dump as [p1]
    for k, v in grid_objects.items():
        if isinstance(v, list):
            grid_objects[k] = FlowList(v)
    
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
    keys = list(grid_objects.keys())
    for key in keys:
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

def main():

    input_valid = False
    while not input_valid:
        input_path = input("Enter the path to the YAML file you want to delete blank data from (e.g., levels/level1.yaml): ")
        if not input_path.endswith('.yaml'):
            print("Invalid file type. Please enter a path to a .yaml file.")
            continue
        try:
            with open(input_path, 'r') as file:
                yaml.safe_load(file)  # Try loading the YAML to check if it's valid
            input_valid = True
        except Exception as e:
            print(f"Error loading YAML file: {e}. Please try again.")

    output_valid = False
    while not output_valid:
        output_path = input("Enter the path where you want to save the modified YAML file (e.g., levels/level1_formatted.yaml): ")
        if output_path == '':
            output_path = 'formatted_level.yaml'
            output_valid = True
        if not output_path.endswith('.yaml'):
            print("Invalid file type. Please enter a path to a .yaml file.")
        else:
            output_valid = True

    error_message = delete_blank(input_path, output_path)
    if error_message:
        print(error_message)
    else:
        print(f"Successfully deleted blank data and saved to {output_path}")

if __name__ == "__main__":
    main()