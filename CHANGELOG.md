# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.3.1] - 2026-03-22

### 設計意図コメント追記
- task_spawn_guard.py docstringにagent_spawn_guardセクション共有の設計意図コメント追記 (issue_8562)

## [0.3.0] - 2026-03-19

### エスカレーション機構・規約拡充
- tasuki_workflow.mdにバグ起票エスカレーションフロー追記 — 即時起票・握りつぶし禁止ルール (issue_8194)
- config.yaml/CLAUDE.md/ticket_comment_templates.mdにauditorエントリ追加 (issue_8506)
- leader config.yaml session_startupメッセージ圧縮 (issue_8277)

## [0.2.4] - 2026-03-17

### role別ツール権限調整
- tech-leadにEdit/Writeツール付与 — vibes/docs配下ドキュメント編集権限 (issue_8227)
- tech-lead禁止事項を更新 — ソースコード編集禁止、vibes/docs配下のみ編集可 (issue_8227)

## [0.2.3] - 2026-03-15

### バグ暫定対応
ClaudeCodeの既知のバグに暫定対応
https://github.com/anthropics/claude-code/issues/26408 

## [0.2.2] - 2026-03-15

### 各agentのモデルを見直し
opusはトークン量が重いため､試験的にsonnetに変更してみる

## [0.2.1] - 2026-03-09

### SessionStart自動配置の追加
プロジェクトルートに `vibes/docs/rules/vibes_documentation_standards.md` が未配置の場合、tech-leadレビュー時にファイル不在でエラーとなっていた。SessionStartフックで存在チェック・テンプレートからの自動コピーを追加した。
- session_cleanup.pyにensure_vibes_files()追加: 全source（startup/resume/compact）で実行 (issue_7947)
- templates/vibes_documentation_standards.mdバンドル (issue_7947)
- tests/__pycache__/*.pyc除去・.gitignoreに__pycache__/追加 (issue_7947)

## [0.2.0] - 2026-03-07

### セッション安定性の改善
leader起動直後にチーム残骸（前セッションの未クリーンアップTeam）が残存し、subagent起動に失敗するケースがあった。チーム残骸の自動削除とleader除外パターンを追加した。
→ セッション開始時の安定性が向上し、手動クリーンアップが不要になった。
- チーム残骸自動削除・leader除外パターン追加 (issue_7435)

leader/subagent間の責務分離を強化し、常駐レビュー体制・通信制御・トレーサビリティを確立した。

### 常駐レビュー体制の確立
leaderがレビュー・コミット・チケット管理を全て担い、ボトルネックだった。tech-lead常駐agentを新設しpeer-to-peerレビューを導入、PMOにチケットCRUD責務を統合し、leaderの負荷を分散した。
→ coder→tech-lead直接レビューが可能になり、leaderはコンテクスト管理・意思決定に集中できるようになった。
- tech-lead常駐agent新設: 設計整合性・コード品質レビュー、コミット権限保持 (issue_6114)
- PMO拡張: Scribe統合によるチケットCRUD一元化 (issue_6228)
- PMO監査チェックリスト拡充: 規約体系(E)項目追加 (issue_6155, issue_6156)
- peer-to-peerレビューフロー: coder→tech-lead直接レビュー (issue_6228)
- researcher調査専門agent新設: 読み取り専用
- tasuki-delegate skill: 4ロール委譲テンプレート

### agent間通信の制御
全agent間で自由に通信でき、情報フローの統制が取れなかった。P2P通信マトリクスを定義し、許可された経路のみ通信可能にした。
→ pmo・researcherへの直接送信禁止（leader経由）、broadcast禁止等の制約でノイズを低減。
- P2P通信マトリクス: 全agentにSendMessage規約・通信経路テーブル定義 (issue_6219)
- coder: git commit/push禁止 → tech-leadがコミット実行に変更

### トレーサビリティ強化
タスク委譲時のissue_id欠落で追跡困難だった。task_spawn_guardにissue_{id}チェックを追加し、team_name必須化で所属不明agentの発生を防止した。
→ 全タスク委譲がチケットに紐付き、監査可能になった。
- task_spawn_guard: issue_{id}トレーサビリティチェック (issue_6218)
- task_spawn_guard: permissionDecision修正・team_name必須化 (issue_6919)

### 廃止・移管
- Scribe agent廃止 → PMOに統合 (issue_6228)
- Conductor agent廃止 → leader本体に責務復帰 (issue_6228)
- leader規約をCLAUDE.md → config.yaml session_startupに移動 (issue_6159)
- hooks.jsonからleader_constraint_guard/redmine_guard登録削除 — claude-nagger conventions体系に移管

## [0.1.0] - 2026-02-01

初回リリース。ticket-tasukiプラグイン基本構成。

### Added
- leader/coder分離アーキテクチャ
- coder・tester・scribe・conductor agent定義
- task_spawn_guard hook
- leader_constraint_guard hook
- tasuki-setup・tasuki-delegate skill
- claude-nagger統合設定テンプレート
