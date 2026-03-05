#!/usr/bin/env python3
"""ticket-tasuki SessionStartクリーンアップ

SessionStart hook: セッション起動時（source=startup）に前セッションのチーム残骸を自動削除。
~/.claude/teams/ と ~/.claude/tasks/ を削除する。

resume/compact/clear時はスキップし、既存チーム情報を保護する。
"""

import json
import os
import shutil
import sys


# クリーンアップ対象ディレクトリ
CLEANUP_DIRS = [
    os.path.expanduser("~/.claude/teams"),
    os.path.expanduser("~/.claude/tasks"),
]


def main():
    """stdinからSessionStart入力JSONを読み、startup時のみクリーンアップを実行する"""
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    # source判定: startupのみ実行（resume/compact/clearはスキップ）
    source = input_data.get("source", "")
    if source != "startup":
        sys.exit(0)

    # 残骸削除
    for dir_path in CLEANUP_DIRS:
        if os.path.isdir(dir_path):
            try:
                shutil.rmtree(dir_path)
            except OSError:
                pass


if __name__ == "__main__":
    main()
