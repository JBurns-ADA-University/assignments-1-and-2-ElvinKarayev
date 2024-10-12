import requests
import sys
import time

def main():
    # Check if the user provided exactly two command-line arguments (excluding the script name)
    if len(sys.argv) != 3:
        # If not, display the correct usage and exit the program
        print('Usage: python client.py <server_address> <port>')
        sys.exit(1)

    # Extract the server address and port number from the command-line arguments
    server_address = sys.argv[1]
    port = sys.argv[2]

    # Construct the base URL using the provided server address and port number
    base_url = f'http://{server_address}:{port}'

    # Create a Session object to persist certain parameters across requests
    # and to reuse the underlying TCP connection for multiple requests
    session = requests.Session()

    # Define the number of times to call the /getbalance endpoint
    num_requests = 20

    # Loop to send multiple GET requests to the /getbalance endpoint
    for i in range(num_requests):
        try:
            # Send a GET request to the /getbalance endpoint with a timeout of 10 seconds
            response = session.get(f'{base_url}/getbalance', timeout=10)

            # Print the status code received from the server
            print(f'/getbalance response status code: {response.status_code}')

        except requests.exceptions.Timeout:
            # Handle the case where the request times out
            print('/getbalance request timed out')

        except requests.exceptions.RequestException as e:
            print(f'/getbalance request failed: {e}')

        # Wait for half a second before sending the next request to avoid overwhelming the server
        time.sleep(0.5)

    # After completing the /getbalance requests, retrieve the server logs
    try:
        response = session.get(f'{base_url}/getlogs')
        print('Logs:')
        print(response.text)

    except requests.exceptions.RequestException as e:
        # Handle any exceptions that occur while requesting the logs
        print(f'/getlogs request failed: {e}')

if __name__ == '__main__':
    main()
