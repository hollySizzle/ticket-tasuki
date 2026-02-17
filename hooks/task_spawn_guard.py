#!/usr/bin/env python3
"""ticket-tasuki Task spawn ガード (プラグインhook)

PreToolUse hook: ticket-tasuki:* の Task 直接起動をブロックし、
Agent Teams (team_name指定) 経由の起動は許可する。
また、ブロック後にgeneral-purpose等で同等作業を迂回実行するケースを検知・警告する。
promptにissue_{id}が含まれない場合は警告を出す（ブロックはしない）。

Claude Code プラグインhook機構で ${CLAUDE_PLUGIN_ROOT}/hooks/task_spawn_guard.py として呼び出される。
"""

import json
import os
import re
import sys
import tempfile
import time

# ブロック対象プレフィックス
BLOCKED_PREFIX = "ticket-tasuki:"

# ブロック時メッセージ (#6103: 迂回禁止を明記)
BLOCK_MESSAGE_TEMPLATE = """\
Task spawn規約: ticket-tasuki プラグインの直接起動禁止
━━━━━━━━━━━━━━━━━
検出: subagent_type="{subagent_type}"
対処:
1. Agent Teams（team_name指定）経由で起動してください
2. Task ツールでの ticket-tasuki:* subagent_type 直接指定は禁止です

⚠ 迂回禁止: general-purpose エージェント等の代替エージェントで
同等の作業を実行することも禁止されています。
必ず Agent Teams 経由で正規の手順に従ってください。"""

# 迂回検知時の警告メッセージ
CIRCUMVENTION_WARNING_TEMPLATE = """\
⚠ 迂回検知: ticket-tasuki 直接起動ブロック直後の代替エージェント起動
━━━━━━━━━━━━━━━━━
直前にブロックされた subagent_type: "{blocked_type}"
現在の subagent_type: "{current_type}"

ticket-tasuki:* のブロック後に、general-purpose 等の代替エージェントで
同等の作業を実行することは禁止されています。
Agent Teams（team_name指定）経由で正規の手順に従ってください。

この起動が ticket-tasuki と無関係な正当な目的であれば許可してください。"""

# ブロック記録の有効期間（秒）: ブロック後この時間内の代替spawn を検知
BLOCK_RECORD_TTL = 300

# 迂回検知の対象となるsubagent_type（team_name未指定の場合のみ）
CIRCUMVENTION_TARGET_TYPES = {"general-purpose", ""}

# issue_{id}パターン（トレーサビリティチェック用）
ISSUE_ID_PATTERN = re.compile(r"issue_\d+")

# issue_{id}欠落時の警告メッセージ
ISSUE_ID_WARN_MESSAGE = """\
⚠ Task promptにissue_{id}が含まれていません。
トレーサビリティのため、promptにissue_{id}（例: issue_1234）を含めてください。"""

# プロンプト内の迂回疑い検出パターン
CIRCUMVENTION_PROMPT_PATTERNS = [
    r"ticket[-_]?tasuki",
    r"redmine",
    r"チケット.{0,10}(管理|操作|作成|更新|起票|コメント)",
    r"issue.{0,10}(create|update|comment|assign|status)",
    r"(起票|コメント追記|ステータス変更|チケット更新)",
]


def _get_block_record_path(session_id: str) -> str:
    """セッション固有のブロック記録ファイルパスを返す"""
    return os.path.join(
        tempfile.gettempdir(),
        f"task_spawn_guard_block_{session_id}.json",
    )


def _record_block(session_id: str, subagent_type: str) -> None:
    """ブロック発生を記録する"""
    path = _get_block_record_path(session_id)
    record = {
        "blocked_type": subagent_type,
        "blocked_at": time.time(),
        "session_id": session_id,
    }
    try:
        with open(path, "w") as f:
            json.dump(record, f)
    except OSError:
        pass  # 記録失敗は無視（ガードの主機能に影響しない）


def _check_recent_block(session_id: str) -> dict | None:
    """直近のブロック記録を確認。TTL超過または存在しなければNoneを返す"""
    path = _get_block_record_path(session_id)
    try:
        with open(path) as f:
            record = json.load(f)
        blocked_at = record.get("blocked_at", 0)
        if time.time() - blocked_at <= BLOCK_RECORD_TTL:
            return record
    except (OSError, json.JSONDecodeError, KeyError):
        pass
    return None


def _has_issue_id(prompt: str) -> bool:
    """promptにissue_{id}パターンが含まれるか判定"""
    if not prompt:
        return False
    return bool(ISSUE_ID_PATTERN.search(prompt))


def _emit_and_exit(output: dict | None) -> None:
    """判定結果を出力して終了する。Noneなら出力なし（許可）"""
    if output is not None:
        print(json.dumps(output, ensure_ascii=False))
    sys.exit(0)


def _make_issue_id_warn_output() -> dict:
    """issue_{id}欠落時の警告出力を生成"""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecisionReason": ISSUE_ID_WARN_MESSAGE,
        }
    }


def _prompt_suggests_circumvention(prompt: str) -> bool:
    """プロンプト内容がticket-tasuki関連の作業を示唆するか判定"""
    if not prompt:
        return False
    prompt_lower = prompt.lower()
    for pattern in CIRCUMVENTION_PROMPT_PATTERNS:
        if re.search(pattern, prompt_lower, re.IGNORECASE):
            return True
    return False


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

    session_id = input_data.get("session_id", "")
    tool_input = input_data.get("tool_input", {})
    subagent_type = tool_input.get("subagent_type", "")
    team_name = tool_input.get("team_name", "")
    prompt = tool_input.get("prompt", "")

    # --- issue_{id}トレーサビリティチェック (#6218) ---
    # promptにissue_{id}が含まれない場合、警告を出す（ブロックはしない）
    issue_id_warn = None
    if not _has_issue_id(prompt):
        issue_id_warn = _make_issue_id_warn_output()

    # --- ticket-tasuki:* 直接起動ブロック判定 ---
    if subagent_type.startswith(BLOCKED_PREFIX):
        # team_nameが指定されていればAgent Teams経由なので許可
        if team_name and team_name.strip():
            # 既存ブロック判定より強い判定はないので、issue_id警告を出して終了
            _emit_and_exit(issue_id_warn)

        # ブロック: ticket-tasuki:* 直接起動 (team_name未指定)
        # deny判定はissue_id警告より優先
        if session_id:
            _record_block(session_id, subagent_type)

        reason = BLOCK_MESSAGE_TEMPLATE.format(subagent_type=subagent_type)
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
        _emit_and_exit(output)

    # --- 迂回検知: ブロック直後の代替エージェントspawn (#6102) ---
    # team_name指定済みの正当な起動は対象外
    if team_name and team_name.strip():
        _emit_and_exit(issue_id_warn)

    # 迂回検知の対象subagent_typeでなければスキップ
    if subagent_type not in CIRCUMVENTION_TARGET_TYPES:
        _emit_and_exit(issue_id_warn)

    # セッション内で直近のブロック記録を確認
    if not session_id:
        _emit_and_exit(issue_id_warn)

    block_record = _check_recent_block(session_id)
    if not block_record:
        _emit_and_exit(issue_id_warn)

    # プロンプト内容を確認: ticket-tasuki関連の作業を示唆する場合のみ警告
    description = tool_input.get("description", "")
    combined_text = f"{prompt}\n{description}"

    if not _prompt_suggests_circumvention(combined_text):
        # プロンプトにticket-tasuki関連の示唆がなければ正当な使用とみなす
        _emit_and_exit(issue_id_warn)

    # 迂回疑い: ユーザー確認を求める（ask = 硬いブロックではなく確認ダイアログ）
    # ask判定はissue_id警告より優先
    blocked_type = block_record.get("blocked_type", "unknown")
    reason = CIRCUMVENTION_WARNING_TEMPLATE.format(
        blocked_type=blocked_type,
        current_type=subagent_type or "(未指定)",
    )
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }
    _emit_and_exit(output)


if __name__ == "__main__":
    main()
