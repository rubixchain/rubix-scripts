# Rubix Single Node Script

This repository provides scripts to set up and manage a single non-quorum Rubix node on your machine. The setup ensures the installation of all necessary dependencies, and the node runs in the background upon successful execution. Once set up, you can explore and test Rubix APIs seamlessly.

## Scripts Overview

### `run_testnet.py`
This script is the first step in setting up a Rubix node. It installs all required dependencies and runs the node in the background. This script is a one-time setup process. After running this script, use `restart_testnet.py` for subsequent restarts.

- **Usage**: Run this script when setting up the node for the first time.

- **For Linux/MacOS:**
```sh
python3 run_testnet.py

```
- **For Windows:**
```sh
python run_testnet.py

```

---

### `restart_testnet.py`
This script restarts the node after it has been set up using `run_testnet.py`.

- **Usage**: Run this script to restart the node when required.

- **For Linux/MacOS:**
```sh
python3 restart_testnet.py

```
- **For Windows:**
```sh
python restart_testnet.py

```

---

### `shutdown.py`
This script stops the currently running node. It is recommended to run this script before logging off or when you're done with development or testing. Shutting down the node frees up system resources, which is considered a best practice.

- **Usage**: Run this script to shut down the node.

- **For Linux/MacOS:**
```sh
python3 shutdown.py

```
- **For Windows:**
```sh
python shutdown.py

```

---

### `deploy_contract.py`
This script deploys a sample smart contract on the Rubix network. The necessary files required for deployment are located in the `contract-files` directory.

- **Usage**: Run this script to deploy a sample smart contract.

- **For Linux/MacOS:**
```sh
python3 deploy_contract.py

```
- **For Windows:**
```sh
python deploy_contract.py

```

---

### `execute_contract.py`
This script executes a sample smart contract on the Rubix network. Executing a contract involves writing data onto the smart contract's token chain. The required input data for execution is stored in the `dependencies` directory in the `smart_contract_data.json` file.

- **Usage**: Run this script to execute a smart contract.

- **For Linux/MacOS:**
```sh
python3 execute_contract.py

```
- **For Windows:**
```sh
python execute_contract.py

```