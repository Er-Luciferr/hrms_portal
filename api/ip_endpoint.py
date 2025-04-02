import json
from pathlib import Path
import threading
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

class IPReportHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/ip-report':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                # Parse JSON data
                data = json.loads(post_data.decode('utf-8'))
                private_ip = data.get("private_ip")
                
                if private_ip:
                    # Store the IP in a file for persistence
                    ip_data_path = Path("config/reported_ips.json")
                    
                    # Create directory if it doesn't exist
                    if not ip_data_path.parent.exists():
                        ip_data_path.parent.mkdir(parents=True)
                    
                    # Load existing data or create new
                    if ip_data_path.exists():
                        try:
                            with open(ip_data_path, "r") as f:
                                ip_data = json.load(f)
                        except:
                            ip_data = {"reported_ips": []}
                    else:
                        ip_data = {"reported_ips": []}
                    
                    # Add the new IP if not already present
                    if private_ip not in ip_data["reported_ips"]:
                        ip_data["reported_ips"].append(private_ip)
                        
                        # Save the updated data
                        with open(ip_data_path, "w") as f:
                            json.dump(ip_data, f, indent=4)
                    
                    # Send successful response
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = json.dumps({"status": "success", "received_ip": private_ip})
                    self.wfile.write(response.encode('utf-8'))
                else:
                    # Send error response - no IP provided
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = json.dumps({"status": "error", "message": "No private_ip provided"})
                    self.wfile.write(response.encode('utf-8'))
            except Exception as e:
                # Send error response - processing error
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = json.dumps({"status": "error", "message": str(e)})
                self.wfile.write(response.encode('utf-8'))
        else:
            # Path not found
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({"status": "error", "message": "Not found"})
            self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        # Suppress or customize logging if needed
        if os.environ.get("DEBUG", "false").lower() == "true":
            print("[IP Server]", format % args)

def run_http_server():
    # Get the port from environment or use default
    port = int(os.environ.get("IP_SERVER_PORT", 5000))
    server_address = ('', port)
    httpd = HTTPServer(server_address, IPReportHandler)
    print(f"HTTP API server started on port {port}")
    httpd.serve_forever()

# Start HTTP server in a separate thread
def start_server():
    server_thread = threading.Thread(target=run_http_server, daemon=True)
    server_thread.start()
    print(f"IP reporting server started on port {os.environ.get('IP_SERVER_PORT', 5000)}")
    return server_thread 