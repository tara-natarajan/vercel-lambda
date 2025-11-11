"""Canvas update utilities using CanvasBuilder."""
from typing import List

from benchling_client import get_benchling_client


def update_canvas(canvas_id: str, app_id: str, feature_id: str, blocks: List) -> None:
    """
    Update a canvas with new UI blocks.
    
    Args:
        canvas_id: Canvas ID to update
        app_id: App ID
        feature_id: Feature ID
        blocks: List of section UI blocks to display
    
    Raises:
        Exception: If canvas update fails
    """
    from benchling_sdk.apps.canvas.framework import CanvasBuilder
    
    benchling = get_benchling_client()
    
    canvas_builder = CanvasBuilder(app_id, feature_id)
    for block in blocks:
        canvas_builder.blocks.append(block)
    
    canvas_update = canvas_builder.to_update()
    benchling.apps.update_canvas(canvas_id=canvas_id, canvas=canvas_update)

