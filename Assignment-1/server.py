import http.server        
import socketserver       
import random             
import time               
import json               
from datetime import datetime   


LOGFILE = 'server.log'

# Define a multithreaded HTTP server class
class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    # Inherits from ThreadingMixIn to handle each request in a separate thread
    pass

# Define a request handler class to handle HTTP requests
class MyHandler(http.server.BaseHTTPRequestHandler):

    # Override the GET request handler
    def do_GET(self):
        # Check the requested path and route accordingly
        if self.path == '/getbalance':
            # Handle the /getbalance endpoint
            self.handle_getbalance()
        elif self.path == '/getlogs':
            # Handle the /getlogs endpoint
            self.handle_getlogs()
        else:
            # If the path is unrecognized, send a 404 error response
            self.send_error(404, "File not found")

    # Method to handle the /getbalance endpoint
    def handle_getbalance(self):
        # Obtain the client's IP address
        client_ip = self.client_address[0]
        # Get the current timestamp in ISO format
        timestamp = datetime.now().isoformat()
        outcome = ''
        # Generate a random number between 0 and 1 to determine the outcome
        r = random.random()
        # 20% chance to simulate a timeout
        if r < 0.2:
            outcome = 'timeout'
            # Log the event before simulating the timeout
            self.log_event(timestamp, client_ip, outcome)
            # Sleep for 15 seconds to simulate a server timeout
            time.sleep(15) 
            # Do not send any response, effectively causing a timeout on the client side
            return
        # 20% chance to return a 403 Forbidden status code
        elif r < 0.4:
            outcome = '403'
            # Send a 403 Forbidden response to the client
            self.send_response(403)
            self.end_headers()
            # Write 'Forbidden' message to the response body
            self.wfile.write(b'Forbidden')
        # 10% chance to return a 500 Internal Server Error status code
        elif r < 0.5:
            outcome = '500'
            # Send a 500 Internal Server Error response to the client
            self.send_response(500)
            self.end_headers()
            # Write 'Internal Server Error' message to the response body
            self.wfile.write(b'Internal Server Error')
        # 50% chance to return a 200 OK status code with fake content
        else:
            outcome = '200'
            # Send a 200 OK response to the client
            self.send_response(200)
            # Specify that the content type of the response is HTML
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            content = '''
            <html>
            <head><title>Balance</title></head>
            <body>
            <h1>Your Balance</h1>
            <p>$9999</p>
            </body>
            </html>
            '''
            # Write the HTML content to the response body
            self.wfile.write(content.encode('utf-8'))

        # Log the event after handling the request
        self.log_event(timestamp, client_ip, outcome)

    # Method to handle the /getlogs endpoint
    def handle_getlogs(self):
        # Attempt to read the log file and send its contents to the client
        try:
            with open(LOGFILE, 'r') as f:
                logs = [json.loads(line) for line in f]
            # Send a 200 OK response to the client
            self.send_response(200)
            # Specify that the content type of the response is JSON
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            # Write the logs as a JSON array to the response body
            self.wfile.write(json.dumps(logs).encode('utf-8'))
        except Exception as e:
            # If an error occurs send a 500 Internal Server Error response
            self.send_response(500)
            self.end_headers()
            # Write an error message to the response body
            self.wfile.write(b'Error reading log file')

    # Function to log events by appending them to the log file in JSON format
    def log_event(self, timestamp, client_ip, outcome):
        with open(LOGFILE, 'a') as f:
            # Create a dictionary representing the log entry
            log_entry = {'timestamp': timestamp, 'client_ip': client_ip, 'outcome': outcome}
            # Write the JSON representation of the log entry to the file, followed by a newline
            f.write(json.dumps(log_entry) + '\n')

# Function to start the HTTP server on the desired port (default is 8080)
def run(server_class=ThreadingHTTPServer, handler_class=MyHandler, port=8080):
    # Create the server address, binding to all available network interfaces
    server_address = ('', port)
    # Create an instance of the HTTP server with the specified handler
    httpd = server_class(server_address, handler_class)
    print(f'Starting HTTP server on port {port}...')
    # Start serving requests indefinitely
    httpd.serve_forever()

if __name__ == '__main__':
    from sys import argv
    # If a port number is provided as a command-line argument
    if len(argv) == 2:
        # Run the server on the specified port
        run(port=int(argv[1]))
    else:
        # Otherwise, run the server on the default port (8080)
        run()
