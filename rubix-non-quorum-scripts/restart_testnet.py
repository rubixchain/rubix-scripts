import os
import json

from prerequisite import get_os_info
from node.commands import cmd_run_rubix_nodes, cmd_setup_quorum_dids

if __name__=='__main__':
    os_name, build_folder = get_os_info()
    complete_binary_path = os.path.join(os.path.abspath("./rubixgoplatform"), build_folder)
    print("Complete binary path: ", complete_binary_path)
    print("build folder: ", build_folder)
    base_server = 20000
    base_grpc_server = 10500

    print("Current current working dir: ", os.getcwd())

    # quorum_list_file = os.path.join(os.getcwd(), "rubixgoplatform", build_folder, "quorumlist.json")
    quorum_node_indices = [0]

    # Run Quorum nodes
    for idx in quorum_node_indices:
        node_name = f"node{idx}"
        server = base_server + idx
        grpc_server = base_grpc_server + idx

        cmd_run_rubix_nodes(node_name, idx)

        print(f"node {idx} is running on {server} is running successfully")

    print("Nodes have been restarted and setup successfully")