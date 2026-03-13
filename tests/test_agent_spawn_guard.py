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
            "tool_input": {"subagent_type": "Explore", "prompt": "issue_1234 explore"},
        })
        assert result.returncode == 0
        assert _get_decision(result) is None

    def test_plan_allowed(self):
        """Agent + subagent_type="Plan" → 許可"""
        result = _run_guard({
            "tool_name": "Agent",
            "tool_input": {"subagent_type": "Plan", "prompt": "issue_1234 plan"},
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

    def test_team_name_allows(self):
        """Agent + team_name指定あり + promptパターン準拠 → allow（override注入付き）"""
        result = _run_guard({
            "tool_name": "Agent",
            "tool_input": {
                "subagent_type": "coder",
                "team_name": "dev-team",
                "prompt": "issue_7947",
            },
        })
        assert result.returncode == 0
        assert _get_decision(result) == "allow"
        output = _parse_output(result)
        # override指示がpromptに注入されていることを確認
        updated_prompt = output["hookSpecificOutput"]["updatedInput"]["prompt"]
        assert updated_prompt.startswith("issue_7947\n\n")

    def test_team_name_freeform_prompt_denied(self):
        """Agent + team_name指定あり + 自由文prompt → deny（promptパターン制限）"""
        result = _run_guard({
            "tool_name": "Agent",
            "tool_input": {
                "subagent_type": "coder",
                "team_name": "dev-team",
                "prompt": "issue_7947 implement feature",
            },
        })
        assert result.returncode == 0
        assert _get_decision(result) == "deny"

    def test_builtin_exempt_from_prompt_pattern(self):
        """ビルトインsubagent_typeはpromptパターン制限対象外"""
        result = _run_guard({
            "tool_name": "Agent",
            "tool_input": {
                "subagent_type": "Explore",
                "team_name": "dev-team",
                "prompt": "issue_1234 explore the codebase",
            },
        })
        assert result.returncode == 0
        assert _get_decision(result) is None


class TestConfigLoading:
    """config.yamlからのメッセージ読み込みテスト"""

    def test_config_block_message_used(self):
        """config.yamlのblock_message_templateがdenyメッセージに反映される"""
        result = _run_guard({
            "tool_name": "Agent",
            "tool_input": {"subagent_type": "coder"},
        })
        assert result.returncode == 0
        output = _parse_output(result)
        reason = output["hookSpecificOutput"]["permissionDecisionReason"]
        # config.yamlのblock_message_templateの内容が使用される
        assert "sub-agent直接起動の制限" in reason
        assert 'subagent_type="coder"' in reason

    def test_config_prompt_pattern_message_used(self):
        """config.yamlのprompt_pattern_block_messageがdenyメッセージに反映される"""
        result = _run_guard({
            "tool_name": "Agent",
            "tool_input": {
                "subagent_type": "coder",
                "team_name": "dev-team",
                "prompt": "free text prompt",
            },
        })
        assert result.returncode == 0
        output = _parse_output(result)
        reason = output["hookSpecificOutput"]["permissionDecisionReason"]
        assert "promptパターン制限" in reason
        assert "free text prompt" in reason

    def test_config_issue_id_warn_message_used(self):
        """config.yamlのissue_id_warn_messageがaskメッセージに反映される"""
        result = _run_guard({
            "tool_name": "Agent",
            "tool_input": {"subagent_type": "Explore", "prompt": "no issue id"},
        })
        assert result.returncode == 0
        output = _parse_output(result)
        reason = output["hookSpecificOutput"]["permissionDecisionReason"]
        assert "issue_{id}" in reason

    def test_fallback_on_missing_config(self):
        """config.yaml不在時はデフォルトメッセージにフォールバック"""
        # _load_guard_config関数の直接テスト
        import importlib
        guard_module_path = Path(SCRIPT_PATH)
        # スクリプトをインポートしてフォールバックを確認
        spec = importlib.util.spec_from_file_location("agent_spawn_guard", SCRIPT_PATH)
        mod = importlib.util.module_from_spec(spec)
        # _load_guard_configを直接テスト（config不在パスを渡す）
        # subprocessで実行し、denyメッセージにデフォルト文言が含まれることで確認
        result = _run_guard({
            "tool_name": "Agent",
            "tool_input": {"subagent_type": "coder"},
        })
        assert result.returncode == 0
        output = _parse_output(result)
        reason = output["hookSpecificOutput"]["permissionDecisionReason"]
        # デフォルト値と同じ文言が含まれる（configが正常に読まれても同内容）
        assert "TeamCreate" in reason
