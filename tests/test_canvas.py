"""Unit tests for canvas webhook handler logic."""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path to import canvas module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.canvas import (
    get_initial_canvas_blocks,
    CANVAS_HEADER_SECTION,
)


class TestGetInitialCanvasBlocks:
    """Test the get_initial_canvas_blocks function."""
    
    def test_returns_section_with_correct_id(self):
        """Test that the function returns a SectionUiBlock with correct ID."""
        result = get_initial_canvas_blocks(num_plates="5")
        
        assert result.id == CANVAS_HEADER_SECTION
        assert result.type.value == "SECTION"
    
    def test_displays_number_of_plates(self):
        """Test that Number of Plates value is displayed in markdown."""
        result = get_initial_canvas_blocks(num_plates="7")
        
        # Should have one child - the markdown block
        assert len(result.children) == 1
        markdown_block = result.children[0]
        
        assert markdown_block.type.value == "MARKDOWN"
        assert "7" in markdown_block.value
        assert "Number of Plates" in markdown_block.value
    
    def test_default_value_is_1(self):
        """Test that default value is 1 when not provided."""
        result = get_initial_canvas_blocks()
        
        markdown_block = result.children[0]
        assert "1" in markdown_block.value


class TestCanvasHandler:
    """Test the canvas webhook handler logic."""
    
    @pytest.fixture
    def mock_handler(self):
        """Create a mock handler instance for testing."""
        # We can't easily instantiate BaseHTTPRequestHandler, so we'll test
        # the handler methods in isolation using mocks
        from api.canvas import handler
        
        # Create a mock handler with necessary attributes
        mock_instance = Mock(spec=handler)
        mock_instance.rfile = Mock()
        mock_instance.headers = {}
        
        # Bind the actual methods to the mock
        mock_instance.handle_canvas_created = handler.handle_canvas_created.__get__(mock_instance, handler)
        mock_instance.handle_user_interaction = handler.handle_user_interaction.__get__(mock_instance, handler)
        
        return mock_instance
    
    @pytest.fixture
    def sample_canvas_created_payload(self):
        """Sample payload for canvas.created event."""
        return {
            "version": "0",
            "baseURL": "https://custom-transform-dev.benchling.com",
            "tenantId": "ten_rv5bjjrq1v",
            "app": {
                "id": "app_M60RL3qy76xNQDFB"
            },
            "appDefinition": {
                "id": "appdef_zc6DGIvSSm",
                "versionNumber": "0.0.1"
            },
            "channel": "app_signals",
            "message": {
                "canvasId": "cnvs_Q4mPJ34a",
                "deprecated": False,
                "featureId": "my_feature_id",
                "type": "v2.canvas.created"
            },
            "configuration": {
                "Number of Plates": "7"
            }
        }
    
    @pytest.fixture
    def sample_user_interaction_payload(self):
        """Sample payload for user interaction event."""
        return {
            "version": "0",
            "baseURL": "https://custom-transform-dev.benchling.com",
            "tenantId": "ten_rv5bjjrq1v",
            "app": {
                "id": "app_M60RL3qy76xNQDFB"
            },
            "message": {
                "canvasId": "cnvs_Q4mPJ34a",
                "featureId": "my_feature_id",
                "userId": "user_123",
                "buttonId": "add_item",
                "type": "v2.canvas.userInteracted"
            },
            "configuration": {
                "Number of Plates": "3"
            }
        }
    
    def test_handle_canvas_created_extracts_data_correctly(self, mock_handler, sample_canvas_created_payload):
        """Test that canvas.created handler extracts data from payload correctly."""
        # Mock environment variables to skip API call
        with patch.dict(os.environ, {
            'BENCHLING_URL': '',
            'BENCHLING_CLIENT_ID': '',
            'BENCHLING_CLIENT_SECRET': ''
        }):
            response = mock_handler.handle_canvas_created(sample_canvas_created_payload)
        
        assert response['status'] == 'success'
        assert response['canvas_id'] == 'cnvs_Q4mPJ34a'
        assert response['num_plates'] == '7'
        assert 'note' in response
    
    def test_handle_canvas_created_with_missing_config(self, mock_handler):
        """Test canvas.created handler with missing configuration."""
        payload = {
            "app": {"id": "app_123"},
            "message": {
                "canvasId": "canvas_456",
                "featureId": "feat_789",
                "type": "v2.canvas.created"
            }
            # No configuration key
        }
        
        with patch.dict(os.environ, {
            'BENCHLING_URL': '',
            'BENCHLING_CLIENT_ID': '',
            'BENCHLING_CLIENT_SECRET': ''
        }):
            response = mock_handler.handle_canvas_created(payload)
        
        assert response['status'] == 'success'
        assert response['num_plates'] == '1'  # Default value
    
    def test_handle_user_interaction_extracts_data_correctly(self, mock_handler, sample_user_interaction_payload):
        """Test that user interaction handler extracts data correctly."""
        with patch.dict(os.environ, {
            'BENCHLING_URL': '',
            'BENCHLING_CLIENT_ID': '',
            'BENCHLING_CLIENT_SECRET': ''
        }):
            response = mock_handler.handle_user_interaction(sample_user_interaction_payload)
        
        assert response['status'] == 'success'
        assert response['button_id'] == 'add_item'
        assert response['num_plates'] == '3'
    
    @patch('api.canvas.update_canvas')
    @patch('api.canvas.get_benchling_client')
    def test_handle_canvas_created_calls_update_canvas(self, mock_get_client, mock_update_canvas, mock_handler, sample_canvas_created_payload):
        """Test that canvas.created calls update_canvas when env vars are set."""
        # Mock environment variables to enable API call
        with patch.dict(os.environ, {
            'BENCHLING_URL': 'https://test.benchling.com',
            'BENCHLING_CLIENT_ID': 'test_client_id',
            'BENCHLING_CLIENT_SECRET': 'test_secret'
        }):
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            
            response = mock_handler.handle_canvas_created(sample_canvas_created_payload)
        
        # Verify update_canvas was called
        assert mock_update_canvas.called
        call_args = mock_update_canvas.call_args
        assert call_args[1]['canvas_id'] == 'cnvs_Q4mPJ34a'
        assert call_args[1]['app_id'] == 'app_M60RL3qy76xNQDFB'
        assert call_args[1]['feature_id'] == 'my_feature_id'
        assert len(call_args[1]['blocks']) == 1
        
        assert response['status'] == 'success'


class TestPayloadParsing:
    """Test payload parsing for different webhook formats."""
    
    def test_parses_new_app_signals_format(self):
        """Test parsing the new app signals format with nested message."""
        payload = {
            "message": {
                "canvasId": "cnvs_123",
                "featureId": "feat_456",
                "type": "v2.canvas.created"
            },
            "app": {"id": "app_789"}
        }
        
        # Extract using the same logic as the handler
        message = payload.get('message', {})
        canvas_id = message.get('canvasId') or payload.get('canvas', {}).get('id')
        feature_id = message.get('featureId') or payload.get('feature', {}).get('id')
        webhook_type = message.get('type', payload.get('type', 'unknown'))
        
        assert canvas_id == 'cnvs_123'
        assert feature_id == 'feat_456'
        assert webhook_type == 'v2.canvas.created'
    
    def test_parses_old_format_fallback(self):
        """Test parsing falls back to old format if new format not present."""
        payload = {
            "canvas": {"id": "cnvs_old_123"},
            "feature": {"id": "feat_old_456"},
            "type": "v2.canvas.created",
            "app": {"id": "app_789"}
        }
        
        # Extract using the same logic as the handler
        message = payload.get('message', {})
        canvas_id = message.get('canvasId') or payload.get('canvas', {}).get('id')
        feature_id = message.get('featureId') or payload.get('feature', {}).get('id')
        webhook_type = message.get('type', payload.get('type', 'unknown'))
        
        assert canvas_id == 'cnvs_old_123'
        assert feature_id == 'feat_old_456'
        assert webhook_type == 'v2.canvas.created'


class TestUpdateCanvas:
    """Test the update_canvas function."""
    
    @patch('api.canvas.get_benchling_client')
    def test_update_canvas_calls_benchling_api(self, mock_get_client):
        """Test that update_canvas calls the Benchling API correctly."""
        from api.canvas import update_canvas
        
        # Setup mocks
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.apps.update_canvas.return_value = {"success": True}
        
        # Create a mock block
        mock_block = Mock()
        mock_block.id = "test_section"
        
        # Call update_canvas
        update_canvas(
            canvas_id="cnvs_test",
            app_id="app_test",
            feature_id="feat_test",
            blocks=[mock_block]
        )
        
        # Verify the API was called
        assert mock_client.apps.update_canvas.called
        call_kwargs = mock_client.apps.update_canvas.call_args[1]
        assert call_kwargs['canvas_id'] == 'cnvs_test'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

