try:
    from dotenv import load_dotenv
    from pathlib import Path
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass

from browser_use.tools.read_tool import read_tool_spec
from browser_use.tools.search_tool import search_tool_spec, get_search_results_tool_spec


__all__ = [
    'read_tool_spec',
    'search_tool_spec',
    'get_search_results_tool_spec'
]