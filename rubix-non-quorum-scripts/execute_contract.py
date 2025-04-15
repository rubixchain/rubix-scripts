from node.actions import execute_smart_contract
from node.utils import load_from_config_file

import os
import requests

script_dir = os.path.dirname(os.path.abspath(__file__))
if __name__=='__main__':
    print(f"script_did {script_dir}")  # Get the directory of the script
    dependencies_dir = os.path.join(script_dir, "dependencies")
    print(f"config_dir: {dependencies_dir}")  # Get the directory of the script
    
    # Construct the full path to the JSON file
    smart_contract_data_path = os.path.join(dependencies_dir, "smart_contract_data.json")
    node_config_path = os.path.join(dependencies_dir, "node_config.json")
    smart_contract_details_path = os.path.join(dependencies_dir, "smart_contract_details.json")
    node_config = load_from_config_file(node_config_path)
    print("node_config: ", node_config)
    # Extract the DID value
    executor_did = node_config['dids']['user_did']['did']
    server_port = node_config['server']
    smart_contract_data = load_from_config_file(smart_contract_data_path)
    contract_hash = load_from_config_file(smart_contract_details_path)["contract_hash"]
    execute_smart_contract(contract_hash, executor_did, smart_contract_data,server_port, 10500)