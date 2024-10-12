import http.server
import socketserver
import random
import time
import json
from datetime import datetime

LOGFILE = 'server.log'

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

class MyHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/getbalance':
            self.handle_getbalance()
        elif self.path == '/getlogs':
            self.handle_getlogs()
        else:
            self.send_error(404, "File not found")

    def handle_getbalance(self):
        # Get the client IP address
        client_ip = self.client_address[0]
        timestamp = datetime.now().isoformat()
        outcome = ''
        r = random.random()
        # 20% chance of timeout
        if r < 0.2:
            outcome = 'timeout'
            # Log the event
            self.log_event(timestamp, client_ip, outcome)
            time.sleep(15) 
            return
        # 20% chance of 403
        elif r < 0.4:
            outcome = '403'
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b'Forbidden')
        # 10% chance of 500
        elif r < 0.5:
            outcome = '500'
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'Internal Server Error')
        # 50% chance of 200
        else:
            outcome = '200'
            self.send_response(200)
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
            self.wfile.write(content.encode('utf-8'))

        # Log the event
        self.log_event(timestamp, client_ip, outcome)

    def handle_getlogs(self):
        # Read the log file and return data in JSON format
        try:
            with open(LOGFILE, 'r') as f:
                logs = [json.loads(line) for line in f]
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(logs).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'Error reading log file')
    #function to store the logs as json format in a file
    def log_event(self, timestamp, client_ip, outcome):
        with open(LOGFILE, 'a') as f:
            log_entry = {'timestamp': timestamp, 'client_ip': client_ip, 'outcome': outcome}
            f.write(json.dumps(log_entry) + '\n')
#Start a server on the desired port(Default is 8080)
def run(server_class=ThreadingHTTPServer, handler_class=MyHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting HTTP server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    from sys import argv
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
