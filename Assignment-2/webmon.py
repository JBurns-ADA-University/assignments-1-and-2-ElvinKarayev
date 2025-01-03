import json
import subprocess
import requests
import time
import os
from datetime import datetime
import argparse

# Configuration
SERVER_PATH = '../Assignment-1/server.py'  # Relative path to the UBS server script
LOGFILE = 'webmon.log'  # Log file for monitoring UBS server activities

# Load the webmon configuration
def load_config(config_path='./webmon.json'):
    """
    Reads and loads the webmon configuration from a JSON file.
    Args:
        config_path (str): Path to the configuration JSON file.
    Returns:
        dict: Configuration settings.
    """
    with open(config_path, 'r') as f:
        return json.load(f)['webmonconfig']

# Start the UBS server
def start_ubs():
    """
    Starts the UBS server by launching the server script as a subprocess.
    Returns:
        subprocess.Popen: The process object representing the running server.
    """
    server_path = os.path.abspath(SERVER_PATH)
    return subprocess.Popen(['python', server_path])

# Check if UBS is running
def is_ubs_running(process):
    """
    Checks whether the UBS server process is still running.
    Args:
        process (subprocess.Popen): The process object to check.
    Returns:
        bool: True if the process is running, False otherwise.
    """
    return process.poll() is None

# Log events to a file
def log_to_file(logfile, message):
    """
    Writes a log message to a specified file.
    Args:
        logfile (str): The path to the log file.
        message (str): The log message to write.
    """
    with open(logfile, 'a') as f:
        f.write(message + '\n')

# Perform the request and get status code
def perform_request(waittime, server_port):
    """
    Sends an HTTP GET request to the UBS server and retrieves the status code.
    Args:
        waittime (float): Timeout duration for the request in seconds.
        server_port (int): Port number where the UBS server is running.
    Returns:
        int or str: The HTTP status code or an error descriptor ('timeout', 'error').
    """
    try:
        response = requests.get(f'http://127.0.0.1:{server_port}/getbalance', timeout=waittime)
        return response.status_code
    except requests.exceptions.Timeout:
        return 'timeout'
    except Exception as e:
        return 'error'

# Check if the status code matches the outcome key
def status_code_matches(status_code, outcome_key):
    """
    Compares the actual status code with the expected outcome key.
    Args:
        status_code (int or str): The actual status code or error descriptor.
        outcome_key (str): The expected outcome key from the configuration.
    Returns:
        bool: True if they match, False otherwise.
    """
    if outcome_key == 'timeout' and status_code == 'timeout':
        return True
    elif outcome_key.startswith('http') and isinstance(status_code, int):
        return outcome_key == 'http' + str(status_code)
    else:
        return False

# Monitor UBS with proper retry logic
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

# Main script execution
if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Webmon - Monitor UBS server.")
    parser = argparse.ArgumentParser(usage="webmon.py server_port")
    
    parser.add_argument(
        'server_port',
        type=int,
        help='Port number on which the UBS server is running'
    )
    args = parser.parse_args()

    # Load configuration
    config = load_config()

    # Start the UBS process
    ubs_process = start_ubs()

    try:
        monitor_ubs(config, ubs_process, server_port=args.server_port)
    except KeyboardInterrupt:
        if is_ubs_running(ubs_process):
            ubs_process.terminate()
        print("Webmon terminated.")
