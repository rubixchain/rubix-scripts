# Rubix Node Management Scripts

This repository contains scripts to automate the setup, shutdown, and restart of Rubix nodes.

## Scripts Overview

### `run.py`
This script sets up all the necessary prerequisites for running a Rubix node. It automates the steps mentioned in the "Joining the Testnet" page.

#### **Node Configuration:**
- Initializes a total of **5 Quorum nodes** (running on ports `20000-20004`).
- Initializes **1 Non-Quorum node** (running on port `20005`).

#### **Usage:**
Run this script when setting up a node for the first time. After the initial setup, you can use `restart.py` to restart the nodes.

- **For Linux/MacOS:**
```sh
python3 run.py

```
- **For Windows:**
```sh
python run.py

```

### `shutdown.py`
This script stops all currently running Rubix nodes.

#### **Usage:**
Run this script when you want to shut down the nodes.
```sh
python3 shutdown.py

```
- **For Windows:**
```sh
python shutdown.py

```

### `restart.py`
This script restarts the nodes previously initiated by run.py.

#### Usage:
Run this script after shutting down the nodes to restart them.

- **For Linux/MacOS:**
```sh
python3 restart.py

```
- **For Windows:**
```sh
python restart.py

```
