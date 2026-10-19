#!/bin/bash
cd "$(dirname "$0")"
echo "正在啟動 Claude Desktop 臺灣正體中文語言包解除安裝程式..."
python3 LanguagePack.py --uninstall
echo ""
read -p "請按 Enter 鍵關閉視窗..."
