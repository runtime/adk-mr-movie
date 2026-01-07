#movie night agent tools

from typing import Dict, List
import requests
import logging
from google.adk.tools import ToolContext


logger = logging.getLogger(__name__)

async def say_hello_tool(tool_context: ToolContext) -> dict:
    """
    says hello to user
    Args:
    tool_context: ToolContext Object
    :returns
    A dict with "hello" as the message
    :param tool_context:
    :return:
    """
    return {"status": "ok", "message": "hi I'm using a tool"}

logger.info(f'say hello tool says hello')