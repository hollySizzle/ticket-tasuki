#!/usr/bin/env python3
"""ticket-tasuki Agent spawn ガード (プラグインhook)

PreToolUse hook:
- leaderによるAgent toolでのsub-agent直接起動をブロックし、TeamCreate経由を強制する。
- ビルトイン軽量エージェント（Explore, Plan等）は許可。
- subagent（agent_context="subagent"）からの呼び出しは制約対象外。
- team_name指定ありのAgent呼び出し（team agent経由）は許可。

Claude Code プラグインhook機構で ${CLAUDE_PLUGIN_ROOT}/hooks/agent_spawn_guard.py として呼び出される。
"""

import json
import re
import sys
from pathlib import Path

# team_name不要で許可するsubagent_type（ビルトイン軽量エージェント）
BUILTIN_WHITELIST = {
    "Explore", "Plan",
    "statusline-setup", "claude-code-guide",
}

# issue_{id}パターン（トレーサビリティチェック用）
ISSUE_ID_PATTERN = re.compile(r"issue_\d+")

# issue_{id}欠落時の警告メッセージ
ISSUE_ID_WARN_MESSAGE = """\
⚠ Agent promptにissue_{id}が含まれていません。
トレーサビリティのため、promptにissue_{id}（例: issue_1234）を含めてください。"""

# ブロック時メッセージ
BLOCK_MESSAGE_TEMPLATE = """\
Agent tool規約: sub-agent直接起動の制限
━━━━━━━━━━━━━━━━━
検出: subagent_type="{subagent_type}"
対処:
1. TeamCreate でチームを作成し、Agent tool に team_name を指定して起動してください
2. sub-agent（Agent tool単独）でのticket-tasukiロール起動は禁止です
3. 軽量エージェント（Explore, Plan）はsub-agentで利用可能です"""


def _has_issue_id(prompt: str) -> bool:
    """promptにissue_{id}パターンが含まれるか判定"""
    if not prompt:
        return False
    return bool(ISSUE_ID_PATTERN.search(prompt))


def _make_issue_id_warn_output() -> dict:
    """issue_{id}欠落時の警告出力を生成（ユーザー確認要求）"""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": ISSUE_ID_WARN_MESSAGE,
        }
    }


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
    prompt = tool_input.get("prompt", "")

    # --- issue_{id}トレーサビリティチェック ---
    issue_id_warn = None
    if not _has_issue_id(prompt):
        issue_id_warn = _make_issue_id_warn_output()

    # team_name指定あり → config.json実在確認（偽装対策）
    if team_name and team_name.strip():
        config_path = Path.home() / ".claude" / "teams" / team_name.strip() / "config.json"
        if config_path.exists():
            _emit_and_exit(issue_id_warn)
        # config.json不在 → フォールスルーしてdeny判定へ

    # ビルトインホワイトリスト → 許可
    if subagent_type in BUILTIN_WHITELIST:
        _emit_and_exit(issue_id_warn)

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
