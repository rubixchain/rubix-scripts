import subprocess
import os
import re
import platform
import time
import requests
from .utils import get_base_ports

def is_windows_os():
    os_name = platform.system()
    return os_name == "Windows"

def get_build_dir():
    os_name = platform.system()
    build_folder = ""
    if os_name == "Linux":
        build_folder = "linux"
    elif os_name == "Windows":
        build_folder = "windows"
    elif os_name == "Darwin":
        build_folder = "mac"

    return build_folder

def cmd_add_peer_details(peer_id, did_id, did_type, server_port, grpc_port):
    os.chdir("../" + get_build_dir())
    cmd_string = f"./rubixgoplatform addpeerdetails -peerID {peer_id} -did {did_id} -didType {did_type} -port {server_port} -grpcPort {grpc_port}"
    if is_windows_os():
        cmd_string = f".\\rubixgoplatform addpeerdetails -peerID {peer_id} -did {did_id} -didType {did_type} -port {server_port} -grpcPort {grpc_port}"
    output, code = run_command(cmd_string, True)
    print(output)

    if code != 0:
        raise Exception("Error occurred while run the command: " + cmd_string)

    os.chdir("../tests")
    return output

def run_command(cmd_string, is_output_from_stderr=False):
    assert isinstance(cmd_string, str), "command must be of string type"
    cmd_result = subprocess.run(cmd_string, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    code = cmd_result.returncode
    
    if int(code) != 0:
        err_output = cmd_result.stderr.decode('utf-8')[:-1]
        print(err_output)
        return err_output, int(code)

    output = ""
    if not is_output_from_stderr:
        output = cmd_result.stdout.decode('utf-8')[:-1]
        print(output)
        if output.find('[ERROR]') > 0 or output.find('parse error') > 0:
            return output, 1
        else:
            return output, code
    else:
        output = cmd_result.stderr.decode('utf-8')[:-1]
        if output.find('[ERROR]') > 0 or output.find('parse error') > 0:
            print(output)
            return output, 1
        else:
            return output, code

def cmd_run_rubix_servers(node_name, server_port_idx, isTestnet=False):
    os.chdir(os.path.join(os.getcwd(), "rubixgoplatform", get_build_dir()))
    
    base_node_server, base_grpc_port = get_base_ports()
    grpc_port = base_grpc_port + server_port_idx
    node_server = base_node_server + server_port_idx

    cmd_string = ""
    if is_windows_os():
        if not isTestnet:
            cmd_string = f"powershell -Command  Start-Process -FilePath '.\\rubixgoplatform.exe' -ArgumentList 'run -p {node_name} -n {server_port_idx} -s -testNet -grpcPort {grpc_port}' -WindowStyle Hidden"
        else:
            cmd_string = f"powershell -Command  Start-Process -FilePath '.\\rubixgoplatform.exe' -ArgumentList 'run -p {node_name} -n {server_port_idx} -s -grpcPort {grpc_port} -testNet -defaultSetup' -WindowStyle Hidden"
    else:
        if not isTestnet:
            cmd_string = f"tmux new -s {node_name} -d ./rubixgoplatform run -p {node_name} -n {server_port_idx} -s -testNet -grpcPort {grpc_port}"
        else:
            cmd_string = f"tmux new -s {node_name} -d ./rubixgoplatform run -p {node_name} -n {server_port_idx} -s -testNet -defaultSetup -grpcPort {grpc_port}"
    
    _, code = run_command(cmd_string)
    if code != 0:
        raise Exception("Error occurred while run the command: " + cmd_string)
    
    print("Waiting for 40 seconds before checking if its running....")
    time.sleep(40)
    try:
        # Check if the node is running and retrieve the list of DIDs
        did_list = check_if_nodes_is_running(server_port_idx)
        
        # Register each DID
        for did in did_list:
            print(f"Registering DID: {did}")
            try:
                cmd_register_did(did, node_server, grpc_port)
            except Exception as e:
                print(f"Error registering DID {did}: {e}")
    except Exception as e:
        raise e
    
    os.chdir("../../")
    return node_server, grpc_port

def cmd_run_rubix_nodes(node_name, server_port_idx, isTestnet=False):
    os.chdir(os.path.join(os.getcwd(), "rubixgoplatform", get_build_dir()))
    
    base_node_server, base_grpc_port = get_base_ports()
    grpc_port = base_grpc_port + server_port_idx
    node_server = base_node_server + server_port_idx

    cmd_string = ""
    if is_windows_os():
        if not isTestnet:
            cmd_string = f"powershell -Command  Start-Process -FilePath '.\\rubixgoplatform.exe' -ArgumentList 'run -p {node_name} -n {server_port_idx} -s -testNet -grpcPort {grpc_port}' -WindowStyle Hidden"
        else:
            cmd_string = f"powershell -Command  Start-Process -FilePath '.\\rubixgoplatform.exe' -ArgumentList 'run -p {node_name} -n {server_port_idx} -s -grpcPort {grpc_port} -testNet -defaultSetup' -WindowStyle Hidden"
    else:
        if not isTestnet:
            cmd_string = f"tmux new -s {node_name} -d ./rubixgoplatform run -p {node_name} -n {server_port_idx} -s -testNet -grpcPort {grpc_port}"
        else:
            cmd_string = f"tmux new -s {node_name} -d ./rubixgoplatform run -p {node_name} -n {server_port_idx} -s -testNet -defaultSetup -grpcPort {grpc_port}"
    
    _, code = run_command(cmd_string)
    if code != 0:
        raise Exception("Error occurred while run the command: " + cmd_string)
    
    print("Waiting for 40 seconds before checking if its running....")
    time.sleep(40)
    try:
        # Check if the node is running and retrieve the list of DIDs
        did_list = check_if_nodes_is_running(server_port_idx)
        
        # Register each DID
        for did in did_list:
            print(f"Registering DID: {did}")
            try:
                cmd_register_node(did, node_server, grpc_port)
            except Exception as e:
                print(f"Error registering DID {did}: {e}")
    except Exception as e:
        raise e
    
    os.chdir("../../")
    return node_server, grpc_port

def check_if_nodes_is_running(server_idx):
    base_server, _ = get_base_ports()
    port = base_server + int(server_idx)
    print(f"Check if server with ENS web server port {port} is running...")
    url = f"http://localhost:{port}/api/getalldid"
    try:
        print(f"Sending GET request to URL: {url}")
        response = requests.get(url)
        if response.status_code == 200:
            print(f"Server with port {port} is running successfully")
            
            # Parse the response JSON
            response_data = response.json()
            
            # Extract `did` values from `account_info`
            account_info = response_data.get("account_info", [])
            did_list = [account.get("did") for account in account_info if "did" in account]
            
            # Return the extracted `did` list
            return did_list
        else:
            raise Exception(f"Failed with Status Code: {response.status_code} | Server with port {port} is NOT running successfully")
    except Exception as e:
        raise Exception(f"ConnectionError | Server with port {port} is NOT running successfully. Error: {e}")

def cmd_create_did(server_port, grpc_port, did_type = 4, priv_pwd = "mypassword", quorum_pwd = "mypassword"):
    os.chdir(os.path.join(os.getcwd(), "rubixgoplatform", get_build_dir()))
    cmd_string = f"./rubixgoplatform createdid -port {server_port} -grpcPort {grpc_port} -didType {did_type} -privPWD {priv_pwd} -quorumPWD {quorum_pwd}"
    if is_windows_os():
        cmd_string = f".\\rubixgoplatform createdid -port {server_port} -grpcPort {grpc_port} -didType {did_type} -privPWD {priv_pwd} -quorumPWD {quorum_pwd}"
    output, code = run_command(cmd_string, True)
    print(output)
    
    if code != 0:
        raise Exception("Error occurred while run the command: " + cmd_string)
    
    did_id = ""
    if "successfully" in output:
        pattern = r'bafybmi\w+'
        matches = re.findall(pattern, output)
        if matches:
            did_id = matches[0]
        else:
            raise Exception("unable to extract DID ID")

    os.chdir("../../")
    return did_id

def cmd_register_did(did_id, server_port, grpc_port, priv_pwd = "mypassword"):
    os.chdir(os.path.join(os.getcwd(), "rubixgoplatform", get_build_dir()))
    cmd_string = f"./rubixgoplatform registerdid -did {did_id} -port {server_port} -grpcPort {grpc_port} -privPWD {priv_pwd}"
    if is_windows_os():
        cmd_string = f".\\rubixgoplatform registerdid -did {did_id} -port {server_port} -grpcPort {grpc_port} -privPWD {priv_pwd}"
    output, code = run_command(cmd_string, True)
    print(output)

    if code != 0:
        raise Exception("Error occurred while run the command: " + cmd_string)

    os.chdir("../../")
    return output


def cmd_register_node(did_id, server_port, grpc_port, priv_pwd = "mypassword"):
    # os.chdir(os.path.join(os.getcwd(), "rubixgoplatform", get_build_dir()))
    cmd_string = f"./rubixgoplatform registerdid -did {did_id} -port {server_port} -grpcPort {grpc_port} -privPWD {priv_pwd}"
    if is_windows_os():
        cmd_string = f".\\rubixgoplatform registerdid -did {did_id} -port {server_port} -grpcPort {grpc_port} -privPWD {priv_pwd}"
    output, code = run_command(cmd_string, True)
    print(output)

    if code != 0:
        raise Exception("Error occurred while run the command: " + cmd_string)

    os.chdir("../../")
    return output

def cmd_generate_rbt(did_id, numTokens, server_port, grpc_port, priv_pwd = "mypassword"):
    os.chdir(os.path.join(os.getcwd(), "rubixgoplatform", get_build_dir()))
    cmd_string = f"./rubixgoplatform generatetestrbt -did {did_id} -numTokens {numTokens} -port {server_port} -grpcPort {grpc_port} -privPWD {priv_pwd}"
    if is_windows_os():
        cmd_string = f".\\rubixgoplatform generatetestrbt -did {did_id} -numTokens {numTokens} -port {server_port} -grpcPort {grpc_port} -privPWD {priv_pwd}"
    output, code = run_command(cmd_string, True)
    
    if code != 0:
        raise Exception("Error occurred while run the command: " + cmd_string)

    os.chdir("../../")
    return output

def cmd_add_quorum_dids(server_port, grpc_port, quorumlist = "quorumlist.json"):
    os.chdir(os.path.join(os.getcwd(), "rubixgoplatform", get_build_dir()))
    cmd_string = f"./rubixgoplatform addquorum -port {server_port} -grpcPort {grpc_port} -quorumList {quorumlist}"
    if is_windows_os():
        cmd_string = f".\\rubixgoplatform addquorum -port {server_port} -grpcPort {grpc_port} -quorumList {quorumlist}"
    output, code = run_command(cmd_string, True)
    print(output)
    if code != 0:
        raise Exception("Error occurred while run the command: " + cmd_string)

    os.chdir("../../")
    return output

def cmd_shutdown_node(server_port, grpc_port):
    os.chdir(os.path.join(os.getcwd(), "rubixgoplatform", get_build_dir()))
    cmd_string = f"./rubixgoplatform shutdown -port {server_port} -grpcPort {grpc_port}"
    if is_windows_os():
        cmd_string = f".\\rubixgoplatform shutdown -port {server_port} -grpcPort {grpc_port}"
    output, _ = run_command(cmd_string, True)
    print(output)

    os.chdir("../../")
    return output

def cmd_setup_quorum_dids(did, server_port, grpc_port):
    os.chdir(os.path.join(os.getcwd(), "rubixgoplatform", get_build_dir()))
    cmd_string = f"./rubixgoplatform setupquorum -did {did} -port {server_port} -grpcPort {grpc_port}"
    if is_windows_os():
        cmd_string = f".\\rubixgoplatform setupquorum -did {did} -port {server_port} -grpcPort {grpc_port}"
    output, code = run_command(cmd_string, True)
    print(output)
    if code != 0:
        raise Exception("Error occurred while run the command: " + cmd_string)

    os.chdir("../../")
    return output

def cmd_add_peer_details(peer_id, did_id, did_type, server_port, grpc_port):
    os.chdir(os.path.join(os.getcwd(), "rubixgoplatform", get_build_dir()))
    cmd_string = f"./rubixgoplatform addpeerdetails -peerID {peer_id} -did {did_id} -didType {did_type} -port {server_port} -grpcPort {grpc_port}"
    if is_windows_os():
        cmd_string = f".\\rubixgoplatform addpeerdetails -peerID {peer_id} -did {did_id} -didType {did_type} -port {server_port} -grpcPort {grpc_port}"
    output, code = run_command(cmd_string, True)
    print(output)

    if code != 0:
        raise Exception("Error occurred while run the command: " + cmd_string)

    os.chdir("../../")
    return output

def cmd_get_peer_id(server_port, grpc_port):
    os.chdir(os.path.join(os.getcwd(), "rubixgoplatform", get_build_dir()))
    cmd_string = f"./rubixgoplatform get-peer-id -port {server_port} -grpcPort {grpc_port}"
    if is_windows_os():
        cmd_string = f".\\rubixgoplatform get-peer-id -port {server_port} -grpcPort {grpc_port}"
    output, code = run_command(cmd_string)

    if code != 0:
        raise Exception("Error occurred while run the command: " + cmd_string)
    os.chdir("../../")
    return output



def cmd_generate_smart_contract(wasm_file_path, code_file_path, state_file_path, deployer_did, server_port, grpc_port):
    os.chdir(os.path.join(os.getcwd(), "rubixgoplatform", get_build_dir()))
    cmd_string = f"./rubixgoplatform generatesct -did {deployer_did} -binCode {wasm_file_path} -rawCode {code_file_path} -schemaFile {state_file_path} -port {server_port} -grpcPort {grpc_port}"
    if is_windows_os():
        cmd_string = f".\\rubixgoplatform generatesct -did {deployer_did} -binCode {wasm_file_path} -rawCode {code_file_path} -schemaFile {state_file_path} -port {server_port} -grpcPort {grpc_port}"
    output, code = run_command(cmd_string, True)

    if code != 0:
        raise Exception("Error occurred while run the command: " + cmd_string)
    
    contract_hash = ""

    if "successfully" in output:
        pattern = r"\bQm\w+"
        matches = re.findall(pattern, output)
        if matches:
            contract_hash = matches[0]
        else:
            raise Exception("unable to extract Contract hash")

    os.chdir("../../")
    return contract_hash

def cmd_deploy_smart_contract(contract_hash, deployer_did, server_port, grpc_port):
    os.chdir(os.path.join(os.getcwd(), "rubixgoplatform", get_build_dir()))
    cmd_string = f"./rubixgoplatform deploysmartcontract -sct {contract_hash} -transType 2 -deployerAddr {deployer_did} -rbtAmount 2 -port {server_port} -grpcPort {grpc_port}"
    if is_windows_os():
        cmd_string = f".\\rubixgoplatform deploysmartcontract -sct {contract_hash} -transType 2 -deployerAddr {deployer_did} -rbtAmount 2 -port {server_port} -grpcPort {grpc_port}"
    output, code = run_command(cmd_string, True)
    print(output)
    
    if code != 0:
        raise Exception("Error occurred while run the command: " + cmd_string)
    os.chdir("../../")

def cmd_deploy_smart_contract(contract_hash, deployer_did, server_port, grpc_port):
    os.chdir(os.path.join(os.getcwd(), "rubixgoplatform", get_build_dir()))
    cmd_string = f"./rubixgoplatform deploysmartcontract -sct {contract_hash} -transType 2 -deployerAddr {deployer_did} -rbtAmount 2 -port {server_port} -grpcPort {grpc_port}"
    if is_windows_os():
        cmd_string = f".\\rubixgoplatform deploysmartcontract -sct {contract_hash} -transType 2 -deployerAddr {deployer_did} -rbtAmount 2 -port {server_port} -grpcPort {grpc_port}"
    output, code = run_command(cmd_string, True)
    print(output)
    
    if code != 0:
        raise Exception("Error occurred while run the command: " + cmd_string)
    os.chdir("../../")

def cmd_subscribe_smart_contract(contract_hash, server_port, grpc_port):
    os.chdir(os.path.join(os.getcwd(), "rubixgoplatform", get_build_dir()))
    cmd_string = f"./rubixgoplatform subscribesct -sct {contract_hash} -port {server_port} -grpcPort {grpc_port}"
    if is_windows_os():
        cmd_string = f".\\rubixgoplatform subscribesct -sct {contract_hash} -port {server_port} -grpcPort {grpc_port}"
    output, code = run_command(cmd_string, True)
    print(output)
    
    if code != 0:
        raise Exception("Error occurred while run the command: " + cmd_string)
    os.chdir("../../")


def cmd_deploy_smart_contract(contract_hash, deployer_did, server_port, grpc_port):
    os.chdir(os.path.join(os.getcwd(), "rubixgoplatform", get_build_dir()))
    cmd_string = f"./rubixgoplatform deploysmartcontract -sct {contract_hash} -transType 2 -deployerAddr {deployer_did} -rbtAmount 2 -port {server_port} -grpcPort {grpc_port}"
    if is_windows_os():
        cmd_string = f".\\rubixgoplatform deploysmartcontract -sct {contract_hash} -transType 2 -deployerAddr {deployer_did} -rbtAmount 2 -port {server_port} -grpcPort {grpc_port}"
    output, code = run_command(cmd_string, True)
    print(output)
    
    if code != 0:
        raise Exception("Error occurred while run the command: " + cmd_string)
    os.chdir("../../")

def cmd_execute_smart_contract(contract_hash, executor_did,smart_contract_data, server_port, grpc_port ):
    os.chdir(os.path.join(os.getcwd(), "rubixgoplatform", get_build_dir()))
    cmd_string = f"./rubixgoplatform executesmartcontract -sct {contract_hash} -transType 2 -executorAddr {executor_did} -sctData {smart_contract_data} -rbtAmount 2 -port {server_port} -grpcPort {grpc_port}"
    if is_windows_os():
        cmd_string = f".\\rubixgoplatform executesmartcontract -sct {contract_hash} -transType 2 -executorAddr {executor_did} -sctData {smart_contract_data} -rbtAmount 2 -port {server_port} -grpcPort {grpc_port}"
    output, code = run_command(cmd_string, True)
    print(output)
    
    if code != 0:
        raise Exception("Error occurred while run the command: " + cmd_string)
    os.chdir("../../")
    