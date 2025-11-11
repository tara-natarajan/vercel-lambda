"""Integration tests for update_canvas to debug the to_dict error."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.canvas import update_canvas, get_initial_canvas_blocks


class TestUpdateCanvasIntegration:
    """Test update_canvas with realistic mock scenarios."""
    
    @patch('api.canvas.get_benchling_client')
    def test_update_canvas_object_has_to_dict_method(self, mock_get_client):
        """Test that the canvas_update object passed to API has to_dict method."""
        # Setup
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Track what was passed to update_canvas
        captured_canvas_arg = None
        
        def capture_canvas_arg(canvas_id, canvas):
            nonlocal captured_canvas_arg
            captured_canvas_arg = canvas
            return Mock()
        
        mock_client.apps.update_canvas = Mock(side_effect=capture_canvas_arg)
        
        # Get a real block
        blocks = [get_initial_canvas_blocks(num_plates="5")]
        
        # Execute
        try:
            update_canvas(
                canvas_id="test_canvas",
                app_id="test_app",
                feature_id="test_feature",
                blocks=blocks
            )
        except AttributeError as e:
            if "has no attribute 'to_dict'" in str(e):
                pytest.fail(f"Canvas object doesn't have to_dict method: {captured_canvas_arg}")
        
        # Assert - the canvas argument should have a to_dict method
        assert captured_canvas_arg is not None, "Canvas argument was not captured"
        assert hasattr(captured_canvas_arg, 'to_dict'), f"Canvas object {type(captured_canvas_arg)} doesn't have to_dict method"
    
    @patch('api.canvas.get_benchling_client')
    def test_update_canvas_with_real_blocks(self, mock_get_client):
        """Test update_canvas with real blocks from get_initial_canvas_blocks."""
        # Setup
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.apps.update_canvas.return_value = {"id": "canvas_123"}
        
        # Get real blocks from our function
        blocks = [get_initial_canvas_blocks(num_plates="5")]
        
        # Call update_canvas - should work now
        update_canvas(
            canvas_id="test_canvas",
            app_id="test_app",
            feature_id="test_feature",
            blocks=blocks
        )
        
        # Verify the API was called
        assert mock_client.apps.update_canvas.called
        call_kwargs = mock_client.apps.update_canvas.call_args[1]
        assert call_kwargs['canvas_id'] == 'test_canvas'
        # Verify the canvas argument has to_dict method (not a dict)
        assert hasattr(call_kwargs['canvas'], 'to_dict')


class TestAppCanvasUpdateModel:
    """Test the AppCanvasUpdate model directly."""
    
    def test_app_canvas_update_accepts_blocks(self):
        """Test that AppCanvasUpdate can be created with blocks."""
        from benchling_api_client.v2.stable.models.app_canvas_update import AppCanvasUpdate
        
        # Get real blocks
        blocks = [get_initial_canvas_blocks(num_plates="5")]
        
        # Create AppCanvasUpdate
        canvas_update = AppCanvasUpdate(blocks=blocks)
        
        # Verify it has the required methods
        assert hasattr(canvas_update, 'to_dict')
        assert canvas_update.blocks == blocks
        
        # Verify to_dict works
        dict_result = canvas_update.to_dict()
        assert 'blocks' in dict_result
    
    def test_app_canvas_update_structure(self):
        """Test the structure of AppCanvasUpdate."""
        from benchling_api_client.v2.stable.models.app_canvas_update import AppCanvasUpdate
        
        blocks = [get_initial_canvas_blocks(num_plates="3")]
        canvas_update = AppCanvasUpdate(blocks=blocks)
        
        # Verify structure
        assert isinstance(canvas_update.to_dict(), dict)
        assert len(canvas_update.blocks) == 1


class TestDirectModelUsage:
    """Test using Benchling models directly without CanvasBuilder."""
    
    def test_find_app_canvas_update_model(self):
        """Try to find the correct AppCanvasUpdate import."""
        # Try different import paths
        import_attempts = [
            "benchling_api_client.v2.stable.models.app_canvas_update",
            "benchling_api_client.v2.stable.models",
            "benchling_sdk.apps.types",
            "benchling_sdk.apps.canvas.types",
        ]
        
        for import_path in import_attempts:
            try:
                if import_path == "benchling_api_client.v2.stable.models.app_canvas_update":
                    from benchling_api_client.v2.stable.models import app_canvas_update
                    print(f"\n✓ Found in {import_path}")
                    print(f"  Available: {dir(app_canvas_update)}")
                elif import_path == "benchling_api_client.v2.stable.models":
                    import benchling_api_client.v2.stable.models as models
                    # Check if AppCanvasUpdate exists
                    if hasattr(models, 'AppCanvasUpdate'):
                        print(f"\n✓ AppCanvasUpdate found in {import_path}")
                    else:
                        # List models that contain 'canvas' or 'Canvas'
                        canvas_models = [name for name in dir(models) if 'canvas' in name.lower()]
                        print(f"\n✗ AppCanvasUpdate not in {import_path}")
                        print(f"  Canvas-related models: {canvas_models[:10]}")
            except ImportError as e:
                print(f"\n✗ Failed to import from {import_path}: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])

