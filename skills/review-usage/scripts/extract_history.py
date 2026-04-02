#!/usr/bin/env python3
"""
Extract user prompts and conversation patterns from Claude Code history.

Usage:
    python extract_history.py [--limit N] [--project PROJECT_PATH]

Output: JSON with structured conversation data for analysis.
"""

import json
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime


def read_jsonl(filepath):
    """Read a JSONL file and return list of parsed objects."""
    entries = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except (IOError, OSError):
        pass
    return entries


def extract_user_prompts_from_history(history_path, limit=None, project_filter=None):
    """Extract user prompts from the global history.jsonl file."""
    entries = read_jsonl(history_path)

    # Group by sessionId
    sessions = {}
    for entry in entries:
        sid = entry.get("sessionId", "unknown")
        if sid not in sessions:
            sessions[sid] = {
                "sessionId": sid,
                "project": entry.get("project", ""),
                "prompts": [],
                "first_timestamp": entry.get("timestamp", 0),
                "last_timestamp": entry.get("timestamp", 0),
            }

        display = entry.get("display", "")
        if display and not display.startswith("/"):  # Skip slash commands in history
            sessions[sid]["prompts"].append({
                "text": display,
                "timestamp": entry.get("timestamp", 0),
            })
        elif display and display.startswith("/"):
            sessions[sid]["prompts"].append({
                "text": display,
                "timestamp": entry.get("timestamp", 0),
                "is_command": True,
            })

        ts = entry.get("timestamp", 0)
        if ts > sessions[sid]["last_timestamp"]:
            sessions[sid]["last_timestamp"] = ts
        if ts < sessions[sid]["first_timestamp"]:
            sessions[sid]["first_timestamp"] = ts

    # Filter by project if specified
    if project_filter:
        sessions = {k: v for k, v in sessions.items()
                    if project_filter in v.get("project", "")}

    # Sort by last_timestamp descending
    sorted_sessions = sorted(sessions.values(), key=lambda x: x["last_timestamp"], reverse=True)

    if limit:
        sorted_sessions = sorted_sessions[:limit]

    return sorted_sessions


def extract_session_details(session_jsonl_path):
    """Extract detailed conversation data from a session JSONL file."""
    entries = read_jsonl(session_jsonl_path)

    conversation = {
        "file": str(session_jsonl_path),
        "user_messages": [],
        "tools_used": [],
        "slash_commands": [],
        "total_user_messages": 0,
        "total_assistant_messages": 0,
        "session_metadata": {},
    }

    for entry in entries:
        msg_type = entry.get("type")
        message = entry.get("message", {})

        if msg_type == "user":
            content = message.get("content", "")
            if isinstance(content, str) and content.strip():
                conversation["user_messages"].append({
                    "text": content,
                    "timestamp": entry.get("timestamp", ""),
                    "cwd": entry.get("cwd", ""),
                })
                conversation["total_user_messages"] += 1
            elif isinstance(content, list):
                # Multi-part content
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                if text_parts:
                    conversation["user_messages"].append({
                        "text": "\n".join(text_parts),
                        "timestamp": entry.get("timestamp", ""),
                        "cwd": entry.get("cwd", ""),
                    })
                    conversation["total_user_messages"] += 1

            # Capture metadata from first user message
            if not conversation["session_metadata"] and entry.get("version"):
                conversation["session_metadata"] = {
                    "version": entry.get("version", ""),
                    "entrypoint": entry.get("entrypoint", ""),
                    "gitBranch": entry.get("gitBranch", ""),
                    "permissionMode": entry.get("permissionMode", ""),
                }

        elif msg_type == "assistant":
            conversation["total_assistant_messages"] += 1
            content = message.get("content", [])
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "tool_use":
                        tool_name = part.get("name", "")
                        if tool_name and tool_name not in conversation["tools_used"]:
                            conversation["tools_used"].append(tool_name)

    return conversation


def find_session_files(projects_dir, limit=10):
    """Find the most recent session JSONL files across all projects."""
    session_files = []
    projects_path = Path(projects_dir)

    if not projects_path.exists():
        return []

    for jsonl_file in projects_path.rglob("*.jsonl"):
        # Skip subagent files
        if "subagents" in str(jsonl_file):
            continue

        try:
            stat = jsonl_file.stat()
            session_files.append({
                "path": str(jsonl_file),
                "mtime": stat.st_mtime,
                "size": stat.st_size,
                "project": jsonl_file.parent.name,
            })
        except OSError:
            continue

    # Sort by modification time, most recent first
    session_files.sort(key=lambda x: x["mtime"], reverse=True)

    return session_files[:limit]


def main():
    parser = argparse.ArgumentParser(description="Extract Claude Code conversation history")
    parser.add_argument("--limit", type=int, default=5, help="Number of recent sessions to analyze")
    parser.add_argument("--project", type=str, default=None, help="Filter by project path substring")
    parser.add_argument("--detailed", action="store_true", help="Include full session JSONL analysis")
    args = parser.parse_args()

    claude_dir = Path.home() / ".claude"
    history_path = claude_dir / "history.jsonl"
    projects_dir = claude_dir / "projects"

    result = {
        "history_prompts": [],
        "session_details": [],
        "summary": {},
    }

    # Extract from global history
    if history_path.exists():
        result["history_prompts"] = extract_user_prompts_from_history(
            history_path, limit=args.limit * 3, project_filter=args.project
        )

    # Find and analyze recent session files
    if args.detailed and projects_dir.exists():
        recent_sessions = find_session_files(projects_dir, limit=args.limit)
        for session_info in recent_sessions:
            details = extract_session_details(session_info["path"])
            details["project"] = session_info["project"]
            details["last_modified"] = datetime.fromtimestamp(session_info["mtime"]).isoformat()
            result["session_details"].append(details)

    # Compute summary stats
    all_prompts = []
    for session in result["history_prompts"]:
        for p in session.get("prompts", []):
            all_prompts.append(p.get("text", ""))

    slash_commands_used = [p for p in all_prompts if p.startswith("/")]
    regular_prompts = [p for p in all_prompts if not p.startswith("/")]

    avg_prompt_length = 0
    if regular_prompts:
        avg_prompt_length = sum(len(p) for p in regular_prompts) / len(regular_prompts)

    result["summary"] = {
        "total_sessions_found": len(result["history_prompts"]),
        "total_prompts": len(all_prompts),
        "total_regular_prompts": len(regular_prompts),
        "total_slash_commands": len(slash_commands_used),
        "avg_prompt_length_chars": round(avg_prompt_length, 1),
        "slash_commands_breakdown": {},
        "short_prompts_count": len([p for p in regular_prompts if len(p) < 20]),
        "medium_prompts_count": len([p for p in regular_prompts if 20 <= len(p) < 100]),
        "long_prompts_count": len([p for p in regular_prompts if len(p) >= 100]),
    }

    # Count slash command usage
    for cmd in slash_commands_used:
        cmd_name = cmd.split()[0] if cmd else ""
        result["summary"]["slash_commands_breakdown"][cmd_name] = \
            result["summary"]["slash_commands_breakdown"].get(cmd_name, 0) + 1

    # Output
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
