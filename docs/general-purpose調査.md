# general-purpose subagent 調査

## 1. Task toolのsubagent_type一覧

| subagent_type | 用途 | 利用可能ツール | 主な利用場面 |
|---|---|---|---|
| `general-purpose` | 全ツール利用可能な汎用サブエージェント | 全ツール（MCP含む） | 複雑なタスク委譲 |
| `Explore` | コードベース探索専用 | Read, Glob, Grep, Bash(制限付き) | コード調査・影響範囲特定 |
| `Plan` | 計画立案専用 | Read, Glob, Grep | 実装計画・設計検討 |
| `Bash` | シェルコマンド実行専用 | Bash | ビルド・テスト・スクリプト実行 |
| `claude-code-guide` | Claude Code自体の使い方案内 | なし（知識ベース応答） | ヘルプ・ガイダンス |

`general-purpose`は制限なしで全ツールにアクセスできる唯一のsubagent_type。

## 2. subagentの種類と違い

### general-purpose vs カスタムagent（.claude/agents/*.md）

| 観点 | general-purpose | カスタムagent |
|---|---|---|
| MCPツール | 動作する | バグ(#13605)で不可 |
| ツール制限 | 不可（全ツール固定） | `tools`/`disallowedTools`で制限可 |
| システムプロンプト | 内部固定（変更不可） | Markdown本文がプロンプト |
| モデル選択 | 親セッション継承のみ | `sonnet`/`opus`/`haiku`/`inherit`指定可 |
| hookのagent_type | `"general-purpose"` | agentファイルのname値 |
| CLAUDE.md継承 | なし | なし |

### 要点
- general-purposeはブラックボックス的に全機能を委譲する用途
- カスタムagentは役割・権限を明示的に設計できる
- 現時点ではMCPツール利用が必要な場合、general-purpose一択

## 3. 実行モードの違い

| 観点 | フォアグラウンド | バックグラウンド (`run_in_background=true`) |
|---|---|---|
| MCPツール | 使用可 | 使用不可（#13254） |
| 実行方式 | 順次実行（親ブロック） | 並列実行可 |
| 結果取得 | 即時 | TaskOutput toolで後から取得 |
| 適用場面 | MCP依存タスク | 独立した並列処理 |

## 4. セッション構造

| 要素 | 挙動 |
|---|---|
| session_id | 親セッションと共有 |
| agent_id | サブエージェントごとに個別付与 |
| トランスクリプト | `subagents/agent-{agent_id}.jsonl`に分離保存 |
| コンテキストウィンドウ | 独立（親とは別管理） |

**既知バグ**: コンテキスト漏洩（#14118）- サブエージェントのコンテキストが親に混入する場合がある。

## 5. Conductorパターンでの転用

### 本来の用途との乖離点
- general-purposeは「単発タスク委譲」が本来の設計意図
- Conductorパターンでは「役割固定の専門エージェント」として常駐的に使用
- システムプロンプト制御不可のため、役割定義をタスク説明文に埋め込む必要がある
- ツール制限不可のため、意図しないツール使用を防げない

### #13605修正後のカスタムagent移行理由
1. **プロンプト制御**: Markdown本文で役割・制約を明確に定義可能
2. **ツール制限**: `tools`/`disallowedTools`で権限を最小化できる
3. **モデル選択**: タスク難度に応じたモデル使い分けでコスト最適化
4. **hook連携**: agent_typeにname値が入り、フック側で正確に識別可能
5. **保守性**: agent定義がファイルとして管理でき、バージョン管理に適合
