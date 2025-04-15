from node.actions import generate_smart_contract, deploy_smart_contract, subscribe_smart_contract
from app.app_config import update_config, get_config
from node.commands import get_build_dir
from node.utils import save_to_config_file, load_from_config_file

import os
import requests

script_dir = os.path.dirname(os.path.abspath(__file__))


def deploy_contract(deployer_did, server_port=20000):

    wasm_file_path = os.path.abspath(os.path.join(script_dir, os.path.join("contract-files", "sample_contract.wasm")))
    raw_code_path = os.path.abspath(os.path.join(script_dir, os.path.join("contract-files", "lib.rs")))
    state_file_json = os.path.abspath(os.path.join(script_dir, os.path.join("contract-files", "state.json")))

    contract_hash = generate_smart_contract(wasm_file_path, raw_code_path, state_file_json, deployer_did, server_port, 10500)
    
    deploy_smart_contract(contract_hash, deployer_did, server_port, 10500)

    subscribe_smart_contract(contract_hash, server_port, 10500)

    print(f"Smart contract {contract_hash} has been deployed")
    save_to_config_file(script_dir,"smart_contract_details.json", {
        "contract_hash": contract_hash
    })
    
    # Register Dapp Callback URLs
    register_callback_url("http://localhost:20000",contract_hash, "/api/callback")

def register_callback_url(rubix_node_url, contract_hash, callback_url_endpoint):
    callback_url = f"http://localhost:8080{callback_url_endpoint}"
    
    payload = {
        "SmartContractToken": contract_hash,
        "CallBackURL": callback_url
    }

    api = f"{rubix_node_url}/api/register-callback-url"

    response = requests.post(api, json = payload)
    response_body = response.json()

    if not response_body["status"]:
        raise Exception(f"failed to register callback url {callback_url}, error: ", response_body["message"])

    print(f"Callback url {callback_url} has been registered")

if __name__=='__main__':
    print(f"script_did {script_dir}")  # Get the directory of the script
    dependencies_dir = os.path.join(script_dir, "dependencies")
    print(f"config_dir: {dependencies_dir}")  # Get the directory of the script
    node_config_path = os.path.join(dependencies_dir, "node_config.json")
    node_config = load_from_config_file(node_config_path)
    print("node_config: ", node_config)
    # Extract the DID value
    did_value = node_config['dids']['user_did']['did']

    print(f"The DID value is: {did_value}")
    deploy_contract(did_value)

    