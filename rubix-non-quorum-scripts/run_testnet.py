from prerequisite import clone_and_build, get_os_info, \
     download_ipfs_binary
from node.non_quorum import run_non_quorum_nodes
from node.actions import setup_rubix_nodes, create_and_register_did, fund_did_with_rbt
from app.app_config import update_config

import os
import requests

script_dir = os.path.dirname(os.path.abspath(__file__))
    

def fetch_testnet_swarm_key(build_dir):
    url = "https://github.com/rubixchain/rubixgoplatform/raw/refs/heads/development/testswarm.key"
    response = requests.get(url)
    
    if response.status_code == 200:
        swarm_key_path = os.path.join(build_dir, "testswarm.key")
        with open(swarm_key_path, "wb") as file:
            file.write(response.content)
        print(f"Swarm key has been downloaded and saved to {swarm_key_path}")
    else:
        raise Exception(f"Failed to download swarm key, status code: {response.status_code}")

def run_testnet_node():
    non_quorum_config = setup_rubix_nodes(0, 0, isTestnet=True)
    node_key = "node0"
    config_param = non_quorum_config[node_key]

    user_did = create_and_register_did(config_param, "user_did", register_did=True)
    fund_did_with_rbt(config_param, user_did)

    update_config(user_did=user_did, non_quorum_node_address="http://localhost:20000")

    return user_did

if __name__=='__main__':
    os_name, build_folder = get_os_info()
    complete_binary_path = os.path.join(os.path.abspath("./rubixgoplatform"), build_folder)

    # Clone and build Rubixgoplatform
    clone_and_build("https://github.com/rubixchain/rubixgoplatform.git", "dev/trie", os_name)

    fetch_testnet_swarm_key(complete_binary_path)

    download_ipfs_binary(os_name, "v0.21.0", complete_binary_path)

    os.chdir("../")

    # Run Non-Quorum node
    node_did = run_testnet_node() 
    print(f"The node did created : {node_did}")