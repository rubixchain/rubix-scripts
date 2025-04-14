from node.actions import generate_smart_contract, execute_smart_contract, subscribe_smart_contract
from app.app_config import update_config, get_config
from node.commands import get_build_dir
from node.utils import save_to_config_file, load_from_config_file

import os
import requests

script_dir = os.path.dirname(os.path.abspath(__file__))


def execute_contract(executor_did,contract_hash, server_port=20000):

    execute_smart_contract(contract_hash, executor_did, server_port,smart_contract_data, 10500)
    app_config = get_config()

if __name__=='__main__':
    node_config = load_from_config_file("node_config.json")
    print("node_config: ", node_config)
    # Extract the DID value
    did_value = node_config['dids']['user_did']['did']
    smart_contract_data = load_from_config_file("smart_contract_data.json")

    print(f"The DID value is: {did_value}")
    execute_contract(contract_hash,did_value,server_port,smart_contract_data,10500)