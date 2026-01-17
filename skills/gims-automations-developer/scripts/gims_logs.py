#!/usr/bin/env python3
"""CLI for GIMS Script Execution Logs via SSE stream."""

import argparse
import json
import re
import sys
import time
from gims_client import GimsClient, GimsApiError, print_error

# Regex pattern to match log line prefix: "2026-01-11 04:23:33,350 [INFO] "
LOG_LINE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \[[^\]]+\] ")

# Default end markers
DEFAULT_END_MARKERS = ["END SCRIPT"]


def parse_log_line(line: str, keep_timestamp: bool = False) -> str:
    """Parse a log line, optionally removing timestamp and log level."""
    if keep_timestamp:
        return line
    match = LOG_LINE_PATTERN.match(line)
    if match:
        return line[match.end():]
    return line


def check_end_markers(text: str, markers: list[str]) -> bool:
    """Check if text contains any of the end markers."""
    for marker in markers:
        if marker in text:
            return True
    return False


def apply_filter(text: str, pattern: str | None) -> bool:
    """Check if text matches the filter pattern."""
    if pattern is None:
        return True
    try:
        compiled = re.compile(pattern)
        return compiled.search(text) is not None
    except re.error:
        return pattern in text


def cmd_stream(args):
    """Stream script execution log via SSE."""
    client = GimsClient()

    timeout = args.timeout
    end_markers = args.end_markers if args.end_markers else DEFAULT_END_MARKERS
    filter_pattern = args.filter
    keep_timestamp = args.keep_timestamp
    max_size = args.max_size * 1024  # Convert KB to bytes

    # Get log stream URL via dedicated endpoint
    # API returns: {'url': ['/logviewer/stream/{log_name}/']}
    try:
        log_info = client.request("GET", f"/scripts/script_log_url/{args.script_id}/")
        urls = log_info.get("url", [])
        if not urls or not isinstance(urls, list):
            print_error(f"Script {args.script_id} has no log available")
            sys.exit(1)
        log_url = urls[0]  # Get first URL from list
    except GimsApiError as e:
        if e.status_code == 404:
            print_error(f"Script with ID {args.script_id} not found or has no log")
            sys.exit(1)
        raise

    # Add tail parameter (required) - 0 means only new entries
    tail_value = args.tail if args.tail is not None else 0
    if "?" in log_url:
        log_url += f"&tail={tail_value}"
    else:
        log_url += f"?tail={tail_value}"

    # Collect log lines
    buffer: list[str] = []
    buffer_size = 0
    end_marker_found = False
    timeout_reached = False
    size_limit_reached = False
    connection_error: str | None = None

    start_time = time.monotonic()
    retry_delay = 2.0

    while True:
        elapsed = time.monotonic() - start_time
        if elapsed >= timeout:
            timeout_reached = True
            break

        remaining_timeout = timeout - elapsed

        try:
            received_any_data = False
            for data in client.stream_sse(log_url, remaining_timeout):
                received_any_data = True

                # Check timeout
                if time.monotonic() - start_time >= timeout:
                    timeout_reached = True
                    break

                # Parse SSE data - it's JSON with "content" field
                try:
                    parsed = json.loads(data)
                    content = parsed.get("content", "")
                except (json.JSONDecodeError, TypeError):
                    content = data

                if not content:
                    continue

                # Process each line in content
                for line in content.splitlines():
                    if not line.strip():
                        continue

                    # Check for end markers (before filtering!)
                    if check_end_markers(line, end_markers):
                        end_marker_found = True
                        parsed_line = parse_log_line(line, keep_timestamp)
                        if apply_filter(parsed_line, filter_pattern):
                            line_size = len(parsed_line.encode("utf-8")) + 1
                            if buffer_size + line_size <= max_size:
                                buffer.append(parsed_line)
                                buffer_size += line_size
                        break

                    # Parse and filter line
                    parsed_line = parse_log_line(line, keep_timestamp)

                    if not apply_filter(parsed_line, filter_pattern):
                        continue

                    # Check size limit
                    line_size = len(parsed_line.encode("utf-8")) + 1
                    if buffer_size + line_size > max_size:
                        size_limit_reached = True
                        break

                    buffer.append(parsed_line)
                    buffer_size += line_size

                if end_marker_found or size_limit_reached or timeout_reached:
                    break

            # Exit if we found what we need or timed out
            if end_marker_found or size_limit_reached or timeout_reached:
                break

            # Connection closed - retry if we have time
            if not received_any_data:
                remaining = timeout - (time.monotonic() - start_time)
                if remaining > retry_delay:
                    time.sleep(retry_delay)
                    continue
                else:
                    timeout_reached = True
                    break
            else:
                if buffer:
                    break
                remaining = timeout - (time.monotonic() - start_time)
                if remaining > retry_delay:
                    time.sleep(retry_delay)
                    continue
                else:
                    timeout_reached = True
                    break

        except GimsApiError as e:
            connection_error = f"SSE connection error: {e.message}"
            remaining = timeout - (time.monotonic() - start_time)
            if remaining > retry_delay:
                time.sleep(retry_delay)
                connection_error = None
                continue
            break
        except Exception as e:
            connection_error = f"Unexpected error: {str(e)}"
            break

    # Build result
    warnings: list[str] = []
    if timeout_reached and not end_marker_found:
        warnings.append(f"WARNING: Timeout ({timeout}s) reached without end marker")
    if size_limit_reached:
        warnings.append(f"WARNING: Size limit ({args.max_size}KB) reached")
    if connection_error:
        warnings.append(f"WARNING: {connection_error}")

    # Output
    if warnings:
        for w in warnings:
            print(w, file=sys.stderr)

    if buffer:
        print("\n".join(buffer))
    else:
        print("No log data received", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="GIMS Script Execution Logs CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s stream 123                      Stream log for script 123
  %(prog)s stream 123 --timeout 60         Stream with 60s timeout
  %(prog)s stream 123 --tail 10            Start with last 10 lines
  %(prog)s stream 123 --filter "ERROR"     Only show lines containing ERROR
  %(prog)s stream 123 --keep-timestamp     Keep timestamp in output
  %(prog)s stream 123 --end-markers "DONE" "END"  Custom end markers
""",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    stream_cmd = subparsers.add_parser("stream", help="Stream script execution log via SSE")
    stream_cmd.add_argument("script_id", type=int, help="Script ID")
    stream_cmd.add_argument("--timeout", type=int, default=30, help="Timeout in seconds (default: 30)")
    stream_cmd.add_argument("--tail", type=int, help="Number of historical lines (default: 0 = new only)")
    stream_cmd.add_argument("--end-markers", nargs="+", help="End markers (default: 'END SCRIPT')")
    stream_cmd.add_argument("--filter", help="Regex filter for log lines")
    stream_cmd.add_argument("--keep-timestamp", action="store_true", help="Keep timestamp in output")
    stream_cmd.add_argument("--max-size", type=int, default=100, help="Max output size in KB (default: 100)")

    args = parser.parse_args()

    try:
        handlers = {
            "stream": cmd_stream,
        }
        handlers[args.command](args)
    except GimsApiError as e:
        print_error(f"{e.message}\nDetail: {e.detail}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
