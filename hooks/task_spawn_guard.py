#!/usr/bin/env python3
"""ticket-tasuki Task spawn ガード (プラグインhook)

PreToolUse hook: ticket-tasuki:* の Task 直接起動をブロックし、
Agent Teams (team_name指定) 経由の起動は許可する。

Claude Code プラグインhook機構で ${CLAUDE_PLUGIN_ROOT}/hooks/task_spawn_guard.py として呼び出される。
"""

import json
import sys

# ブロック対象プレフィックス
BLOCKED_PREFIX = "ticket-tasuki:"

# ブロック時メッセージ
BLOCK_MESSAGE_TEMPLATE = """\
Task spawn規約: ticket-tasuki プラグインの直接起動禁止
━━━━━━━━━━━━━━━━━
検出: subagent_type="{subagent_type}"
対処:
1. Agent Teams（team_name指定）経由で起動してください
2. Task ツールでの ticket-tasuki:* subagent_type 直接指定は禁止です"""


def main():
    """stdinからPreToolUse入力JSONを読み、判定結果をstdoutに出力する"""
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # 入力不正は無視して許可
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Task":
        # Task以外は対象外
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    subagent_type = tool_input.get("subagent_type", "")

    # ブロック対象プレフィックスに一致しなければ許可
    if not subagent_type.startswith(BLOCKED_PREFIX):
        sys.exit(0)

    # team_nameが指定されていればAgent Teams経由なので許可
    team_name = tool_input.get("team_name", "")
    if team_name and team_name.strip():
        sys.exit(0)

    # ブロック: ticket-tasuki:* 直接起動 (team_name未指定)
    reason = BLOCK_MESSAGE_TEMPLATE.format(subagent_type=subagent_type)
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
