from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime
from typing import List, Optional
import pytz

from benchling_sdk.benchling import Benchling
from benchling_sdk.auth.client_credentials_oauth2 import ClientCredentialsOAuth2
from benchling_sdk.apps.canvas.framework import CanvasBuilder
from benchling_sdk.models.webhooks.v0 import CanvasCreatedWebhookV2, CanvasInteractionWebhookV2
from benchling_sdk.models import (
    AppCanvasCreate,
    AppCanvasUpdate,
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
REMOVE_BUTTON_ID = "remove_item"
SUBMIT_BUTTON_ID = "submit"

INSTRUCTIONS = """
Welcome to the Vercel Lambda Canvas!\n
Add or remove items using the buttons below, then click submit when ready.\n
"""


def get_benchling_client() -> Benchling:
    """Initialize and return Benchling client"""
    base_url = os.environ.get('BENCHLING_URL', 'https://your-tenant.benchling.com')
    client_id = os.environ.get('BENCHLING_CLIENT_ID')
    client_secret = os.environ.get('BENCHLING_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        raise ValueError("BENCHLING_CLIENT_ID and BENCHLING_CLIENT_SECRET must be set in environment variables")
    
    token_url = f"{base_url}/api/v2/token"
    
    return Benchling(
        url=base_url,
        auth_method=ClientCredentialsOAuth2(client_id, client_secret, token_url),
    )


def get_initial_canvas_blocks(num_plates: int = 1) -> SectionUiBlock:
    """Generate initial canvas UI blocks"""
    return SectionUiBlock(
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
                id=REMOVE_BUTTON_ID,
                label="Remove Item",
                enabled=True,
            ),
            ButtonUiBlock(
                type=ButtonUiBlockType.BUTTON,
                id=SUBMIT_BUTTON_ID,
                label="Submit",
                enabled=True,
            ),
        ],
    )


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
        
        try:
            # Get configuration for number of plates
            config = payload.get('configuration', {})
            num_plates = int(config.get('Number of Plates', 1))
            
            # Initialize Benchling client
            benchling = get_benchling_client()
            
            # Build canvas using CanvasBuilder
            canvas_builder = CanvasBuilder(app_id, feature_id)
            canvas_builder.blocks.append(get_initial_canvas_blocks(num_plates))
            
            # Create canvas update from builder
            canvas_update = canvas_builder.to_update()
            
            # Update canvas in Benchling
            benchling.apps.update_canvas(canvas_id=canvas_id, canvas=canvas_update)
            
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
            
            # Initialize Benchling client
            benchling = get_benchling_client()
            
            # Build updated canvas
            canvas_builder = CanvasBuilder(app_id, feature_id)
            canvas_builder.blocks.append(get_initial_canvas_blocks())
            
            # Add success message
            canvas_builder.blocks.append(
                SectionUiBlock(
                    type=SectionUiBlockType.SECTION,
                    id="add_item_success",
                    children=[
                        MarkdownUiBlock(
                            type=MarkdownUiBlockType.MARKDOWN,
                            id="add_message",
                            value="✅ Item added successfully!"
                        ),
                    ],
                )
            )
            
            # Update canvas
            canvas_update = canvas_builder.to_update()
            benchling.apps.update_canvas(canvas_id=canvas_id, canvas=canvas_update)
            
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
            
            # Initialize Benchling client
            benchling = get_benchling_client()
            
            # Build updated canvas
            canvas_builder = CanvasBuilder(app_id, feature_id)
            canvas_builder.blocks.append(get_initial_canvas_blocks())
            
            # Add success message
            canvas_builder.blocks.append(
                SectionUiBlock(
                    type=SectionUiBlockType.SECTION,
                    id="remove_item_success",
                    children=[
                        MarkdownUiBlock(
                            type=MarkdownUiBlockType.MARKDOWN,
                            id="remove_message",
                            value="✅ Item removed successfully!"
                        ),
                    ],
                )
            )
            
            # Update canvas
            canvas_update = canvas_builder.to_update()
            benchling.apps.update_canvas(canvas_id=canvas_id, canvas=canvas_update)
            
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
            
            # Initialize Benchling client
            benchling = get_benchling_client()
            
            # Build success canvas
            canvas_builder = CanvasBuilder(app_id, feature_id)
            canvas_builder.blocks.append(
                SectionUiBlock(
                    type=SectionUiBlockType.SECTION,
                    id="success_section",
                    children=[
                        MarkdownUiBlock(
                            type=MarkdownUiBlockType.MARKDOWN,
                            id="success_message",
                            value="✅ **Submitted successfully!**\n\nYour data has been processed."
                        ),
                        ButtonUiBlock(
                            type=ButtonUiBlockType.BUTTON,
                            id="reset_button",
                            label="Start Over",
                            enabled=True,
                        ),
                    ],
                )
            )
            
            # Update canvas
            canvas_update = canvas_builder.to_update()
            benchling.apps.update_canvas(canvas_id=canvas_id, canvas=canvas_update)
            
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
            benchling = get_benchling_client()
            
            canvas_builder = CanvasBuilder(app_id, feature_id)
            canvas_builder.blocks.append(
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
                )
            )
            
            canvas_update = canvas_builder.to_update()
            benchling.apps.update_canvas(canvas_id=canvas_id, canvas=canvas_update)
            
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
        self.end_headers()
        error_response = {
            'status': 'error',
            'message': message
        }
        self.wfile.write(json.dumps(error_response).encode('utf-8'))

