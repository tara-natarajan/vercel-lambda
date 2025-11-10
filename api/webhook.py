from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime
import pytz

from benchling_sdk.models.webhooks.v0 import CanvasCreatedWebhookV2, CanvasInteractionWebhookV2
from benchling_sdk.models import (
    ButtonUiBlock,
    ButtonUiBlockType,
    DropdownUiBlock,
    DropdownUiBlockType,
    MarkdownUiBlock,
    MarkdownUiBlockType,
    SectionUiBlock,
    SectionUiBlockType,
    TextInputUiBlock,
    TextInputUiBlockType,
)

# Constants
CANVAS_HEADER_SECTION = "canvas_header_section"
ADD_BUTTON_ID = "add_item"
SUBMIT_BUTTON_ID = "submit"

INSTRUCTIONS = """
Welcome to the Vercel Lambda Canvas!\n
Add items using the button below, then click submit when ready.\n
"""


def get_initial_canvas_blocks(num_plates: int = 1):
    """Generate initial canvas UI blocks"""
    return [
        SectionUiBlock(
            type=SectionUiBlockType.SECTION,
            id=CANVAS_HEADER_SECTION,
            children=[
                MarkdownUiBlock(
                    type=MarkdownUiBlockType.MARKDOWN,
                    id="instructions",
                    value=INSTRUCTIONS
                ),
                TextInputUiBlock(
                    type=TextInputUiBlockType.TEXT_INPUT,
                    id="plates_input",
                    label=f"Number of Plates (configured: {num_plates})",
                    enabled=True,
                    value=str(num_plates),
                ),
                ButtonUiBlock(
                    type=ButtonUiBlockType.BUTTON,
                    id=ADD_BUTTON_ID,
                    label="Add Item",
                    enabled=True,
                ),
                ButtonUiBlock(
                    type=ButtonUiBlockType.BUTTON,
                    id=SUBMIT_BUTTON_ID,
                    label="Submit",
                    enabled=True,
                ),
            ],
        ),
    ]


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
                response = self.handle_canvas_created(payload)
            elif webhook_type == 'v2.canvas.userInteracted':
                response = self.handle_user_interaction(payload)
            else:
                response = self.create_error_response(f'Unknown webhook type: {webhook_type}')
            
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
            'message': 'Webhook handler is running',
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def handle_canvas_created(self, payload):
        """Handle canvas.created webhook event"""
        # Extract canvas data
        canvas_id = payload.get('canvas', {}).get('id')
        feature_id = payload.get('feature', {}).get('id')
        app_id = payload.get('app', {}).get('id')
        
        print(f"Canvas initialized - ID: {canvas_id}, Feature: {feature_id}, App: {app_id}")
        
        # Get configuration for number of plates
        config = payload.get('configuration', {})
        num_plates = int(config.get('Number of Plates', 1))
        
        # Generate initial canvas blocks
        canvas_blocks = get_initial_canvas_blocks(num_plates)
        
        # Return section UI blocks
        return {
            'sections': [block.to_dict() for block in canvas_blocks]
        }
    
    def handle_user_interaction(self, payload):
        """Handle canvas.userInteracted webhook event"""
        # Extract interaction data
        canvas_id = payload.get('canvas', {}).get('id')
        user_id = payload.get('user', {}).get('id')
        button_id = payload.get('buttonId')
        
        print(f"Canvas interaction - Canvas: {canvas_id}, User: {user_id}, Button: {button_id}")
        
        # Handle different button interactions
        if button_id == ADD_BUTTON_ID:
            return self.handle_add_item(payload)
        elif button_id == SUBMIT_BUTTON_ID:
            return self.handle_submit(payload)
        else:
            return self.create_error_response(f'Unknown button ID: {button_id}')
    
    def handle_add_item(self, payload):
        """Handle add item button click"""
        # TODO: Add your logic for adding items
        print("Add item clicked")
        
        # Return updated UI blocks
        canvas_blocks = get_initial_canvas_blocks()
        return {
            'sections': [block.to_dict() for block in canvas_blocks]
        }
    
    def handle_submit(self, payload):
        """Handle submit button click"""
        # TODO: Add your submit logic here
        canvas_id = payload.get('canvas', {}).get('id')
        print(f"Submit clicked for canvas: {canvas_id}")
        
        # Return success message
        success_blocks = [
            SectionUiBlock(
                type=SectionUiBlockType.SECTION,
                id="success_section",
                children=[
                    MarkdownUiBlock(
                        type=MarkdownUiBlockType.MARKDOWN,
                        id="success_message",
                        value="✅ **Submitted successfully!**\n\nYour data has been processed."
                    ),
                ],
            ),
        ]
        
        return {
            'sections': [block.to_dict() for block in success_blocks]
        }
    
    def create_error_response(self, message):
        """Create error response with UI blocks"""
        error_blocks = [
            SectionUiBlock(
                type=SectionUiBlockType.SECTION,
                id="error_section",
                children=[
                    MarkdownUiBlock(
                        type=MarkdownUiBlockType.MARKDOWN,
                        id="error_message",
                        value=f"❌ **Error**\n\n{message}"
                    ),
                ],
            ),
        ]
        return {
            'sections': [block.to_dict() for block in error_blocks]
        }
    
    def send_error_response(self, status_code, message):
        """Send HTTP error response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        error_response = {
            'status': 'error',
            'message': message
        }
        self.wfile.write(json.dumps(error_response).encode('utf-8'))

