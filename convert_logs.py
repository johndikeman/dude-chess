#!/usr/bin/env python3
"""
Dude Log Converter - CLI tool to convert Dude agent logs to Label Studio format

This script provides a command-line interface to convert Dude agent logs
into Label Studio XML format for annotation and correction.

Usage:
    python convert_logs.py <log_file|log_directory> [--output <output_path>]
"""

import sys
import argparse
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dude.label_studio_converter import convert_single_log, convert_logs_directory


def main():
    parser = argparse.ArgumentParser(
        description='Convert Dude agent logs to Label Studio XML format',
        epilog='Examples:\n'
               '  python convert_logs.py logs/dude_session_20231115_143022.log\n'
               '  python convert_logs.py logs/ --output label_studio_tasks/\n'
               '  python convert_logs.py logs/ -v',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'input',
        help='Path to log file or directory containing log files'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Path to output XML file or directory (default: same name with .xml extension or "label_studio_tasks/")'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--list-logs', '-l',
        action='store_true',
        help='List available log files and exit'
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    # List available logs if requested
    if args.list_logs:
        log_dir = Path("logs")
        if not log_dir.exists():
            print("No logs directory found. Run the agent first to generate logs.")
            return 1
        
        log_files = sorted(log_dir.glob("dude_session_*.log"))
        if not log_files:
            print("No log files found in logs/ directory.")
            return 1
        
        print("Available log files:")
        print("-" * 60)
        for i, log_file in enumerate(log_files, 1):
            size_mb = log_file.stat().st_size / (1024 * 1024)
            print(f"{i:2d}. {log_file.name} ({size_mb:.2f} MB)")
        print("-" * 60)
        print(f"Total: {len(log_files)} log files")
        return 0
    
    # Check if input exists
    if not input_path.exists():
        print(f"❌ Error: Input path does not exist: {input_path}")
        print("\nTip: Use --list-logs to see available log files")
        return 1
    
    # Process based on input type
    try:
        if input_path.is_file():
            # Single file conversion
            output_path = args.output or f"{input_path.stem}.xml"
            print(f"Converting log file: {input_path.name}")
            print(f"{'Output:':<10} {output_path}")
            
            result = convert_single_log(str(input_path), output_path)
            
            if result and not result.startswith("ERROR"):
                print(f"✅ Successfully converted to {output_path}")
                return 0
            else:
                print(f"❌ Failed to convert: {result}")
                return 1
                
        elif input_path.is_dir():
            # Directory conversion
            output_dir = args.output or "label_studio_tasks"
            print(f"Converting all logs in directory: {input_path}")
            print(f"{'Output directory:':<18} {output_dir}")
            print(f"{'Verbose mode:':<18} {'Yes' if args.verbose else 'No'}")
            print("-" * 50)
            
            results = convert_logs_directory(str(input_path), output_dir)
            
            success_count = sum(1 for r in results.values() if not r.startswith("ERROR"))
            total_count = len(results)
            
            print(f"\n📊 Conversion Summary:")
            print(f"   Total files processed: {total_count}")
            print(f"   Successful conversions: {success_count}")
            print(f"   Failed conversions: {total_count - success_count}")
            
            if success_count == total_count:
                print(f"✅ All files converted successfully to {output_dir}/")
                return 0
            else:
                print("\n❌ Errors encountered:")
                for path, result in results.items():
                    if result.startswith("ERROR"):
                        print(f"   {Path(path).name}: {result[6:]}")
                return 1
                
    except KeyboardInterrupt:
        print("\n\n⚠️  Conversion interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
