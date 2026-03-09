#!/bin/bash

# 行政書士過去問分析ツール ローカル起動スクリプト
# このスクリプトは、バックエンド(FastAPI)とフロントエンド(Vite)を同時に起動します。

# スクリプトの場所をベースディレクトリに設定
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 行政書士分析ツールを起動しています..."

# バックエンドの起動 (バックグラウンド)
echo "1/2: バックエンド(FastAPI)を起動中..."
cd "$BASE_DIR/backend"
# 仮想環境があれば使用
if [ -d "venv" ]; then
    source venv/bin/activate
fi
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# フロントエンドの起動
echo "2/2: フロントエンド(Vite)を起動中..."
cd "$BASE_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

# 終了処理 (Ctrl+Cで両方のプロセスを停止)
trap "kill $BACKEND_PID $FRONTEND_PID; echo '👋 終了しました'; exit" SIGINT

echo "------------------------------------------------"
echo "✅ 起動完了！"
echo "🔗 フロントエンド: http://localhost:5173"
echo "🔗 バックエンドAPI: http://localhost:8000"
echo "------------------------------------------------"
echo "※ 終了するにはこのウィンドウで Ctrl + C を押してください。"

# プロセスの生存を確認
wait
