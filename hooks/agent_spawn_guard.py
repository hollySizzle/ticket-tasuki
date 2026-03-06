#!/usr/bin/env python3
"""ticket-tasuki Agent spawn ガード (プラグインhook)

PreToolUse hook:
- leaderによるAgent toolでのsub-agent直接起動をブロックし、TeamCreate経由を強制する。
- ビルトイン軽量エージェント（Explore, Plan, Bash等）は許可。
- subagent（agent_context="subagent"）からの呼び出しは制約対象外。
- team_name指定ありのAgent呼び出し（team agent経由）は許可。

Claude Code プラグインhook機構で ${CLAUDE_PLUGIN_ROOT}/hooks/agent_spawn_guard.py として呼び出される。
"""

import json
import sys

# team_name不要で許可するsubagent_type（ビルトイン軽量エージェント）
BUILTIN_WHITELIST = {
    "Explore", "Plan", "Bash",
    "statusline-setup", "claude-code-guide",
}

# ブロック時メッセージ
BLOCK_MESSAGE_TEMPLATE = """\
Agent tool規約: sub-agent直接起動の制限
━━━━━━━━━━━━━━━━━
検出: subagent_type="{subagent_type}"
対処:
1. TeamCreate でチームを作成し、Agent tool に team_name を指定して起動してください
2. sub-agent（Agent tool単独）でのticket-tasukiロール起動は禁止です
3. 軽量エージェント（Explore, Plan, Bash）はsub-agentで利用可能です"""


def _emit_and_exit(output: dict | None) -> None:
    """判定結果を出力して終了する。Noneなら出力なし（許可）"""
    if output is not None:
        print(json.dumps(output, ensure_ascii=False))
    sys.exit(0)


def main():
    """stdinからPreToolUse入力JSONを読み、判定結果をstdoutに出力する"""
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # 入力不正は無視して許可
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Agent":
        # Agent以外は対象外
        sys.exit(0)

    # agent_contextフィルタ: subagentは制約対象外
    agent_context = input_data.get("agent_context", "")
    if agent_context == "subagent":
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    subagent_type = tool_input.get("subagent_type", "")
    team_name = tool_input.get("team_name", "")

    # team_name指定あり → 許可（team agent経由）
    if team_name and team_name.strip():
        sys.exit(0)

    # ビルトインホワイトリスト → 許可
    if subagent_type in BUILTIN_WHITELIST:
        sys.exit(0)

    # それ以外 → deny
    reason = BLOCK_MESSAGE_TEMPLATE.format(subagent_type=subagent_type or "(未指定)")
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    _emit_and_exit(output)


if __name__ == "__main__":
    main()
