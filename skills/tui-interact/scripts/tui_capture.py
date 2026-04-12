#!/usr/bin/env python3
"""Capture the current screen of a TUI application running in tmux.

Usage:
    tui_capture.py <session-name> [--mode text|screenshot] [--output path]

Modes:
    text       - Print plain text content of the terminal (default)
    screenshot - Render a PNG image with colors

The text mode prints to stdout. The screenshot mode saves a PNG file.
"""

import argparse
import subprocess
import sys
import re
import os
import time


def capture_pane(session: str, with_ansi: bool = False) -> str:
    """Capture tmux pane content."""
    cmd = ["tmux", "capture-pane", "-t", session, "-p"]
    if with_ansi:
        cmd.append("-e")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout


def render_screenshot(ansi_text: str, output_path: str):
    """Render ANSI text to a PNG image using Pillow."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print(
            "Error: Pillow is required for screenshot mode. Install with: pip3 install Pillow",
            file=sys.stderr,
        )
        sys.exit(1)

    ANSI_RE = re.compile(r"\033\[([0-9;]*)m")
    DEFAULT_FG = (255, 255, 255)
    DEFAULT_BG = (26, 26, 46)

    # Try to find a good monospace font with CJK support
    font = None
    font_size = 14
    font_candidates = [
        # macOS fonts with CJK support
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        # macOS monospace
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/SFMono-Regular.otf",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    ]
    for candidate in font_candidates:
        if os.path.exists(candidate):
            try:
                font = ImageFont.truetype(candidate, font_size)
                break
            except Exception:
                continue
    if font is None:
        font = ImageFont.load_default()

    # Measure character dimensions using a representative character
    # Use full-width char to test, fall back to 'M'
    bbox = font.getbbox("M")
    char_w = bbox[2] - bbox[0]
    char_h = int((bbox[3] - bbox[1]) * 2.2)

    # Check if CJK chars are wider (they usually take 2 columns)
    cjk_bbox = font.getbbox("\u4e2d")  # "中"
    cjk_char_w = cjk_bbox[2] - cjk_bbox[0] if cjk_bbox else char_w * 2

    lines = ansi_text.rstrip("\n").split("\n")
    padding = 12

    # Dynamically determine image width from the actual content
    # Query tmux pane width, or measure the longest line
    max_cols = 0
    strip_ansi = re.compile(r"\033\[[0-9;]*m")
    for line in lines:
        clean = strip_ansi.sub("", line)
        # Count columns: CJK chars take 2 columns
        cols = sum(2 if _is_wide_char(c) else 1 for c in clean)
        max_cols = max(max_cols, cols)
    max_cols = max(max_cols, 80)  # minimum 80 columns

    img_w = max_cols * char_w + padding * 2
    img_h = len(lines) * char_h + padding * 2

    img = Image.new("RGB", (img_w, img_h), color=DEFAULT_BG)
    draw = ImageDraw.Draw(img)

    def parse_sgr(params_str: str):
        """Parse SGR parameters and return (fg_color, is_bold, is_dim)."""
        if not params_str:
            return DEFAULT_FG, False, False
        params = []
        for p in params_str.split(";"):
            if p:
                try:
                    params.append(int(p))
                except ValueError:
                    pass

        fg = None
        bold = False
        dim = False
        i = 0
        while i < len(params):
            p = params[i]
            if p == 0:
                fg = DEFAULT_FG
                bold = False
                dim = False
            elif p == 1:
                bold = True
            elif p == 2:
                dim = True
            elif p == 39:
                fg = DEFAULT_FG
            elif p == 38 and i + 1 < len(params) and params[i + 1] == 2:
                if i + 4 < len(params):
                    fg = (params[i + 2], params[i + 3], params[i + 4])
                    i += 4
                else:
                    i = len(params)
            elif p == 38 and i + 1 < len(params) and params[i + 1] == 5:
                # 256-color mode - simplified mapping
                if i + 2 < len(params):
                    color_idx = params[i + 2]
                    fg = _256_to_rgb(color_idx)
                    i += 2
            # Basic 8 colors (30-37)
            elif 30 <= p <= 37:
                basic_colors = [
                    (0, 0, 0),        # black
                    (187, 0, 0),      # red
                    (0, 187, 0),      # green
                    (187, 187, 0),    # yellow
                    (0, 0, 187),      # blue
                    (187, 0, 187),    # magenta
                    (0, 187, 187),    # cyan
                    (187, 187, 187),  # white
                ]
                fg = basic_colors[p - 30]
            elif 90 <= p <= 97:
                bright_colors = [
                    (85, 85, 85),
                    (255, 85, 85),
                    (85, 255, 85),
                    (255, 255, 85),
                    (85, 85, 255),
                    (255, 85, 255),
                    (85, 255, 255),
                    (255, 255, 255),
                ]
                fg = bright_colors[p - 90]
            i += 1
        return fg or DEFAULT_FG, bold, dim

    y = padding
    for line in lines:
        x = padding
        current_fg = DEFAULT_FG

        parts = ANSI_RE.split(line)
        i = 0
        while i < len(parts):
            if i % 2 == 0:
                # Text segment
                text = parts[i]
                if text:
                    # Draw character by character for correct CJK spacing
                    for ch in text:
                        if ch == "\t":
                            x += char_w * 4
                            continue
                        # Check if CJK character (takes 2 columns in terminal)
                        is_wide = _is_wide_char(ch)
                        draw.text((x, y), ch, fill=current_fg, font=font)
                        if is_wide:
                            x += cjk_char_w
                        else:
                            x += char_w
            else:
                # ANSI params
                current_fg, _, _ = parse_sgr(parts[i])
            i += 1
        y += char_h

    # Downscale if the longest side exceeds MAX_PX to stay within viewer limits
    MAX_PX = 1800
    longest = max(img.width, img.height)
    if longest > MAX_PX:
        scale = MAX_PX / longest
        new_w = int(img.width * scale)
        new_h = int(img.height * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)

    img.save(output_path, optimize=True)
    print(f"Screenshot saved to {output_path} ({img.width}x{img.height})")


def _256_to_rgb(idx: int):
    """Convert 256-color index to RGB tuple."""
    if idx < 16:
        basic = [
            (0, 0, 0), (187, 0, 0), (0, 187, 0), (187, 187, 0),
            (0, 0, 187), (187, 0, 187), (0, 187, 187), (187, 187, 187),
            (85, 85, 85), (255, 85, 85), (85, 255, 85), (255, 255, 85),
            (85, 85, 255), (255, 85, 255), (85, 255, 255), (255, 255, 255),
        ]
        return basic[idx]
    elif idx < 232:
        idx -= 16
        r = (idx // 36) * 51
        g = ((idx % 36) // 6) * 51
        b = (idx % 6) * 51
        return (r, g, b)
    else:
        v = 8 + (idx - 232) * 10
        return (v, v, v)


def _is_wide_char(ch: str) -> bool:
    """Check if character is a wide (full-width) character in terminal."""
    cp = ord(ch)
    # CJK Unified Ideographs and common wide ranges
    if (
        0x4E00 <= cp <= 0x9FFF  # CJK Unified
        or 0x3000 <= cp <= 0x303F  # CJK Symbols
        or 0x3040 <= cp <= 0x309F  # Hiragana
        or 0x30A0 <= cp <= 0x30FF  # Katakana
        or 0xFF00 <= cp <= 0xFFEF  # Fullwidth forms
        or 0xF900 <= cp <= 0xFAFF  # CJK Compatibility
        or 0x20000 <= cp <= 0x2FA1F  # CJK Extension B+
        or 0xFE30 <= cp <= 0xFE4F  # CJK Compatibility Forms
        or 0x2E80 <= cp <= 0x2EFF  # CJK Radicals Supplement
    ):
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Capture TUI screen from tmux")
    parser.add_argument("session", help="tmux session name")
    parser.add_argument(
        "--mode",
        choices=["text", "screenshot"],
        default="text",
        help="Capture mode (default: text)",
    )
    parser.add_argument(
        "--output",
        help="Output file path (screenshot mode only)",
    )
    args = parser.parse_args()

    if args.mode == "text":
        text = capture_pane(args.session, with_ansi=False)
        print(text, end="")
    elif args.mode == "screenshot":
        if args.output:
            output = args.output
        else:
            # Default: per-session directory under /tmp/tui-interact/<session>/
            session_dir = f"/tmp/tui-interact/{args.session}"
            os.makedirs(session_dir, exist_ok=True)
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            output = f"{session_dir}/capture-{timestamp}.png"
        # Make sure parent dir exists even when --output is explicit
        os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
        ansi = capture_pane(args.session, with_ansi=True)
        render_screenshot(ansi, output)


if __name__ == "__main__":
    main()
