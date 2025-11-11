"""Canvas UI block builders and constants."""

# Constants
CANVAS_HEADER_SECTION = "canvas_header_section"
ADD_BUTTON_ID = "add_item"
REMOVE_BUTTON_ID = "remove_item"
SUBMIT_BUTTON_ID = "submit"

INSTRUCTIONS = """
Welcome to the Vercel Lambda Canvas!\n
Add or remove items using the buttons below, then click submit when ready.\n
"""


def get_initial_canvas_blocks(num_plates: int = 1):
    """
    Generate initial canvas UI blocks.
    
    Args:
        num_plates: Number of plates from configuration
    
    Returns:
        SectionUiBlock: Initial canvas section with form inputs and buttons
    """
    from benchling_sdk.models import (
        ButtonUiBlock,
        ButtonUiBlockType,
        MarkdownUiBlock,
        MarkdownUiBlockType,
        SectionUiBlock,
        SectionUiBlockType,
        TextInputUiBlock,
        TextInputUiBlockType,
    )
    
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


def create_success_section(section_id: str, message: str):
    """
    Create a success message section.
    
    Args:
        section_id: Unique ID for the section
        message: Success message to display
    
    Returns:
        SectionUiBlock: Section with success message
    """
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
    """
    Create an error message section.
    
    Args:
        section_id: Unique ID for the section
        message: Error message to display
    
    Returns:
        SectionUiBlock: Section with error message
    """
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
    """
    Create the submit success section with reset button.
    
    Returns:
        SectionUiBlock: Section with success message and reset button
    """
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
                label="Start Over",
                enabled=True,
            ),
        ],
    )

