#!/usr/bin/env python3
"""ticket-tasuki SessionStartクリーンアップ + 必須ファイル自動配置

SessionStart hook:
- セッション起動時（source=startup）に前セッションのチーム残骸を自動削除
- vibes_documentation_standards.md がプロジェクトルートに未配置の場合、テンプレートからコピー

resume/compact/clear時はクリーンアップをスキップし、既存チーム情報を保護する。
ファイル自動配置はsource問わず毎回実行する。
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

# プラグインルートからの相対パス
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 自動配置対象: (プロジェクトルートからの相対パス, テンプレートファイル名)
AUTO_PLACE_FILES = [
    (
        "vibes/docs/rules/vibes_documentation_standards.md",
        os.path.join(PLUGIN_ROOT, "templates", "vibes_documentation_standards.md"),
    ),
    (
        "vibes/docs/rules/ticket_comment_templates.md",
        os.path.join(PLUGIN_ROOT, "templates", "ticket_comment_templates.md"),
    ),
    (
        "vibes/docs/rules/ticket_conventions.md",
        os.path.join(PLUGIN_ROOT, "templates", "ticket_conventions.md"),
    ),
    (
        "vibes/docs/rules/tasuki_workflow.md",
        os.path.join(PLUGIN_ROOT, "templates", "tasuki_workflow.md"),
    ),
]


def ensure_vibes_files(cwd: str) -> None:
    """プロジェクトルート（CWD）に必須ファイルが存在しない場合、テンプレートからコピーする"""
    for relative_dest, template_src in AUTO_PLACE_FILES:
        dest_path = os.path.join(cwd, relative_dest)
        if os.path.exists(dest_path):
            continue
        if not os.path.exists(template_src):
            continue
        # ディレクトリが存在しない場合は作成
        dest_dir = os.path.dirname(dest_path)
        os.makedirs(dest_dir, exist_ok=True)
        shutil.copy2(template_src, dest_path)


def main():
    """stdinからSessionStart入力JSONを読み、処理を実行する"""
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    # 必須ファイル自動配置（source問わず毎回実行）
    cwd = input_data.get("cwd", os.getcwd())
    ensure_vibes_files(cwd)

    # source判定: startupのみクリーンアップ実行（resume/compact/clearはスキップ）
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
