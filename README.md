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
  ├── scribe subagent → チケット読み取り
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

### C. プロジェクトのsettings.jsonに直接設定

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

## 依存

- **必須**: Claude Code、redmine-epic-grid MCP
- **推奨**: claude-nagger

## 構成

```
.claude-plugin/plugin.json       ← マニフェスト
agents/
  coder.md                       ← coder subagent（tools制限あり）
  tester.md                      ← tester subagent（Read/Bash/Glob/Grep）
  scribe.md                      ← scribe subagent（Redmine MCPのみ）
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
| scribe | agents/scribe.mdのtools: | 物理的制限 |
