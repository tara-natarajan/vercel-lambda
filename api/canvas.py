"""Benchling Canvas handler for Vercel.

Handles Benchling Canvas events sent via app signals.
Uses BaseHTTPRequestHandler as per Vercel Python runtime documentation.
"""
from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime

# Try to import dependencies with error handling
try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    print("Warning: pytz not available")
    PYTZ_AVAILABLE = False

try:
    from benchling_sdk.models.webhooks.v0 import CanvasCreatedWebhookV2, CanvasInteractionWebhookV2
    BENCHLING_SDK_AVAILABLE = True
except ImportError as e:
    print(f"Warning: benchling_sdk not available: {e}")
    BENCHLING_SDK_AVAILABLE = False

# Constants (fallback if imports fail)
ADD_BUTTON_ID = "add_item"
REMOVE_BUTTON_ID = "remove_item"
SUBMIT_BUTTON_ID = "submit"
CANVAS_HEADER_SECTION = "canvas_header_section"
HELPERS_AVAILABLE = True  # We'll check this later

INSTRUCTIONS = """
Welcome to the Vercel Lambda Canvas!\n
Add or remove items using the buttons below, then click submit when ready.\n
"""


# Helper functions inlined to avoid import issues
def get_benchling_client():
    """Initialize Benchling client."""
    import os
    from benchling_sdk.benchling import Benchling
    from benchling_sdk.auth.client_credentials_oauth2 import ClientCredentialsOAuth2
    
    base_url = os.environ.get('BENCHLING_URL')
    client_id = os.environ.get('BENCHLING_CLIENT_ID')
    client_secret = os.environ.get('BENCHLING_CLIENT_SECRET')
    
    if not base_url:
        raise ValueError("BENCHLING_URL must be set in environment variables")
    if not client_id or not client_secret:
        raise ValueError("BENCHLING_CLIENT_ID and BENCHLING_CLIENT_SECRET must be set in environment variables")
    
    token_url = f"{base_url}/api/v2/token"
    
    return Benchling(
        url=base_url,
        auth_method=ClientCredentialsOAuth2(client_id, client_secret, token_url),
    )


def get_initial_canvas_blocks(num_plates: str = "1"):
    """Generate initial canvas UI blocks showing Number of Plates."""
    from benchling_sdk.models import (
        MarkdownUiBlock,
        MarkdownUiBlockType,
        SectionUiBlock,
        SectionUiBlockType,
    )
    
    return SectionUiBlock(
        type=SectionUiBlockType.SECTION,
        id=CANVAS_HEADER_SECTION,
        children=[
            MarkdownUiBlock(
                type=MarkdownUiBlockType.MARKDOWN,
                id="plates_display",
                value=f"**Number of Plates:** {num_plates}"
            ),
        ],
    )


def create_success_section(section_id: str, message: str):
    """Create a success message section."""
    from benchling_sdk.models import (
        MarkdownUiBlock,
        MarkdownUiBlockType,
        SectionUiBlock,
        SectionUiBlockType,
    )
    
    return SectionUiBlock(
        type=SectionUiBlockType.SECTION,
        id=section_id,
        children=[
            MarkdownUiBlock(
                type=MarkdownUiBlockType.MARKDOWN,
                id=f"{section_id}_message",
                value=f"✅ {message}"
            ),
        ],
    )


def create_error_section(section_id: str, message: str):
    """Create an error message section."""
    from benchling_sdk.models import (
        MarkdownUiBlock,
        MarkdownUiBlockType,
        SectionUiBlock,
        SectionUiBlockType,
    )
    
    return SectionUiBlock(
        type=SectionUiBlockType.SECTION,
        id=section_id,
        children=[
            MarkdownUiBlock(
                type=MarkdownUiBlockType.MARKDOWN,
                id=f"{section_id}_message",
                value=f"❌ **Error**\n\n{message}"
            ),
        ],
    )


def create_submit_success_section():
    """Create the submit success section with reset button."""
    from benchling_sdk.models import (
        ButtonUiBlock,
        ButtonUiBlockType,
        MarkdownUiBlock,
        MarkdownUiBlockType,
        SectionUiBlock,
        SectionUiBlockType,
    )
    
    return SectionUiBlock(
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
                text="Start Over",
                enabled=True,
            ),
        ],
    )


def update_canvas(canvas_id: str, app_id: str, feature_id: str, blocks):
    """Update a canvas with new UI blocks."""
    from benchling_api_client.v2.stable.models import AppCanvasUpdate
    
    print(f"update_canvas called with canvas_id={canvas_id}, app_id={app_id}, feature_id={feature_id}")
    print(f"Number of blocks: {len(blocks)}")
    
    try:
        print("Getting Benchling client...")
        benchling = get_benchling_client()
        print("✓ Benchling client created")
        
        print(f"Creating canvas update with {len(blocks)} blocks...")
        for i, block in enumerate(blocks):
            print(f"Block {i}: {type(block).__name__} with id={getattr(block, 'id', 'no-id')}")
        
        # Create the update object directly with blocks
        canvas_update = AppCanvasUpdate(
            blocks=blocks
        )
        print(f"✓ Canvas update created: {type(canvas_update)}")
        
        print(f"Calling Benchling API to update canvas {canvas_id}...")
        result = benchling.apps.update_canvas(canvas_id=canvas_id, canvas=canvas_update)
        print(f"✓ Canvas updated successfully: {result}")
        
    except Exception as e:
        print(f"ERROR in update_canvas: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Error repr: {repr(e)}")
        import traceback
        traceback.print_exc()
        raise


class handler(BaseHTTPRequestHandler):
    
    def do_POST(self):
        """Handle incoming webhook POST requests"""
        print("=" * 80)
        print("POST request received")
        print(f"Path: {self.path}")
        print(f"Headers: {dict(self.headers)}")
        
        try:
            # Read the request body
            content_length = int(self.headers.get('Content-Length', 0))
            print(f"Content-Length: {content_length}")
            
            body = self.rfile.read(content_length)
            body_str = body.decode('utf-8')
            print(f"Raw body: {body_str}")
            
            # Parse JSON payload
            payload = json.loads(body_str)
            print(f"Parsed payload: {json.dumps(payload, indent=2)}")
            
            # Extract message from payload (new format)
            message = payload.get('message', {})
            webhook_type = message.get('type', payload.get('type', 'unknown'))
            print(f"Webhook type: {webhook_type}")
            
            if webhook_type == 'v2.canvas.created':
                print("Routing to handle_canvas_created")
                response_data = self.handle_canvas_created(payload)
            elif webhook_type == 'v2.canvas.userInteracted':
                print("Routing to handle_user_interaction")
                response_data = self.handle_user_interaction(payload)
            else:
                print(f"Unknown webhook type: {webhook_type}")
                response_data = {'status': 'error', 'message': f'Unknown webhook type: {webhook_type}'}
            
            print(f"Response: {json.dumps(response_data, indent=2)}")
            print("=" * 80)
            
            # Send successful response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {str(e)}")
            print("=" * 80)
            self.send_error_response(400, f'Invalid JSON: {str(e)}')
        except Exception as e:
            error_msg = str(e) if str(e) else f'{type(e).__name__}: {repr(e)}'
            print(f"Exception occurred: {error_msg}")
            import traceback
            traceback.print_exc()
            print("=" * 80)
            self.send_error_response(500, f'Server error: {error_msg}')
    
    def do_GET(self):
        """Health check endpoint"""
        try:
            print("=" * 80)
            print("GET request received")
            print(f"Path: {self.path}")
            print(f"Headers: {dict(self.headers)}")
            
            # Check import status
            print(f"PYTZ_AVAILABLE: {PYTZ_AVAILABLE}")
            print(f"BENCHLING_SDK_AVAILABLE: {BENCHLING_SDK_AVAILABLE}")
            print(f"HELPERS_AVAILABLE: {HELPERS_AVAILABLE}")
            print("=" * 80)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            if PYTZ_AVAILABLE:
                timestamp = datetime.now(pytz.UTC).isoformat()
            else:
                timestamp = datetime.utcnow().isoformat()
            
            response = {
                'status': 'ok',
                'message': 'Webhook handler is running',
                'timestamp': timestamp,
                'dependencies': {
                    'pytz': PYTZ_AVAILABLE,
                    'benchling_sdk': BENCHLING_SDK_AVAILABLE,
                    'helpers': HELPERS_AVAILABLE
                }
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
        except Exception as e:
            print(f"Error in do_GET: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_error_response(500, f'GET error: {str(e)}')
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        print("=" * 80)
        print("OPTIONS request received")
        print(f"Path: {self.path}")
        print(f"Headers: {dict(self.headers)}")
        print("=" * 80)
        
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def handle_canvas_created(self, payload):
        """Handle canvas.created webhook event - simply display Number of Plates"""
        import os
        
        # Extract canvas data - support both old and new format
        message = payload.get('message', {})
        canvas_id = message.get('canvasId') or payload.get('canvas', {}).get('id')
        feature_id = message.get('featureId') or payload.get('feature', {}).get('id')
        app_id = payload.get('app', {}).get('id')
        
        print(f"Canvas initialized - ID: {canvas_id}, Feature: {feature_id}, App: {app_id}")
        
        try:
            # Get configuration for number of plates
            config = payload.get('configuration', {})
            num_plates = config.get('Number of Plates', '1')
            
            print(f"Number of Plates from config: {num_plates}")
            
            # Check if environment variables are set
            benchling_url = os.environ.get('BENCHLING_URL')
            benchling_client_id = os.environ.get('BENCHLING_CLIENT_ID')
            benchling_client_secret = os.environ.get('BENCHLING_CLIENT_SECRET')
            
            if not benchling_url or not benchling_client_id or not benchling_client_secret:
                print("WARNING: Benchling environment variables not set - skipping API call")
                print("To enable Benchling API, set: BENCHLING_URL, BENCHLING_CLIENT_ID, BENCHLING_CLIENT_SECRET")
                return {
                    'status': 'success',
                    'canvas_id': canvas_id,
                    'message': 'Webhook received (Benchling API not configured)',
                    'num_plates': num_plates,
                    'note': 'Set environment variables to enable Benchling API calls'
                }
            
            # Update canvas with simple display block
            print("Updating canvas with standard blocks...")
            update_canvas(
                canvas_id=canvas_id,
                app_id=app_id,
                feature_id=feature_id,
                blocks=[get_initial_canvas_blocks(num_plates)]
            )
            
            print(f"Canvas {canvas_id} updated successfully")
            
            return {
                'status': 'success',
                'canvas_id': canvas_id,
                'message': 'Canvas created successfully',
                'num_plates': num_plates
            }
        except Exception as e:
            error_msg = str(e) if str(e) else f'{type(e).__name__}: {repr(e)}'
            print(f"Error creating canvas: {error_msg}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            raise
    
    def handle_user_interaction(self, payload):
        """Handle canvas.userInteracted webhook event - just return standard blocks"""
        import os
        
        # Extract interaction data - support both old and new format
        message = payload.get('message', {})
        canvas_id = message.get('canvasId') or payload.get('canvas', {}).get('id')
        user_id = message.get('userId') or payload.get('user', {}).get('id')
        button_id = message.get('buttonId') or payload.get('buttonId')
        app_id = payload.get('app', {}).get('id')
        feature_id = message.get('featureId') or payload.get('feature', {}).get('id')
        
        print(f"Canvas interaction - Canvas: {canvas_id}, User: {user_id}, Button: {button_id}")
        
        # Get configuration
        config = payload.get('configuration', {})
        num_plates = config.get('Number of Plates', '1')
        
        print(f"Number of Plates from config: {num_plates}")
        
        # Check if environment variables are set
        benchling_url = os.environ.get('BENCHLING_URL')
        benchling_client_id = os.environ.get('BENCHLING_CLIENT_ID')
        benchling_client_secret = os.environ.get('BENCHLING_CLIENT_SECRET')
        
        if not benchling_url or not benchling_client_id or not benchling_client_secret:
            print("WARNING: Benchling environment variables not set - skipping API call")
            return {
                'status': 'success',
                'message': 'User interaction received (Benchling API not configured)',
                'button_id': button_id,
                'num_plates': num_plates,
                'note': 'Set environment variables to enable Benchling API calls'
            }
        
        # Update canvas with standard blocks
        try:
            print("Updating canvas with standard blocks...")
            update_canvas(
                canvas_id=canvas_id,
                app_id=app_id,
                feature_id=feature_id,
                blocks=[get_initial_canvas_blocks(num_plates)]
            )
            
            return {
                'status': 'success',
                'message': 'Interaction received',
                'button_id': button_id
            }
        except Exception as e:
            error_msg = str(e) if str(e) else f'{type(e).__name__}: {repr(e)}'
            print(f"Error handling interaction: {error_msg}")
            import traceback
            traceback.print_exc()
            raise
    
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

