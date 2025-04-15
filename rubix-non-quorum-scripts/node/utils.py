import json
import sys
import os
sys.path.insert(1, os.getcwd())
from .vars import QUORUM_NODES

def get_node_name_from_idx(idx, prefix_string: str = "node"):
    return prefix_string + str(idx)

def get_base_ports():
    base_ens_server = 20000
    base_grpc_port = 10500

    return base_ens_server, base_grpc_port

def get_did_by_alias(node_config, alias):
    return node_config["dids"][alias]["did"]

def save_to_config_file(base_dir, config_file_name, config):
    print(f"Saving config to {config_file_name}...")
    print(f"Base directory: {base_dir}")
    try:
        # Build the full path based on the base directory
        config_file_path = os.path.join(base_dir, "dependencies", config_file_name)
        
        # Ensure the parent directory exists
        parent_dir = os.path.dirname(config_file_path)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        # Write the config to the file
        with open(config_file_path, 'w') as f:
            json.dump(config, f, indent=4)
    except PermissionError as e:
        raise PermissionError(f"Error: Permission denied when trying to write to {config_file_path}.") from e
    except TypeError as e:
        raise TypeError(f"Error: Failed to serialize the config data to JSON.") from e
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}") from e
    
def load_from_config_file(config_file_path):
    try:
        with open(config_file_path, 'r') as file:
            config_data = json.load(file)
        return config_data
    except FileNotFoundError as e:
        return {}
    except json.JSONDecodeError as e:
        raise ValueError(f"Error: The file at {config_file_path} is not a valid JSON file.") from e
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}") from e
