from prerequisite import clone_and_build, get_os_info, \
    get_test_swarm_key, download_ipfs_binary, clone_and_install
from node.quorum import run_quorum_nodes
from node.non_quorum import run_non_quorum_nodes

import os

script_dir = os.path.dirname(os.path.abspath(__file__))


if __name__=='__main__':
    os_name, build_folder = get_os_info()
    complete_binary_path = os.path.join(os.path.abspath("./rubixgoplatform"), build_folder)

    # Clone and build Rubixgoplatform
    clone_and_build("https://github.com/rubixchain/rubixgoplatform.git", "main", os_name)

    github_file_url = "https://raw.githubusercontent.com/rubixchain/rubixgoplatform/main/testswarm.key"
    get_test_swarm_key(github_file_url,complete_binary_path)

    clone_and_install("https://github.com/rubixchain/rubix-nexus")
    
    download_ipfs_binary(os_name, "v0.21.0", complete_binary_path)

    os.chdir("../../")
    # Run quorum nodes
    run_quorum_nodes(False, False, quorum_list_file_name=complete_binary_path+"/quorumlist.json")
    
    # Run Non-Quorum node
    deployer_did = run_non_quorum_nodes(2)
