#!/bin/bash
# ticket-tasuki リリース自動化スクリプト
# Usage: ./scripts/release.sh <version>
# Example: ./scripts/release.sh 0.4.0
#
# 機能:
#   - plugin.json バージョン更新
#   - コミット・タグ・push
#   - GitHubリリース作成
#
# 注意: ticket-tasukiはclaude-naggarとは独立したプロダクト
#   - 別リポジトリ (hollySizzle/ticket-tasuki)
#   - 別バージョン体系
#   - 別リリースサイクル
set -e

cd "$(dirname "$0")/.."

# .env読み込み（GH_TOKEN等）
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# 引数チェック
if [ -z "$1" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 0.4.0"
    exit 1
fi

VERSION="$1"
TAG="v$VERSION"
PLUGIN_JSON=".claude-plugin/plugin.json"

# gh CLI認証チェック
if ! gh auth status &>/dev/null; then
    echo "Error: GitHub CLI not authenticated"
    echo "Run: gh auth login"
    echo "Or set GH_TOKEN in .env"
    exit 1
fi

# plugin.json存在チェック
if [ ! -f "$PLUGIN_JSON" ]; then
    echo "Error: $PLUGIN_JSON not found"
    echo "Run this script from ticket-tasuki root directory"
    exit 1
fi

# 未コミットの変更チェック
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Error: Uncommitted changes exist"
    echo "Commit or stash changes before release"
    exit 1
fi

echo "=== ticket-tasuki Release $TAG ==="

# 1. plugin.json バージョン更新
echo "Updating plugin.json version to $VERSION..."
# python3でJSON更新（jqが無い環境対応）
python3 -c "
import json, sys
path = '$PLUGIN_JSON'
with open(path) as f:
    data = json.load(f)
data['version'] = '$VERSION'
with open(path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write('\n')
"

# 2. コミット
echo "Committing..."
git add "$PLUGIN_JSON"
git commit -m "Bump version to $VERSION"

# 3. タグ作成
echo "Creating tag $TAG..."
git tag "$TAG"

# 4. Push
echo "Pushing..."
git push origin main
git push origin "$TAG"

# 5. GitHubリリース作成
echo "Creating GitHub release..."
gh release create "$TAG" --title "$TAG" --generate-notes --repo hollySizzle/ticket-tasuki

echo ""
echo "=== ticket-tasuki Release $TAG created ==="
