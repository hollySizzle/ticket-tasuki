# ticket-tasuki 共通規約

ticket-tasukiプラグインの共通情報。役割別の規約はセッション開始時に通知される。

## 利用可能なsubagent

| subagent | 用途 |
|----------|------|
| coder | コード実装（Edit/Write/Bash） |
| scribe | Redmineチケット管理（CRUD・階層管理・バージョン管理） |
| tester | 受入テスト・E2Eテスト |
| tech-lead | 技術レビュー（設計整合性・ドキュメント整合性・コード品質） |
| Explore | コードベース調査（読み取り専用） |
| Bash | テスト実行・コマンド実行 |
| general-purpose | Web調査・複合タスク |

## ticket-tasuki作業ディレクトリ

ticket-tasukiのソースコードは以下のディレクトリで管理する:

```
/workspace/packages/claude-nagger/.claude/plugins/ticket-tasuki/
```

- このディレクトリは独立したgitリポジトリ（origin: github.com/hollySizzle/ticket-tasuki）
- コミット・pushはこのディレクトリ内で実行すること
- `/workspace/packages/ticket-tasuki/` は使用しない（削除済み）

## 注意事項

- この規約はソフト制約です（CLAUDE.md指示による遵守依頼）
- coder subagentのtools制限は物理的強制（Claude Code本体が制御）
- 1US = 1セッションを推奨（セッション終了時にチケットでコンテキスト保存）

## ticket-tasuki開発ワークフロー

1. agents/*.mdまたはプラグインファイルを編集
2. .claude-plugin/plugin.json のバージョンをバンプ（必須）
3. git commit & push
4. Claude Codeセッション再起動で反映

**注意**: バージョンバンプなしのファイル追加はキャッシュに反映されない
