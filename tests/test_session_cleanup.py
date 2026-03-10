#!/usr/bin/env python3
"""session_cleanup.py のテスト

subprocess.runで実スクリプトを呼び出し、動作を検証する。
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPT_PATH = str(
    Path(__file__).resolve().parent.parent / "hooks" / "session_cleanup.py"
)


def _run_session_cleanup(input_data: dict, env: dict | None = None) -> subprocess.CompletedProcess:
    """session_cleanup.pyを実行し結果を返す"""
    return subprocess.run(
        [sys.executable, SCRIPT_PATH],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )


class TestEnsureVibesFiles:
    """vibes_documentation_standards.md自動配置のテスト"""

    def test_creates_file_when_missing(self, tmp_path):
        """CWDにvibes_documentation_standards.mdが存在しない場合、テンプレートからコピーされる"""
        result = _run_session_cleanup({
            "source": "startup",
            "cwd": str(tmp_path),
        })
        assert result.returncode == 0
        dest = tmp_path / "vibes" / "docs" / "rules" / "vibes_documentation_standards.md"
        assert dest.exists(), "vibes_documentation_standards.md が自動配置されるべき"
        # テンプレートの内容と一致確認
        template = Path(__file__).resolve().parent.parent / "templates" / "vibes_documentation_standards.md"
        assert dest.read_text() == template.read_text()

    def test_skips_when_file_exists(self, tmp_path):
        """既存ファイルがある場合は上書きしない"""
        dest = tmp_path / "vibes" / "docs" / "rules" / "vibes_documentation_standards.md"
        dest.parent.mkdir(parents=True)
        existing_content = "# カスタム内容"
        dest.write_text(existing_content)

        result = _run_session_cleanup({
            "source": "startup",
            "cwd": str(tmp_path),
        })
        assert result.returncode == 0
        assert dest.read_text() == existing_content, "既存ファイルは上書きされないべき"

    def test_creates_directories(self, tmp_path):
        """vibes/docs/rules/ ディレクトリが存在しない場合も自動作成される"""
        result = _run_session_cleanup({
            "source": "resume",
            "cwd": str(tmp_path),
        })
        assert result.returncode == 0
        dest = tmp_path / "vibes" / "docs" / "rules" / "vibes_documentation_standards.md"
        assert dest.exists(), "ディレクトリ自動作成+ファイル配置されるべき"

    def test_runs_on_resume(self, tmp_path):
        """source=resume時もファイル自動配置は実行される"""
        result = _run_session_cleanup({
            "source": "resume",
            "cwd": str(tmp_path),
        })
        assert result.returncode == 0
        dest = tmp_path / "vibes" / "docs" / "rules" / "vibes_documentation_standards.md"
        assert dest.exists(), "resume時もファイル配置されるべき"

    def test_runs_on_compact(self, tmp_path):
        """source=compact時もファイル自動配置は実行される"""
        result = _run_session_cleanup({
            "source": "compact",
            "cwd": str(tmp_path),
        })
        assert result.returncode == 0
        dest = tmp_path / "vibes" / "docs" / "rules" / "vibes_documentation_standards.md"
        assert dest.exists(), "compact時もファイル配置されるべき"


class TestSessionCleanup:
    """チーム残骸クリーンアップのテスト"""

    def test_cleanup_on_startup(self, tmp_path):
        """source=startup時にクリーンアップ対象ディレクトリが削除される"""
        # テスト用のHOMEを設定してクリーンアップ対象を作成
        fake_home = tmp_path / "home"
        teams_dir = fake_home / ".claude" / "teams"
        tasks_dir = fake_home / ".claude" / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)
        (teams_dir / "dummy.json").write_text("{}")
        (tasks_dir / "dummy.json").write_text("{}")

        env = {**os.environ, "HOME": str(fake_home)}
        result = _run_session_cleanup({
            "source": "startup",
            "cwd": str(tmp_path),
        }, env=env)
        assert result.returncode == 0
        assert not teams_dir.exists(), "teams/が削除されるべき"
        assert not tasks_dir.exists(), "tasks/が削除されるべき"

    def test_no_cleanup_on_resume(self, tmp_path):
        """source=resume時はクリーンアップをスキップする"""
        fake_home = tmp_path / "home"
        teams_dir = fake_home / ".claude" / "teams"
        teams_dir.mkdir(parents=True)
        (teams_dir / "dummy.json").write_text("{}")

        env = {**os.environ, "HOME": str(fake_home)}
        result = _run_session_cleanup({
            "source": "resume",
            "cwd": str(tmp_path),
        }, env=env)
        assert result.returncode == 0
        assert teams_dir.exists(), "resume時はteams/が残るべき"
