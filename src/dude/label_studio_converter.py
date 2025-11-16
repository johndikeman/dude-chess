"""
Label Studio XML Converter for Dude Agent Logs

This module converts comprehensive Dude agent logs into Label Studio XML format
for multi-turn conversation annotation, including tool usage and corrections.

Based on: https://labelstud.io/templates/multi_turn_chat
"""

import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging


logger = logging.getLogger(__name__)


class LogEntry:
    """Represents a single parsed log entry"""
    
    def __init__(self, timestamp: str, level: str, logger_name: str, function: str, 
                 line: int, message: str):
        self.timestamp = timestamp
        self.level = level
        self.logger_name = logger_name
        self.function = function
        self.line = line
        self.message = message
        self.raw_data: Optional[Dict[str, Any]] = None
        self.event_type: Optional[str] = None  # 'user', 'assistant', 'tool', 'system', 'error'
        self.author: Optional[str] = None
        self.is_final_response: bool = False
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'level': self.level,
            'logger_name': self.logger_name,
            'function': self.function,
            'line': self.line,
            'message': self.message,
            'raw_data': self.raw_data,
            'event_type': self.event_type,
            'author': self.author,
            'is_final_response': self.is_final_response
        }


class ConversationTurn:
    """Represents a single turn in the conversation"""
    
    def __init__(self, turn_id: int, timestamp: str):
        self.turn_id = turn_id
        self.timestamp = timestamp
        self.user_message: Optional[LogEntry] = None
        self.assistant_messages: List[LogEntry] = []
        self.tool_calls: List[LogEntry] = []
        self.errors: List[LogEntry] = []
        self.system_logs: List[LogEntry] = []
        
    def add_message(self, entry: LogEntry):
        """Add a log entry to the appropriate category"""
        if entry.event_type == 'user':
            self.user_message = entry
        elif entry.event_type == 'assistant':
            self.assistant_messages.append(entry)
        elif entry.event_type == 'tool':
            self.tool_calls.append(entry)
        elif entry.event_type == 'error':
            self.errors.append(entry)
        elif entry.event_type == 'system':
            self.system_logs.append(entry)
    
    def to_xml(self) -> ET.Element:
        """Convert this turn to XML format for Label Studio"""
        turn_elem = ET.Element('Turn', id=str(self.turn_id), timestamp=self.timestamp)
        
        # Add user message if present
        if self.user_message:
            user_elem = ET.SubElement(turn_elem, 'UserMessage')
            user_elem.text = self._clean_text(self.user_message.message)
            user_elem.set('timestamp', self.user_message.timestamp)
            user_elem.set('log_level', self.user_message.level)
            
            # Add raw data as attribute if available
            if self.user_message.raw_data:
                user_elem.set('raw_data', json.dumps(self.user_message.raw_data))
        
        # Add assistant messages
        for i, msg in enumerate(self.assistant_messages):
            assist_elem = ET.SubElement(turn_elem, 'AssistantMessage')
            assist_elem.set('index', str(i))
            assist_elem.set('author', msg.author or 'unknown')
            assist_elem.set('timestamp', msg.timestamp)
            assist_elem.set('log_level', msg.level)
            assist_elem.set('is_final', str(msg.is_final_response).lower())
            assist_elem.text = self._clean_text(msg.message)
            
            if msg.raw_data:
                assist_elem.set('raw_data', json.dumps(msg.raw_data))
        
        # Add tool calls
        for i, tool in enumerate(self.tool_calls):
            tool_elem = ET.SubElement(turn_elem, 'ToolCall')
            tool_elem.set('index', str(i))
            tool_elem.set('author', tool.author or 'unknown')
            tool_elem.set('timestamp', tool.timestamp)
            tool_elem.set('log_level', tool.level)
            tool_elem.text = self._clean_text(tool.message)
            
            if tool.raw_data:
                tool_elem.set('raw_data', json.dumps(tool.raw_data))
        
        # Add errors
        for i, error in enumerate(self.errors):
            error_elem = ET.SubElement(turn_elem, 'Error')
            error_elem.set('index', str(i))
            error_elem.set('timestamp', error.timestamp)
            error_elem.set('log_level', error.level)
            error_elem.set('function', error.function)
            error_elem.set('line', str(error.line))
            error_elem.text = self._clean_text(error.message)
        
        # Add system logs
        for i, sys_log in enumerate(self.system_logs):
            sys_elem = ET.SubElement(turn_elem, 'SystemLog')
            sys_elem.set('index', str(i))
            sys_elem.set('timestamp', sys_log.timestamp)
            sys_elem.set('log_level', sys_log.level)
            sys_elem.set('function', sys_log.function)
            sys_elem.text = self._clean_text(sys_log.message)
        
        return turn_elem
    
    def _clean_text(self, text: str) -> str:
        """Clean text for XML embedding"""
        if not text:
            return ""
        # Escape XML special characters
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        return text.strip()


class LogToLabelStudioConverter:
    """Converts Dude agent logs to Label Studio XML format"""
    
    # Log parsing regex patterns
    LOG_PATTERN = re.compile(
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) - '
        r'([^ ]+) - '
        r'([A-Za-z]+) - '
        r'\[([^:]+):(\d+)\] - '
        r'(.*)'
    )
    
    # Event type detection patterns
    USER_MESSAGE_PATTERNS = [
        r"call_agent_async started with topic",
        r"Updated session state topic",
        r"Full topic content",
        r"User message content created"
    ]
    
    ASSISTANT_MESSAGE_PATTERNS = [
        r"Processing event #\d+ from author",
        r"Final response received from",
        r"Full response captured",
        r"Agent Final Response"
    ]
    
    TOOL_USE_PATTERNS = [
        r"Event type:",
        r"Event attributes:",
        r"Usage data found",
        r"Event dump:",
        r"Google ADK event",
        r"Tool execution"
    ]
    
    ERROR_PATTERNS = [
        r"Failed to",
        r"Error in",
        r"CLI execution failed",
        r"Traceback",
        r"Exception"
    ]
    
    SYSTEM_PATTERNS = [
        r"Setting up session",
        r"Initializing",
        r"Session created",
        r"Starting agent",
        r"Agent execution"
    ]
    
    def __init__(self):
        self.conversation_turns: List[ConversationTurn] = []
        self.current_turn: Optional[ConversationTurn] = None
        self.turn_counter = 0
        
    def parse_log_file(self, log_path: Path) -> List[LogEntry]:
        """Parse a log file and return list of log entries"""
        logger.info(f"Parsing log file: {log_path}")
        
        entries = []
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                        
                    entry = self._parse_log_line(line, line_num)
                    if entry:
                        entries.append(entry)
                        logger.debug(f"Parsed entry from line {line_num}: {entry.event_type}")
                    else:
                        logger.warning(f"Failed to parse line {line_num}: {line[:100]}...")
            
            logger.info(f"Successfully parsed {len(entries)} log entries")
            return entries
            
        except Exception as e:
            logger.error(f"Error parsing log file {log_path}: {str(e)}", exc_info=True)
            return []
    
    def _parse_log_line(self, line: str, line_num: int) -> Optional[LogEntry]:
        """Parse a single log line"""
        match = self.LOG_PATTERN.match(line)
        if not match:
            # Try alternative format without milliseconds
            alt_pattern = re.compile(
                r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - '
                r'([^ ]+) - '
                r'([A-Za-z]+) - '
                r'\[([^:]+):(\d+)\] - '
                r'(.*)'
            )
            match = alt_pattern.match(line)
            if not match:
                return None
        
        timestamp, logger_name, level, function, line_no, message = match.groups()
        
        entry = LogEntry(
            timestamp=timestamp,
            level=level,
            logger_name=logger_name,
            function=function,
            line=int(line_no),
            message=message
        )
        
        # Classify the event type
        entry.event_type = self._classify_event_type(entry)
        
        # Extract additional metadata from the message
        self._extract_metadata(entry)
        
        return entry
    
    def _classify_event_type(self, entry: LogEntry) -> str:
        """Classify the event type based on patterns"""
        message_lower = entry.message.lower()
        
        # Check error patterns first (highest priority)
        for pattern in self.ERROR_PATTERNS:
            if re.search(pattern, entry.message, re.IGNORECASE):
                return 'error'
        
        # Check user patterns
        for pattern in self.USER_MESSAGE_PATTERNS:
            if re.search(pattern, entry.message, re.IGNORECASE):
                return 'user'
        
        # Check assistant patterns
        for pattern in self.ASSISTANT_MESSAGE_PATTERNS:
            if re.search(pattern, entry.message, re.IGNORECASE):
                return 'assistant'
        
        # Check tool patterns
        for pattern in self.TOOL_USE_PATTERNS:
            if re.search(pattern, entry.message, re.IGNORECASE):
                return 'tool'
        
        # Check system patterns
        for pattern in self.SYSTEM_PATTERNS:
            if re.search(pattern, entry.message, re.IGNORECASE):
                return 'system'
        
        # Default classification based on log level
        if entry.level in ['ERROR', 'CRITICAL']:
            return 'error'
        elif entry.level in ['WARNING']:
            return 'system'
        elif 'orchestrator' in entry.logger_name.lower() or 'agent' in entry.logger_name.lower():
            return 'assistant'
        else:
            return 'system'
    
    def _extract_metadata(self, entry: LogEntry):
        """Extract additional metadata from log messages"""
        # Extract author information
        author_match = re.search(r"from \[([^\]]+)\]", entry.message)
        if author_match:
            entry.author = author_match.group(1)
        
        # Detect final responses
        if 'final response' in entry.message.lower() or entry.message.startswith('Agent Final Response'):
            entry.is_final_response = True
        
        # Try to parse JSON in messages
        json_match = re.search(r'\{.*\}', entry.message)
        if json_match:
            try:
                entry.raw_data = json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
    
    def build_conversation_structure(self, entries: List[LogEntry]):
        """Build conversation structure from log entries"""
        logger.info(f"Building conversation structure from {len(entries)} entries")
        
        self.conversation_turns = []
        self.current_turn = None
        self.turn_counter = 0
        
        for entry in entries:
            # Start new turn on user messages
            if entry.event_type == 'user' and 'topic' in entry.message:
                if self.current_turn:
                    self.conversation_turns.append(self.current_turn)
                
                self.turn_counter += 1
                self.current_turn = ConversationTurn(self.turn_counter, entry.timestamp)
                logger.debug(f"Started new conversation turn {self.turn_counter}")
            
            # Add entry to current turn if it exists
            if self.current_turn:
                self.current_turn.add_message(entry)
        
        # Add the last turn
        if self.current_turn:
            self.conversation_turns.append(self.current_turn)
        
        logger.info(f"Built {len(self.conversation_turns)} conversation turns")
    
    def to_label_studio_xml(self, output_path: Optional[Path] = None) -> str:
        """Convert conversation to Label Studio XML format"""
        logger.info("Converting conversation to Label Studio XML format")
        
        # Create root element
        root = ET.Element('Dialogue', version='1.0')
        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        
        # Add metadata
        metadata = ET.SubElement(root, 'Metadata')
        ET.SubElement(metadata, 'TotalTurns').text = str(len(self.conversation_turns))
        ET.SubElement(metadata, 'GeneratedAt').text = datetime.now().isoformat()
        ET.SubElement(metadata, 'SourceLogs').text = str(self.conversation_turns[0].timestamp if self.conversation_turns else 'unknown')
        
        # Add conversation turns
        conversation_elem = ET.SubElement(root, 'Conversation')
        for turn in self.conversation_turns:
            turn_elem = turn.to_xml()
            conversation_elem.append(turn_elem)
        
        # Add Label Studio specific annotations structure
        annotations = ET.SubElement(root, 'Annotations')
        annotations.set('interface', 'multi_turn_chat')
        
        # Create choices for corrections
        corrections = ET.SubElement(annotations, 'Corrections')
        ET.SubElement(corrections, 'Correction', type='message_content', label='Fix Message Content')
        ET.SubElement(corrections, 'Correction', type='tool_call', label='Fix Tool Call')
        ET.SubElement(corrections, 'Correction', type='author', label='Correct Author')
        ET.SubElement(corrections, 'Correction', type='remove_turn', label='Remove Turn')
        ET.SubElement(corrections, 'Correction', type='add_turn', label='Add Missing Turn')
        
        # Create ratings
        ratings = ET.SubElement(annotations, 'Ratings')
        ET.SubElement(ratings, 'Rating', name='response_quality', type="choices", toName="assistant_message",
                     choices="["Very Good", "Good", "Neutral", "Poor", "Very Poor"]")
        ET.SubElement(ratings, 'Rating', name='tool_accuracy', type="choices", toName="tool_call",
                     choices="["Correct", "Partially Correct", "Incorrect"]")
        ET.SubElement(ratings, 'Rating', name='conversation_flow', type="rating", toName="conversation",
                     min="1", max="5")
        
        # Convert to string
        xml_str = ET.tostring(root, encoding='unicode', method='xml')
        
        # Pretty print with proper indentation
        import xml.dom.minidom
        dom = xml.dom.minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent='  ')
        
        # Save to file if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
            logger.info(f"Label Studio XML saved to: {output_path}")
        
        return pretty_xml
    
    def convert_log_to_label_studio(self, log_path: Path, output_path: Optional[Path] = None) -> str:
        """Complete conversion from log file to Label Studio XML"""
        logger.info(f"Starting complete conversion: {log_path} -> Label Studio XML")
        
        # Parse log file
        entries = self.parse_log_file(log_path)
        if not entries:
            logger.error("No log entries found or failed to parse log file")
            return ""
        
        # Build conversation structure
        self.build_conversation_structure(entries)
        
        # Generate XML
        xml_output = self.to_label_studio_xml(output_path)
        
        logger.info("Conversion completed successfully")
        return xml_output
    
    def process_directory(self, log_dir: Path, output_dir: Path) -> Dict[str, str]:
        """Process all log files in a directory"""
        logger.info(f"Processing directory: {log_dir}")
        
        results = {}
        
        if not log_dir.exists():
            logger.error(f"Log directory does not exist: {log_dir}")
            return results
        
        # Find all log files
        log_files = list(log_dir.glob("dude_session_*.log"))
        logger.info(f"Found {len(log_files)} log files")
        
        for log_file in log_files:
            try:
                output_file = output_dir / f"{log_file.stem}.xml"
                xml_content = self.convert_log_to_label_studio(log_file, output_file)
                results[str(log_file)] = xml_content
                logger.info(f"Successfully processed {log_file.name}")
            except Exception as e:
                logger.error(f"Failed to process {log_file}: {str(e)}", exc_info=True)
                results[str(log_file)] = f"ERROR: {str(e)}"
        
        return results


def convert_single_log(log_path: str, output_path: Optional[str] = None) -> str:
    """Convert a single log file to Label Studio XML"""
    converter = LogToLabelStudioConverter()
    
    log_file = Path(log_path)
    output_file = Path(output_path) if output_path else None
    
    return converter.convert_log_to_label_studio(log_file, output_file)


def convert_logs_directory(log_dir: str, output_dir: str) -> Dict[str, str]:
    """Convert all log files in a directory"""
    converter = LogToLabelStudioConverter()
    
    return converter.process_directory(Path(log_dir), Path(output_dir))


if __name__ == "__main__":
    # CLI interface for the converter
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert Dude agent logs to Label Studio XML format')
    parser.add_argument('input', help='Input log file or directory')
    parser.add_argument('--output', '-o', help='Output XML file or directory')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        exit(1)
    
    if input_path.is_file():
        # Single file conversion
        output = args.output or f"{input_path.stem}.xml"
        result = convert_single_log(str(input_path), output)
        
        if result and not result.startswith("ERROR"):
            print(f"Successfully converted {input_path} to {output}")
        else:
            print(f"Failed to convert {input_path}: {result}")
            exit(1)
            
    elif input_path.is_dir():
        # Directory conversion
        output_dir = args.output or "label_studio_tasks"
        results = convert_logs_directory(str(input_path), output_dir)
        
        success_count = sum(1 for r in results.values() if not r.startswith("ERROR"))
        total_count = len(results)
        
        print(f"Processed {success_count}/{total_count} files successfully")
        print(f"Output directory: {output_dir}")
        
        if success_count < total_count:
            print("Errors:")
            for path, result in results.items():
                if result.startswith("ERROR"):
                    print(f"  {Path(path).name}: {result}")
            exit(1)
