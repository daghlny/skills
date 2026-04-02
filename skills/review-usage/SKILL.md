---
name: review-usage
description: "Review and analyze the user's Claude Code conversation history to provide actionable improvement suggestions for prompting style, workflow patterns, and feature utilization. Use this skill when the user asks to review their usage, improve their prompting, analyze their conversation history, or wants tips on how to use Claude Code more effectively. Also trigger when the user mentions wanting to get better at using Claude Code, asks about their usage patterns, or says things like 'how can I use you better', 'review my history', 'analyze my conversations', or 'improve my workflow'."
user_invocable: true
argument: "[N] - number of recent sessions to analyze (default: 5)"
---

# Review Usage - Claude Code 使用分析与改进建议

This skill analyzes the user's Claude Code conversation history and produces a structured improvement report in Chinese (Simplified).

## How it works

1. Run the extraction script to gather conversation data
2. Read and analyze the extracted data
3. Produce a structured report with actionable suggestions

## Step 1: Extract conversation history

Run the extraction script bundled with this skill. The script reads from `~/.claude/history.jsonl` (global prompt history) and `~/.claude/projects/` (detailed session data).

```bash
python3 <skill-path>/scripts/extract_history.py --limit <N> --detailed
```

Where `<N>` is the number of sessions to analyze (default 5, or use the user's argument).

If the user specifies a project, add `--project <path-substring>`.

## Step 2: Analyze the data

After running the script, read the JSON output carefully. Focus on these dimensions:

### A. Prompt Quality (提示词质量)
- **Clarity**: Are prompts specific or vague? "fix the bug" vs "fix the null pointer exception in UserService.getUser when the user ID doesn't exist"
- **Context provided**: Do prompts include relevant context (file paths, error messages, expected behavior)?
- **Prompt length distribution**: Very short prompts (<20 chars) often lack context; very long prompts might be unfocused
- **Language**: Does the user provide prompts in a language Claude handles well? Do they mix languages effectively?

### B. Workflow Patterns (工作流模式)
- **Planning**: Does the user plan before jumping into implementation?
- **Iterative refinement**: Does the user review results and iterate, or accept first outputs?
- **Task decomposition**: Does the user break complex tasks into smaller steps?
- **Context continuity**: Does the user maintain context across conversations or start fresh each time?

### C. Feature Utilization (功能利用)
- **Slash commands**: Which ones are used? Which useful ones are missing?
  - `/plan` for complex tasks
  - `/review-pr` for code reviews
  - `/commit` for git commits
  - `/simplify` for code quality
- **Tools awareness**: Does the user leverage Claude Code's tool capabilities (file reading, code search, running tests)?
- **Agent delegation**: Does the user delegate complex research to subagents?
- **Memory/CLAUDE.md**: Does the user maintain project memory for better context?

### D. Anti-patterns (反模式)
- Repeating the same instruction multiple times (sign of unclear initial prompt)
- Not providing error messages when reporting bugs
- Asking Claude to do things the user could do faster themselves
- Not reviewing Claude's output before accepting it
- Overly micro-managing step-by-step when a high-level instruction would suffice

## Step 3: Generate the report

Output the report in Chinese (Simplified) using this structure:

```
# Claude Code 使用分析报告

## 📊 基本统计
- 分析会话数: X
- 总提示数: X
- 平均提示长度: X 字符
- 斜杠命令使用: X 次

## 🔍 当前使用模式分析

### 提示词风格
[分析用户的提示词特点，给出具体例子]

### 工作流习惯
[分析用户的工作流程模式]

### 功能利用情况
[分析用户使用了哪些 Claude Code 功能，哪些未充分利用]

## 💡 改进建议

### 1. 提示词优化
[具体的改进建议，附带 before/after 示例]

**改进前**: [用户实际使用的提示词]
**改进后**: [建议的更好写法]
**原因**: [为什么这样更好]

### 2. 工作流优化
[工作流程的改进建议]

### 3. 推荐尝试的功能
[用户可能不知道或未充分利用的 Claude Code 功能]

## ⚡ 快速改进清单
- [ ] [最重要的改进项1]
- [ ] [最重要的改进项2]
- [ ] [最重要的改进项3]
```

## Important guidelines

- Be specific and actionable — generic advice like "write clearer prompts" isn't helpful without concrete examples from the user's actual history
- Use the user's real prompts as before/after examples (but don't expose any sensitive content like API keys or passwords if they appear in history)
- Be encouraging — highlight what the user is doing well, not just what needs improvement
- Prioritize suggestions by impact — the most impactful improvements should come first
- If there isn't enough history data to draw meaningful conclusions, say so honestly and suggest the user come back after more usage
- If data extraction fails or is empty, inform the user and suggest they check their Claude Code version/setup
