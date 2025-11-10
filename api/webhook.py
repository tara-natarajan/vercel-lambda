"""Benchling Canvas webhook handler for Vercel.

Uses BaseHTTPRequestHandler as per Vercel Python runtime documentation.
"""
from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime
import pytz

from benchling_sdk.models.webhooks.v0 import CanvasCreatedWebhookV2, CanvasInteractionWebhookV2

# Import helper modules
from benchling_client import get_benchling_client
from canvas_blocks import (
    ADD_BUTTON_ID,
    REMOVE_BUTTON_ID,
    SUBMIT_BUTTON_ID,
    get_initial_canvas_blocks,
    create_success_section,
    create_error_section,
    create_submit_success_section,
)
from canvas_updater import update_canvas


class handler(BaseHTTPRequestHandler):
    
    def do_POST(self):
        """Handle incoming webhook POST requests"""
        try:
            # Read the request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            # Parse JSON payload
            payload = json.loads(body.decode('utf-8'))
            
            # Determine webhook type and route to handler
            webhook_type = payload.get('type', 'unknown')
            
            if webhook_type == 'v2.canvas.created':
                response_data = self.handle_canvas_created(payload)
            elif webhook_type == 'v2.canvas.userInteracted':
                response_data = self.handle_user_interaction(payload)
            else:
                response_data = {'status': 'error', 'message': f'Unknown webhook type: {webhook_type}'}
            
            # Send successful response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
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
            'message': 'Webhook handler is running',
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def handle_canvas_created(self, payload):
        """Handle canvas.created webhook event"""
        # Extract canvas data
        canvas_id = payload.get('canvas', {}).get('id')
        feature_id = payload.get('feature', {}).get('id')
        app_id = payload.get('app', {}).get('id')
        
        print(f"Canvas initialized - ID: {canvas_id}, Feature: {feature_id}, App: {app_id}")
        
        try:
            # Get configuration for number of plates
            config = payload.get('configuration', {})
            num_plates = int(config.get('Number of Plates', 1))
            
            # Update canvas with initial blocks
            update_canvas(
                canvas_id=canvas_id,
                app_id=app_id,
                feature_id=feature_id,
                blocks=[get_initial_canvas_blocks(num_plates)]
            )
            
            print(f"Canvas {canvas_id} created successfully")
            
            return {
                'status': 'success',
                'canvas_id': canvas_id,
                'message': 'Canvas created successfully'
            }
        except Exception as e:
            print(f"Error creating canvas: {str(e)}")
            raise
    
    def handle_user_interaction(self, payload):
        """Handle canvas.userInteracted webhook event"""
        # Extract interaction data
        canvas_id = payload.get('canvas', {}).get('id')
        user_id = payload.get('user', {}).get('id')
        button_id = payload.get('buttonId')
        app_id = payload.get('app', {}).get('id')
        feature_id = payload.get('feature', {}).get('id')
        
        print(f"Canvas interaction - Canvas: {canvas_id}, User: {user_id}, Button: {button_id}")
        
        # Handle different button interactions
        if button_id == ADD_BUTTON_ID:
            return self.handle_add_item(canvas_id, app_id, feature_id, payload)
        elif button_id == REMOVE_BUTTON_ID:
            return self.handle_remove_item(canvas_id, app_id, feature_id, payload)
        elif button_id == SUBMIT_BUTTON_ID:
            return self.handle_submit(canvas_id, app_id, feature_id, payload)
        else:
            return self.update_canvas_with_error(canvas_id, app_id, feature_id, f'Unknown button ID: {button_id}')
    
    def handle_add_item(self, canvas_id: str, app_id: str, feature_id: str, payload: dict):
        """Handle add item button click"""
        print(f"Add item clicked for canvas: {canvas_id}")
        
        try:
            # TODO: Add your logic for adding items
            # For now, just refresh the canvas with current state
            
            # Update canvas with initial blocks and success message
            update_canvas(
                canvas_id=canvas_id,
                app_id=app_id,
                feature_id=feature_id,
                blocks=[
                    get_initial_canvas_blocks(),
                    create_success_section("add_item_success", "Item added successfully!")
                ]
            )
            
            return {
                'status': 'success',
                'message': 'Item added'
            }
        except Exception as e:
            print(f"Error adding item: {str(e)}")
            return self.update_canvas_with_error(canvas_id, app_id, feature_id, str(e))
    
    def handle_remove_item(self, canvas_id: str, app_id: str, feature_id: str, payload: dict):
        """Handle remove item button click"""
        print(f"Remove item clicked for canvas: {canvas_id}")
        
        try:
            # TODO: Add your logic for removing items
            
            # Update canvas with initial blocks and success message
            update_canvas(
                canvas_id=canvas_id,
                app_id=app_id,
                feature_id=feature_id,
                blocks=[
                    get_initial_canvas_blocks(),
                    create_success_section("remove_item_success", "Item removed successfully!")
                ]
            )
            
            return {
                'status': 'success',
                'message': 'Item removed'
            }
        except Exception as e:
            print(f"Error removing item: {str(e)}")
            return self.update_canvas_with_error(canvas_id, app_id, feature_id, str(e))
    
    def handle_submit(self, canvas_id: str, app_id: str, feature_id: str, payload: dict):
        """Handle submit button click"""
        print(f"Submit clicked for canvas: {canvas_id}")
        
        try:
            # TODO: Add your submit logic here
            # Extract form data, process it, etc.
            
            # Update canvas with success message
            update_canvas(
                canvas_id=canvas_id,
                app_id=app_id,
                feature_id=feature_id,
                blocks=[create_submit_success_section()]
            )
            
            return {
                'status': 'success',
                'message': 'Submitted successfully'
            }
        except Exception as e:
            print(f"Error submitting: {str(e)}")
            return self.update_canvas_with_error(canvas_id, app_id, feature_id, str(e))
    
    def update_canvas_with_error(self, canvas_id: str, app_id: str, feature_id: str, message: str):
        """Update canvas with error message"""
        try:
            update_canvas(
                canvas_id=canvas_id,
                app_id=app_id,
                feature_id=feature_id,
                blocks=[create_error_section("error_section", message)]
            )
            
            return {
                'status': 'error',
                'message': message
            }
        except Exception as e:
            print(f"Error updating canvas with error message: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to update canvas: {message}'
            }
    
    def send_error_response(self, status_code, message):
        """Send HTTP error response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        error_response = {
            'status': 'error',
            'message': message
        }
        self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to customize logging"""
        print(f"{self.address_string()} - {format % args}")

