#!/usr/bin/env python3
"""ticket-tasuki leader行動制約ガード (プラグインhook)

PreToolUse hook: leaderのソースコード直接操作ツールおよびSerena MCPツールをブロックし、
subagentへの委譲を強制する。

Claude Code プラグインhook機構で ${CLAUDE_PLUGIN_ROOT}/hooks/leader_constraint_guard.py として呼び出される。
"""

import json
import sys

# ブロック対象ツール（完全一致）
BLOCKED_TOOLS = {"Read", "Edit", "Write", "Grep", "Glob", "MultiEdit"}

# ブロック対象MCPプレフィックス
BLOCKED_MCP_PREFIXES = ("mcp__serena__",)

# ブロック時メッセージ
BLOCK_MESSAGE_TEMPLATE = """\
[ticket-tasuki] leader行動制約: ソースコード操作の制限
━━━━━━━━━━━━━━━━━
検出: {tool_name}
対処:
1. ソースコード操作はTeam-Agentに委譲してください
2. 開発プロセス管理･チケット操作→PMO,調査→researcher、実装→coder、テスト→tester"""


def main():
    """stdinからPreToolUse入力JSONを読み、判定結果をstdoutに出力する"""
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # 入力不正は無視して許可
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Bash特別判定: gitコマンドのみ許可
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        if command.strip().startswith("git"):
            sys.exit(0)
        else:
            reason = BLOCK_MESSAGE_TEMPLATE.format(tool_name=f"Bash ({command[:50]})")
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
            print(json.dumps(output, ensure_ascii=False))
            sys.exit(0)

    # ブロック対象ツール判定（完全一致）
    is_blocked = tool_name in BLOCKED_TOOLS

    # MCPプレフィックス判定
    if not is_blocked:
        for prefix in BLOCKED_MCP_PREFIXES:
            if tool_name.startswith(prefix):
                is_blocked = True
                break

    if not is_blocked:
        sys.exit(0)

    # ブロック: deny で物理的ブロック
    reason = BLOCK_MESSAGE_TEMPLATE.format(tool_name=tool_name)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(output, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
