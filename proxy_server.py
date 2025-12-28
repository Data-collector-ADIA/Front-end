import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import logging

import grpc

# Add parent directory to path to import generated protobuf files
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import generated protobuf files
try:
    import backend_service_pb2
    import backend_service_pb2_grpc
    import database_service_pb2
    import database_service_pb2_grpc
except ImportError:
    print("ERROR: Protobuf files not found or incomplete. Please run: python shared/generate_protos.py")
    sys.exit(1)

# Configuration
BACKEND_SERVICE_HOST = os.getenv("BACKEND_SERVICE_HOST", "localhost")
BACKEND_SERVICE_PORT = int(os.getenv("BACKEND_SERVICE_PORT", "50050"))
DATABASE_SERVICE_HOST = os.getenv("DATABASE_SERVICE_HOST", "localhost")
DATABASE_SERVICE_PORT = int(os.getenv("DATABASE_SERVICE_PORT", "50052"))
FRONTEND_PORT = int(os.getenv("FRONTEND_SERVICE_PORT", "8501"))

# Global gRPC channels for reuse
_backend_channel = None
_database_channel = None

def get_backend_stub():
    global _backend_channel
    if _backend_channel is None:
        # Use a longer timeout for the channel
        _backend_channel = grpc.insecure_channel(f"{BACKEND_SERVICE_HOST}:{BACKEND_SERVICE_PORT}")
    return backend_service_pb2_grpc.BackendServiceStub(_backend_channel)

def get_database_stub():
    global _database_channel
    if _database_channel is None:
        _database_channel = grpc.insecure_channel(f"{DATABASE_SERVICE_HOST}:{DATABASE_SERVICE_PORT}")
    return database_service_pb2_grpc.DatabaseServiceStub(_database_channel)


class ProxyHandler(BaseHTTPRequestHandler):
    """HTTP request handler that proxies to gRPC services"""
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Serve static files
        if path == '/' or path == '/index.html':
            self.serve_static_file('index.html')
        elif path.startswith('/'):
            # Try to serve other static files
            file_path = path.lstrip('/')
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self.serve_static_file(file_path)
            else:
                # Handle API endpoints
                self.handle_api_get(path, parse_qs(parsed_path.query))
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/tasks/start':
            self.handle_start_task()
        else:
            self.send_error(404, "Not Found")
    
    def handle_api_get(self, path, query_params):
        """Handle GET API requests"""
        if path == '/tasks':
            # List tasks
            limit = int(query_params.get('limit', [50])[0])
            offset = int(query_params.get('offset', [0])[0])
            user_id = query_params.get('user_id', [''])[0]
            self.list_tasks(limit, offset, user_id)
        elif path.startswith('/tasks/') and path.endswith('/history'):
            # Get task history
            task_id = path.split('/')[2]
            self.get_task_history(task_id)
        elif path.startswith('/tasks/') and path.endswith('/status'):
            # Get task status
            task_id = path.split('/')[2]
            self.get_task_status(task_id)
        else:
            self.send_error(404, "Not Found")
    
    def handle_start_task(self):
        """Handle task creation request"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Connect to backend service
            stub = get_backend_stub()
            
            # Create gRPC request
            request = backend_service_pb2.StartTaskRequest(
                task_prompt=data.get('task_prompt', ''),
                max_steps=data.get('max_steps', 15),
                user_id=data.get('user_id', 'default'),
                browser_name=data.get('browser_name', 'chrome'),
                browser_port=data.get('browser_port', 9999)
            )
            
            # Call gRPC service
            response = stub.StartTask(request)
            
            # Convert to JSON response
            result = {
                'success': response.success,
                'task_id': response.task_id,
                'message': response.message
            }
            
            self.send_json_response(result)
            
        except grpc.RpcError as e:
            self.send_error_response(500, f"gRPC Error: {e.code()} - {e.details()}")
        except Exception as e:
            self.send_error_response(500, f"Error: {str(e)}")
    
    def list_tasks(self, limit, offset, user_id):
        """List tasks from database service"""
        try:
            stub = get_database_stub()
            
            request = database_service_pb2.ListTasksRequest(
                user_id=user_id if user_id else "",
                limit=limit,
                offset=offset
            )
            
            response = stub.ListTasks(request)
            
            # Convert tasks to JSON format
            tasks = []
            for task in response.tasks:
                tasks.append({
                    'task_id': task.task_id,
                    'task_prompt': task.task_prompt,
                    'max_steps': task.max_steps,
                    'status': task.status,
                    'user_id': task.user_id,
                    'created_at': task.created_at,
                    'updated_at': task.updated_at,
                    'final_result': task.final_result
                })
            
            self.send_json_response(tasks)
            
        except grpc.RpcError as e:
            self.send_error_response(500, f"gRPC Error: {e.code()} - {e.details()}")
        except Exception as e:
            self.send_error_response(500, f"Error: {str(e)}")
    
    def get_task_history(self, task_id):
        """Get task history from database service"""
        try:
            stub = get_database_stub()
            
            request = database_service_pb2.GetTaskHistoryRequest(task_id=task_id)
            response = stub.GetTaskHistory(request)
            
            if not response.success:
                self.send_error_response(404, "Task not found")
                return
            
            # Convert outputs to JSON format
            outputs = []
            for output in response.outputs:
                outputs.append({
                    'output_id': output.output_id,
                    'task_id': output.task_id,
                    'output_type': output.output_type,
                    'step_data': output.step_data,
                    'step_number': output.step_number,
                    'timestamp': output.timestamp
                })
            
            self.send_json_response(outputs)
            
        except grpc.RpcError as e:
            self.send_error_response(500, f"gRPC Error: {e.code()} - {e.details()}")
        except Exception as e:
            self.send_error_response(500, f"Error: {str(e)}")
    
    def get_task_status(self, task_id):
        """Get task status from backend service"""
        try:
            stub = get_backend_stub()
            
            request = backend_service_pb2.GetTaskStatusRequest(task_id=task_id)
            response = stub.GetTaskStatus(request)
            
            result = {
                'success': response.success,
                'status': response.status,
                'message': response.message
            }
            
            self.send_json_response(result)
            
        except grpc.RpcError as e:
            self.send_error_response(500, f"gRPC Error: {e.code()} - {e.details()}")
        except Exception as e:
            self.send_error_response(500, f"Error: {str(e)}")
    
    def serve_static_file(self, filename):
        """Serve static files"""
        try:
            if filename == 'index.html' or filename == '/':
                filepath = 'index.html'
            else:
                filepath = filename
            
            if not os.path.exists(filepath):
                self.send_error(404, "File not found")
                return
            
            with open(filepath, 'rb') as f:
                content = f.read()
            
            # Determine content type
            if filename.endswith('.html'):
                content_type = 'text/html'
            elif filename.endswith('.css'):
                content_type = 'text/css'
            elif filename.endswith('.js'):
                content_type = 'application/javascript'
            else:
                content_type = 'application/octet-stream'
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_cors_headers()
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            self.send_error(500, f"Error serving file: {str(e)}")
    
    def send_json_response(self, data):
        """Send JSON response"""
        json_data = json.dumps(data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.send_header('Content-Length', str(len(json_data)))
        self.end_headers()
        self.wfile.write(json_data)
    
    def send_error_response(self, code, message):
        """Send error response"""
        error_data = {'error': message}
        json_data = json.dumps(error_data).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.send_header('Content-Length', str(len(json_data)))
        self.end_headers()
        self.wfile.write(json_data)
    
    def send_cors_headers(self):
        """Send CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def log_message(self, format, *args):
        """Override to reduce log noise"""
        pass


def serve(port: int = 8501):
    """Start the proxy server"""
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, ProxyHandler)
    print(f"Frontend proxy server running on http://localhost:{port}")
    print(f"Backend gRPC: {BACKEND_SERVICE_HOST}:{BACKEND_SERVICE_PORT}")
    print(f"Database gRPC: {DATABASE_SERVICE_HOST}:{DATABASE_SERVICE_PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down frontend proxy server...")
        
        # Close global channels
        global _backend_channel, _database_channel
        if _backend_channel:
            _backend_channel.close()
        if _database_channel:
            _database_channel.close()
            
        httpd.shutdown()


if __name__ == "__main__":
    serve(FRONTEND_PORT)
