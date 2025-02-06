import os
import json

from prerequisite import get_os_info
from node.commands import cmd_run_rubix_servers, cmd_setup_quorum_dids

if __name__=='__main__':
    os_name, build_folder = get_os_info()
    complete_binary_path = os.path.join(os.path.abspath("./rubixgoplatform"), build_folder)
    
    base_server = 20000
    base_grpc_server = 10500

    print("Current current working dir: ", os.getcwd())

    quorum_list_file = os.path.join(os.getcwd(), "rubixgoplatform", build_folder, "quorumlist.json")
    quorum_node_indices = [0, 1, 2, 3, 4]

    # Run Quorum nodes
    for idx in quorum_node_indices:
        node_name = f"node{idx}"
        server = base_server + idx
        grpc_server = base_grpc_server + idx

        cmd_run_rubix_servers(node_name, idx)

        print(f"Quorum node {idx} is running on {server} is running successfully")
    
    # Run Non-Quorum node
    cmd_run_rubix_servers("node5", 5)
    print(f"Non-Quorum node is running successfully")

    # Run Setup Quorum
    with open(quorum_list_file, "r") as f:
        quorum_list_data = json.load(f)

        for idx in quorum_node_indices:
            server = base_server + idx
            grpc_server = base_grpc_server + idx
            quorum_did = quorum_list_data[idx]["address"]

            cmd_setup_quorum_dids(quorum_did, server, grpc_server)

    print("Nodes have been restarted and setup successfully")