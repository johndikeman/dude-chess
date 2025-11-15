from typing import List
from google.adk.agents import (
    LlmAgent,
    BaseAgent,
    LoopAgent,
    SequentialAgent,
    callback_context,
)
import os
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from google.adk.models.lite_llm import LiteLlm
from dude.models import Plan

prompt = """
You are an expert coding agent. your primary directive is to complete the task that's been assigned to you.

here is your goal:
{coder_task}

think carefully and consider all alternatives.
<important>for all tasks, prefer using the python interpreter to run code. you also have access to some special libraries to analyze code files with a language server:</important>

<example code>
from multilspy import SyncLanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger
...
config = MultilspyConfig.from_dict({"code_language": "python"}) # Also supports "python", "rust", "csharp", "typescript", "javascript", "go", "dart", "ruby"
logger = MultilspyLogger()
lsp = SyncLanguageServer.create(config, logger, os.getenv("REPO_ROOT")) # the env var REPO_ROOT will always have your repo root
with lsp.start_server():
    result = lsp.request_definition(
        "relative/path/to/code_file.java", # Filename of location where request is being made
        163, # line number of symbol for which request is being made
        4 # column number of symbol for which request is being made
    )
    result2 = lsp.request_completions(
        ...
    )
    result3 = lsp.request_references(
        ...
    )
    result4 = lsp.request_document_symbols(
       "relative/file/path" 
    ) # returns a list of UnifiedSymbolInformation representing the lsp symbols in the document and their locations. its source is given below
#class UnifiedSymbolInformation(TypedDict):
#    \"""Represents information about programming constructs like variables, classes,
#    interfaces etc.\"""
#
#    deprecated: NotRequired[bool]
#    \""" Indicates if this symbol is deprecated.
#
#    @deprecated Use tags instead \"""
#    location: NotRequired[Location]
#    \""" The location of this symbol. The location's range is used by a tool
#    to reveal the location in the editor. If the symbol is selected in the
#    tool the range's start information is used to position the cursor. So
#    the range usually spans more than the actual symbol's name and does
#    normally include things like visibility modifiers.
#
#    The range doesn't have to denote a node range in the sense of an abstract
#    syntax tree. It can therefore not be used to re-construct a hierarchy of
#    the symbols. \"""
#    name: str
#    \""" The name of this symbol. \"""
#    kind: SymbolKind
#    \""" The kind of this symbol. \"""
#    tags: NotRequired[List[SymbolTag]]
#    \""" Tags for this symbol.
#
#    @since 3.16.0 \"""
#    containerName: NotRequired[str]
#    \""" The name of the symbol containing this symbol. This information is for
#    user interface purposes (e.g. to render a qualifier in the user interface
#    if necessary). It can't be used to re-infer a hierarchy for the document
#    symbols. \"""
#
#    detail: NotRequired[str]
#    \""" More detail for this symbol, e.g the signature of a function. \"""
#    
#    range: NotRequired[Range]
#    \""" The range enclosing this symbol not including leading/trailing whitespace but everything else
#    like comments. This information is typically used to determine if the clients cursor is
#    inside the symbol to reveal in the symbol in the UI. \"""
#    selectionRange: NotRequired[Range]
#    \""" The range that should be selected and revealed when this symbol is being picked, e.g the name of a function.
#    Must be contained by the `range`. \"""
#    class SymbolKind(IntEnum):
#        File = 1
#        Module = 2
#        Namespace = 3
#        Package = 4
#        Class = 5
#        Method = 6
#        Property = 7
#        Field = 8
#        Constructor = 9
#        Enum = 10
#        Interface = 11
#        Function = 12
#        Variable = 13
#        Constant = 14
#        String = 15
#        Number = 16
#        Boolean = 17
#        Array = 18
#        Object = 19
#        Key = 20
#        Null = 21
#        EnumMember = 22
#        Struct = 23
#        Event = 24
#        Operator = 25
#        TypeParameter = 26
#
#class Range(TypedDict):
#    \"""A range in a text document expressed as (zero-based) start and end positions.
#If you want to specify a range that contains a line including the line ending
#    character(s) then use an end position denoting the start of the next line.
#    For example:
#    ```ts
#    {
#        start: { line: 5, character: 23 }
#        end : { line 6, character : 0 }
#    }
#    ```\"""
#
#    start: Position
#    \""" The range's start position. \"""
#    end: Position
#    \""" The range's end position. \"""
#    result5 = lsp.request_hover(
#        ...
#    )
#    ...
#</example code>

"""

coder = LlmAgent(
    name="coder",
    model=LiteLlm(model="openrouter/moonshotai/kimi-k2-thinking"),
    instruction=prompt,
    tools=[
        MCPToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="uvx",
                    args=[
                        "mcp-python-interpreter",
                        "--dir",
                        os.path.abspath(os.getcwd()),
                        "--python-path",
                        os.path.join(os.getcwd(), ".venv"),
                    ],
                ),
                timeout=60,
            ),
        ),
    ],
)
