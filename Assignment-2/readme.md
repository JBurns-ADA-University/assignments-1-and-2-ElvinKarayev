
# Webmon - UBS Server Monitor

`webmon` is a Python-based monitoring tool for a UBS (User Banking System) server. It performs periodic checks on the server's responses and restarts it if necessary, based on configurable rules. This document explains the script in detail.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Requirements](#requirements)
4. [Configuration](#configuration)
5. [Code Explanation](#code-explanation)
    - [load_config](#load_config)
    - [start_ubs](#start_ubs)
    - [is_ubs_running](#is_ubs_running)
    - [log_to_file](#log_to_file)
    - [perform_request](#perform_request)
    - [status_code_matches](#status_code_matches)
    - [monitor_ubs](#monitor_ubs)
6. [Usage](#usage)
7. [Logs](#logs)
8. [License](#license)

---

## Overview

The `webmon` script monitors a UBS server by sending HTTP requests to check its status. If the server is unresponsive or returns errors, the script attempts to resolve the issue through retries or by restarting the server.

---

## Features

- Automatic health checks with configurable retry logic.
- Supports timeout handling for requests.
- Logs all activities and server events.
- Automatically restarts the server if required.

---

## Requirements

- Python 3.6+
- Libraries: `json`, `subprocess`, `requests`, `argparse`, `os`, `datetime`, `time`

---

## Configuration

The behavior of `webmon` is defined in a JSON file (`webmon.json`):

```json
{
  "webmonconfig": {
      "waittime": 10000,
      "logto": "fs",
      "timeout": {
        "retrytimes": 0,
        "action": "restart"
      },
      "http200": {
        "retrytimes": 0,
        "action": "nothing"
      },
      "http403": {
        "retrytimes": 2,
        "action": "restart"
      },
      "http500": {
        "retrytimes": 1,
        "action": "restart"
      }
    }
}
```

- **waittime**: Timeout for HTTP requests in milliseconds.
- **httpXXX**: Configuration for specific HTTP status codes, such as:
  - `retrytimes`: Number of retries before taking further action.
  - `action`: Action to take (e.g., `restart`).

---

## Code Explanation

### 1. **`load_config`**

```python
def load_config(config_path='./webmon.json'):
    with open(config_path, 'r') as f:
        return json.load(f)['webmonconfig']
```

- **Purpose**: Loads monitoring configuration from the `webmon.json` file.
- **How it works**:
  - Opens the JSON file.
  - Reads the `webmonconfig` section and returns it as a Python dictionary.
- **Usage**: This function ensures that all runtime parameters are configurable.

---

### 2. **`start_ubs`**

```python
def start_ubs():
    server_path = os.path.abspath(SERVER_PATH)
    return subprocess.Popen(['python', server_path])
```

- **Purpose**: Starts the UBS server as a separate process.
- **How it works**:
  - Converts the relative server path (`SERVER_PATH`) to an absolute path.
  - Uses the `subprocess` library to launch the server script in the background.
- **Returns**: A `Popen` object representing the server process.
- **Usage**: Used whenever the server needs to be started or restarted.

---

### 3. **`is_ubs_running`**

```python
def is_ubs_running(process):
    return process.poll() is None
```

- **Purpose**: Checks if the UBS server process is running.
- **How it works**:
  - Calls the `poll()` method on the `Popen` object.
  - If `poll()` returns `None`, the process is still active.
- **Usage**: Used to verify the health of the UBS server process.

---

### 4. **`log_to_file`**

```python
def log_to_file(logfile, message):
    with open(logfile, 'a') as f:
        f.write(message + '\n')
```

- **Purpose**: Logs messages to a specified log file.
- **How it works**:
  - Opens the log file in append mode.
  - Writes the provided message with a newline.
- **Usage**: Used to record significant events, such as server restarts or errors.

---

### 5. **`perform_request`**

```python
def perform_request(waittime, server_port):
    try:
        response = requests.get(f'http://127.0.0.1:{server_port}/getbalance', timeout=waittime)
        return response.status_code
    except requests.exceptions.Timeout:
        return 'timeout'
    except Exception as e:
        return 'error'
```

- **Purpose**: Sends an HTTP GET request to the server and captures the response.
- **How it works**:
  - Sends a request to the `/getbalance` endpoint with a timeout.
  - If the request succeeds, it returns the HTTP status code.
  - If the request times out or fails, it returns descriptive error values (`'timeout'` or `'error'`).
- **Usage**: Used for periodic health checks.

---

### 6. **`status_code_matches`**

```python
def status_code_matches(status_code, outcome_key):
    if outcome_key == 'timeout' and status_code == 'timeout':
        return True
    elif outcome_key.startswith('http') and isinstance(status_code, int):
        return outcome_key == 'http' + str(status_code)
    else:
        return False
```

- **Purpose**: Checks if the actual status code matches an expected outcome.
- **How it works**:
  - Compares the `status_code` to predefined `outcome_key` values.
- **Usage**: Used to determine whether retries or corrective actions are needed.

---

### 7. **`monitor_ubs`**

```python
def monitor_ubs(config, process, server_port):
    """
    Monitors the UBS server by making periodic requests and handling failures or errors based on the configuration.
    Args:
        config (dict): Monitoring configuration loaded from JSON.
        process (subprocess.Popen): The process object representing the UBS server.
        server_port (int): Port number where the UBS server is running.
    """
    waittime = config['waittime'] / 1000.0  # Convert milliseconds to seconds
    
    while True:
        # Restart UBS if it is not running
        if not is_ubs_running(process):
            process = start_ubs()
            log_to_file(LOGFILE, f"{datetime.now().isoformat()} - UBS restarted (process was not running)")
            continue

        # Make the initial request
        status_code = perform_request(waittime, server_port)
        outcome_key = 'http' + str(status_code) if isinstance(status_code, int) else status_code
        retry_config = config.get(outcome_key, {})
        retrytimes = retry_config.get('retrytimes', 0)
        action = retry_config.get('action', 'nothing')

        attempts = 1
        max_attempts = 1 + retrytimes  # Number of attempts allowed

        while attempts < max_attempts and status_code_matches(status_code, outcome_key):
            log_to_file(LOGFILE, f"{datetime.now().isoformat()} - Attempt {attempts}/{max_attempts}, Status: {status_code}")
            attempts += 1
            if attempts >= max_attempts:
                break  # All retries exhausted

            time.sleep(1)  # Wait before retrying
            status_code = perform_request(waittime, server_port)

        # After retries, check if action needs to be taken
        if status_code_matches(status_code, outcome_key) and outcome_key != 'http200':
            # Log failed attempts (all retries exhausted, undesirable outcome persists)
            log_to_file(LOGFILE, f"{datetime.now().isoformat()} - Attempt {attempts}/{max_attempts}, Status: {status_code} - Failed")
            # Take the action based on configuration
            if action == 'restart':
                process.terminate()
                process = start_ubs()
                log_to_file(LOGFILE, f"{datetime.now().isoformat()} - UBS restarted due to {outcome_key}")
        else:
            # Log successful outcome
            log_to_file(LOGFILE, f"{datetime.now().isoformat()} - Successful response: Status {status_code} after {attempts} attempts")
```

- **Purpose**: Monitors the UBS server, handles failures, and applies configured actions.
- **How it works**:
  - Periodically sends HTTP requests to the server.
  - Handles errors such as timeouts and unexpected responses based on configuration.
  - Applies retry logic and takes appropriate actions (e.g., restarting the server).
- **Usage**: 
  - This is the main function that orchestrates monitoring.
  - Continuously monitors the server for failures
---

## Usage

1. Start the script with the desired port number:

   ```bash
   python webmon.py <server_port>
   ```

2. Example:

   ```bash
   python webmon.py 8000
   ```

---

## Logs

The script logs events to a file (`webmon.log`), providing a record of all server activities.

---
