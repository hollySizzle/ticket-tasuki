# ticket-tasuki

TiDD基盤のleader/coder分離プラグイン。

## 概要

1セッション内でleader（意思決定）とcoder（実装）を分離し、コンテキスト保護・バイアス排除・レビュー品質向上を実現する。

## アーキテクチャ

```
leader（メインエージェント）
  やること: 読む・判断する・指示する・レビューする
  やらないこと: コード編集
  │
  ├── coder subagent → コード実装・単体テスト
  ├── tester subagent → 受入テスト・E2Eテスト
  ├── pmo subagent（常駐） → ワークフロー相談・チケット管理・プロセス監査
  ├── tech-lead subagent（常駐） → 設計レビュー・コード品質チェック
  ├── Explore subagent → コード調査
  └── general-purpose subagent → Web調査
```

## インストール

### A. マーケットプレイス経由（推奨）

```bash
# マーケットプレイス追加
/plugin marketplace add hollySizzle/ticket-tasuki

# プラグインインストール
/plugin install ticket-tasuki@hollySizzle-ticket-tasuki
```

### B. ローカルディレクトリ指定

```bash
git clone https://github.com/hollySizzle/ticket-tasuki.git
claude --plugin-dir ./ticket-tasuki
```

### C. プロジェクトのsettings.jsonに直接設定（GitHub）

```json
{
  "extraKnownMarketplaces": {
    "ticket-tasuki": {
      "source": {
        "source": "github",
        "repo": "hollySizzle/ticket-tasuki"
      }
    }
  },
  "enabledPlugins": {
    "ticket-tasuki@ticket-tasuki": true
  }
}
```

### D. ローカルディレクトリをsettings.jsonで指定（カスタマイズ推奨）

規約・agent定義・hookをプロジェクトに合わせてカスタマイズしたい場合はこの方法を推奨。

方法A〜Cはプラグイン実体が `~/.claude/plugins/cache/` にコピーされるため、`claude plugin update` やcache clearで編集内容が失われる。この方法はローカルディレクトリを直接参照するため、上書きリスクがない。

#### 手順

1. リポジトリをclone:

```bash
git clone https://github.com/hollySizzle/ticket-tasuki.git /path/to/ticket-tasuki
```

2. `.claude/settings.json` に `directory` ソースを設定:

```json
{
  "extraKnownMarketplaces": {
    "ticket-tasuki": {
      "source": {
        "source": "directory",
        "path": "/path/to/ticket-tasuki"
      }
    }
  },
  "enabledPlugins": {
    "ticket-tasuki@ticket-tasuki": true
  }
}
```

`path` は絶対パスで指定すること。

3. 必要に応じてカスタマイズ:

| カスタマイズ対象 | ファイル | 例 |
|-----------------|---------|-----|
| leader規約 | `CLAUDE.md` | ワークフロー変更・規約追加 |
| coder制約 | `agents/coder.md` | tools許可リスト変更 |
| tester制約 | `agents/tester.md` | テスト方針変更 |
| pmo制約 | `agents/pmo.md` | 監査基準変更 |
| tech-lead制約 | `agents/tech-lead.md` | レビュー基準変更 |
| スキル | `skills/*/SKILL.md` | 委譲テンプレート変更 |
| hook | `hooks/hooks.json` | ガードルール変更 |

4. 変更はローカルgitで管理可能。上流の更新を取り込みたい場合は `git pull` で手動マージ。

## 依存

- **必須**: Claude Code、redmine-epic-grid MCP
- **推奨**: claude-nagger

## claude-naggarセットアップ（任意）

ticket-tasukiはclaude-naggarなしでも動作しますが、併用するとleader規約の通知・subagent別の規約ガードレールが有効になります。

### 1. claude-naggarのインストール

```bash
pip install claude-nagger
```

詳細: https://github.com/hollySizzle/claude-nagger

### 2. 設定ファイルの配置

本プラグインに同梱のサンプル設定を、プロジェクトの`.claude-nagger/`にコピーしてください:

```bash
cp -r .claude/my_plugins/ticket-tasuki/.claude-nagger/ .claude-nagger/
```

または手動で以下を配置:
- `.claude-nagger/config.yaml` — セッション規約・subagent別override
- `.claude-nagger/file_conventions.yaml` — ファイル編集規約
- `.claude-nagger/command_conventions.yaml` — コマンド実行規約

### 3. Claude Codeのhooks設定

`.claude/settings.json`（または`.claude/settings.local.json`）にフックを追加:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "",
        "hooks": [{ "type": "command", "command": "claude-nagger hook session-startup" }]
      },
      {
        "matcher": "Edit",
        "hooks": [{ "type": "command", "command": "claude-nagger hook implementation-design" }]
      },
      {
        "matcher": "Write",
        "hooks": [{ "type": "command", "command": "claude-nagger hook implementation-design" }]
      },
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "claude-nagger hook implementation-design" }]
      }
    ]
  }
}
```

### 4. 設定のカスタマイズ

サンプルのコメントアウトされたルールを参考に、プロジェクトに合わせてカスタマイズしてください。

## 構成

```
.claude-plugin/plugin.json       ← マニフェスト
agents/
  coder.md                       ← coder subagent（tools制限あり）
  tester.md                      ← tester subagent（Read/Bash/Glob/Grep）
  pmo.md                         ← pmo subagent（常駐、チケットCRUD・監査）
  tech-lead.md                   ← tech-lead subagent（常駐、読み取り専用）
skills/
  tasuki-setup/SKILL.md          ← セットアップskill
  tasuki-delegate/SKILL.md       ← coder委譲skill
hooks/hooks.json                 ← フック定義
CLAUDE.md                        ← leader規約（ソフト制約）
.claude-nagger/                  ← claude-nagger設定テンプレート（任意）
```

## 制御方式

| 対象 | 制御手段 | 強制力 |
|------|---------|--------|
| leader | CLAUDE.md指示 | ソフト制約 |
| coder | agents/coder.mdのtools: | 物理的制限 |
| tester | agents/tester.mdのtools: | 物理的制限 |
| pmo | agents/pmo.mdのtools: | 物理的制限 |
| tech-lead | agents/tech-lead.mdのtools: | 物理的制限 |
