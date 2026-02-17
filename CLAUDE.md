# ticket-tasuki 共通規約

ticket-tasukiプラグインの共通情報。役割別の規約はセッション開始時に通知される。

## 利用可能なsubagent

| subagent | 種別 | 用途 |
|----------|------|------|
| pmo | 常駐 | プロセス監査・ワークフロー相談・チケット管理（CRUD） |
| tech-lead | 常駐 | 技術レビュー（設計整合性・ドキュメント整合性・コード品質） |
| coder | 都度起動 | コード実装（Edit/Write/Bash）。実装後tech-leadにレビュー依頼 |
| tester | 都度起動 | 受入テスト・E2Eテスト |
| researcher | 都度起動 | 技術調査・コードベース調査（読み取り専用） |

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
