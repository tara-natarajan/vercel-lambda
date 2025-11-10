from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    
    def do_POST(self):
        """Handle incoming webhook POST requests"""
        try:
            # Read the request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            # Parse JSON payload
            payload = json.loads(body.decode('utf-8'))
            
            # Get event type
            event_type = payload.get('type', 'unknown')
            
            # Route to appropriate handler
            if event_type == 'v2.canvas.created':
                response = self.handle_canvas_created(payload)
            elif event_type == 'v2.canvas.userInteracted':
                response = self.handle_user_interaction(payload)
            else:
                response = {
                    'status': 'error',
                    'message': f'Unknown event type: {event_type}'
                }
            
            # Send successful response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except json.JSONDecodeError as e:
            self.send_error_response(400, f'Invalid JSON: {str(e)}')
        except Exception as e:
            self.send_error_response(500, f'Server error: {str(e)}')
    
    def do_GET(self):
        """Health check endpoint"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = {
            'status': 'ok',
            'message': 'Webhook handler is running'
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def handle_canvas_created(self, payload):
        """Handle canvas.created webhook event"""
        # Extract canvas data
        canvas_id = payload.get('canvas', {}).get('id')
        user_id = payload.get('user', {}).get('id')
        
        # TODO: Add your canvas creation logic here
        print(f"Canvas created - ID: {canvas_id}, User: {user_id}")
        
        # Return response that will be sent back
        return {
            'status': 'success',
            'event': 'canvas.created',
            'canvas_id': canvas_id,
            'message': 'Canvas created successfully'
        }
    
    def handle_user_interaction(self, payload):
        """Handle canvas.userInteracted webhook event"""
        # Extract interaction data
        canvas_id = payload.get('canvas', {}).get('id')
        user_id = payload.get('user', {}).get('id')
        interaction = payload.get('interaction', {})
        
        # TODO: Add your interaction logic here
        print(f"User interaction - Canvas: {canvas_id}, User: {user_id}")
        print(f"Interaction data: {interaction}")
        
        # Return response
        return {
            'status': 'success',
            'event': 'canvas.userInteracted',
            'canvas_id': canvas_id,
            'message': 'Interaction processed successfully'
        }
    
    def send_error_response(self, status_code, message):
        """Send error response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        error_response = {
            'status': 'error',
            'message': message
        }
        self.wfile.write(json.dumps(error_response).encode('utf-8'))

