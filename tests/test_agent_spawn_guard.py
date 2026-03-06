#!/usr/bin/env python3
"""agent_spawn_guard.py のテスト

subprocess.runで実スクリプトを呼び出し、判定結果を検証する。
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPT_PATH = str(
    Path(__file__).resolve().parent.parent / "hooks" / "agent_spawn_guard.py"
)


def _run_guard(input_data: dict, env: dict | None = None) -> subprocess.CompletedProcess:
    """ガードスクリプトを実行し結果を返す"""
    return subprocess.run(
        [sys.executable, SCRIPT_PATH],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )


def _parse_output(result: subprocess.CompletedProcess) -> dict | None:
    """stdout をパースして判定結果を返す。出力なしならNone"""
    stdout = result.stdout.strip()
    if not stdout:
        return None
    return json.loads(stdout)


def _get_decision(result: subprocess.CompletedProcess) -> str | None:
    """判定結果からpermissionDecisionを取得"""
    output = _parse_output(result)
    if output is None:
        return None
    return output["hookSpecificOutput"]["permissionDecision"]


class TestAgentSpawnGuardDeny:
    """ブロックされるべきケース"""

    def test_coder_denied(self):
        """Agent + subagent_type="coder" → deny"""
        result = _run_guard({
            "tool_name": "Agent",
            "tool_input": {"subagent_type": "coder"},
        })
        assert result.returncode == 0
        assert _get_decision(result) == "deny"

    def test_tech_lead_denied(self):
        """Agent + subagent_type="tech-lead" → deny"""
        result = _run_guard({
            "tool_name": "Agent",
            "tool_input": {"subagent_type": "tech-lead"},
        })
        assert result.returncode == 0
        assert _get_decision(result) == "deny"

    def test_prefixed_coder_denied(self):
        """Agent + subagent_type="ticket-tasuki:coder" → deny（プレフィックス付き）"""
        result = _run_guard({
            "tool_name": "Agent",
            "tool_input": {"subagent_type": "ticket-tasuki:coder"},
        })
        assert result.returncode == 0
        assert _get_decision(result) == "deny"


class TestAgentSpawnGuardAllow:
    """許可されるべきケース"""

    def test_explore_allowed(self):
        """Agent + subagent_type="Explore" → 許可"""
        result = _run_guard({
            "tool_name": "Agent",
            "tool_input": {"subagent_type": "Explore"},
        })
        assert result.returncode == 0
        assert _get_decision(result) is None

    def test_plan_allowed(self):
        """Agent + subagent_type="Plan" → 許可"""
        result = _run_guard({
            "tool_name": "Agent",
            "tool_input": {"subagent_type": "Plan"},
        })
        assert result.returncode == 0
        assert _get_decision(result) is None

    def test_bash_denied(self):
        """Agent + subagent_type="Bash" → deny（ホワイトリスト外）"""
        result = _run_guard({
            "tool_name": "Agent",
            "tool_input": {"subagent_type": "Bash"},
        })
        assert result.returncode == 0
        assert _get_decision(result) == "deny"

    def test_general_purpose_denied(self):
        """Agent + subagent_type="general-purpose" → deny（task_spawn_guard迂回防止）"""
        result = _run_guard({
            "tool_name": "Agent",
            "tool_input": {"subagent_type": "general-purpose"},
        })
        assert result.returncode == 0
        assert _get_decision(result) == "deny"

    def test_empty_subagent_type_denied(self):
        """Agent + subagent_type="" → deny"""
        result = _run_guard({
            "tool_name": "Agent",
            "tool_input": {"subagent_type": ""},
        })
        assert result.returncode == 0
        assert _get_decision(result) == "deny"

    def test_subagent_context_bypasses(self):
        """Agent + agent_context="subagent" → 対象外（どのsubagent_typeでも許可）"""
        result = _run_guard({
            "tool_name": "Agent",
            "agent_context": "subagent",
            "tool_input": {"subagent_type": "coder"},
        })
        assert result.returncode == 0
        assert _get_decision(result) is None

    def test_non_agent_tool_ignored(self):
        """tool_name="Read" → 対象外"""
        result = _run_guard({
            "tool_name": "Read",
            "tool_input": {},
        })
        assert result.returncode == 0
        assert _get_decision(result) is None

    def test_team_name_allows(self, tmp_path):
        """Agent + team_name指定あり＋config.json実在 → 許可"""
        # config.jsonを配置した仮HOMEを作成
        config_dir = tmp_path / ".claude" / "teams" / "dev-team"
        config_dir.mkdir(parents=True)
        (config_dir / "config.json").write_text("{}")
        env = {**os.environ, "HOME": str(tmp_path)}

        result = _run_guard({
            "tool_name": "Agent",
            "tool_input": {
                "subagent_type": "coder",
                "team_name": "dev-team",
            },
        }, env=env)
        assert result.returncode == 0
        assert _get_decision(result) is None

    def test_fake_team_name_denied(self):
        """Agent + team_name指定あり＋config.json不在 → deny（偽装対策）"""
        env = {**os.environ, "HOME": tempfile.mkdtemp()}
        result = _run_guard({
            "tool_name": "Agent",
            "tool_input": {
                "subagent_type": "coder",
                "team_name": "fake-team",
            },
        }, env=env)
        assert result.returncode == 0
        assert _get_decision(result) == "deny"
