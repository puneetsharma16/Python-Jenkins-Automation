import time
import warnings
import pytest
import json
import os
from testCases.conftest import local_ip
from preMadeFunctions import pingFunction, ssh_netmiko

# Define constants for SSH credentials
USERNAME = "root"
PASSWORD = "admin"


# Function to perform ping checks on local and remote IPs
def perform_ping_check(local_ip, remote_ip, result_dict):
    print(f"--- Pinging local IP: {local_ip}")
    # Check if local IP is reachable
    if pingFunction.check_access(local_ip):
        result_dict["Ping Results"]["Local"] = True
        print(f"\n* Local Device is up after soft reset *")

        print(f"\n--- Pinging remote IP: {remote_ip}")
        # Check if remote IP is reachable
        if pingFunction.check_access(remote_ip):
            result_dict["Ping Results"]["Remote"] = True
            print(f"\n* Remote Device is up after soft reset *")
            result_dict["status"] = "PASS"
        else:
            result_dict["Ping Results"]["Remote"] = False
    else:
        result_dict["Ping Results"]["Local"] = False


# Function to append test results to a JSON file
def append_result_to_json(result, filename="iteration_results.json"):
    # Try to load existing JSON data, initialize if file doesn't exist or is invalid
    try:
        with open(filename, "r") as f:
            json_data = json.load(f)
        if not isinstance(json_data, dict) or "iterations" not in json_data:
            json_data = {"iterations": []}
    except (FileNotFoundError, json.JSONDecodeError):
        json_data = {"iterations": []}

    # Append new result to the iterations list
    json_data["iterations"].append(result)

    # Write updated JSON data back to the file
    with open(filename, "w") as f:
        json.dump(json_data, f, indent=4)

    # Print the result for debugging
    print(f"\nUpdated JSON Report: {json.dumps(result, indent=4)}")


# Function to wait for a ping response with retries
def wait_for_ping(ip, timeout=15, interval=3):
    """Retry ping until success or timeout (instead of fixed sleep)."""
    start = time.time()
    # Retry pinging until timeout is reached
    while time.time() - start < timeout:
        if pingFunction.check_access(ip):
            print(f"{ip} is reachable")
            return True
        print(f"Waiting for {ip} to respond...")
        time.sleep(interval)
    print(f"Timeout: {ip} not reachable after {timeout}s")
    return False


# Test function to perform a soft network reset and verify connectivity
def test_soft_reset(local_ip, remote_ip, iter, local_ping=None, remote_ping=None):
    # Print test iteration details
    print("\n****************************************************")
    print(f"\nLocal IP Address: {local_ip}")
    print(f"Remote IP Address: {remote_ip}")
    print(f"Running Iteration: {iter}")
    print("****************************************************")

    # Initialize result dictionary for this test iteration
    test_iteration_result = {
        "iteration": iter,
        "test": "test_reset",
        "status": "FAIL",
        "Local IP": local_ip,
        "Remote IP": remote_ip,
        "Ping Results": {
            "Local": False,
            "Remote": False
        }
    }

    # Attempt to reload network services via SSH
    try:
        ssh_netmiko.runcommand(local_ip, "/etc/init.d/network reload &")
        print("Network reload started in background")
        time.sleep(2)  # Brief pause to allow command initiation
    except Exception as e:
        print(f"SSH connection broke as expected: {e}")  # Expected due to network reload

    # Wait for local device to become reachable after reload
    print("Waiting for network services to reload (up to 15s)...")
    wait_for_ping(local_ip, timeout=15)

    # Perform ping checks on local and remote IPs
    perform_ping_check(local_ip, remote_ip, test_iteration_result)

    # Save test results to JSON file
    append_result_to_json(test_iteration_result)


# Suppress warnings to keep console output clean
def warn(*args, **kwargs):
    pass

# Example command to run the test with pytest
# pytest -v -s testCases/test_SSHReset.py::test_soft_reset --local-ip '192.168.1.56' --remote-ip '192.168.1.15'