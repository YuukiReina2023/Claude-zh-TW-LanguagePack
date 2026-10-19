# Claude Desktop 臺灣正體中文在地化語言包 (zh-TW)

> **道地臺灣正體中文習慣用語 · 依據英文原版全新在地化 · 小版本更新自愈不失效 · 跨平台支援 (Windows / macOS)**

---

## 🌟 專案特色

1. **極簡便攜設計**
   - 捨棄繁雜的碎片檔案與轉換腳本，在 Windows 下**僅需一個 BAT 或一個 PS1** 即可一鍵搞定安裝與還原。
   - 所有語系檔案整齊收錄於 `locales/` 目錄中，同時 `LanguagePack.ps1` 內建離線備用資源庫，即使單檔運行也能正常注入。

2. **道地臺灣資訊習慣用語**
   - 100% 依據英文原版（`en-US`）官方字串全新翻譯，全數通過嚴格的臺灣本地化軟體標準檢驗。
   - 絕無中國大陸簡中轉碼詞，確保繁體中文使用者的流暢閱讀體驗：
     - `Project` ➔ **專案**（非項目）
     - `Settings` ➔ **設定**（非設置）
     - `Default` ➔ **預設**（非默認）
     - `Server` ➔ **伺服器**（非服務器）
     - `Save` ➔ **儲存**（非保存）
     - `Undo / Redo` ➔ **復原 / 重做**（非撤銷）
     - `Cut / Copy / Paste` ➔ **剪下 / 複製 / 貼上**（非剪切 / 粘貼）
     - `Refresh` ➔ **重新整理**（非刷新）
     - `Quit` ➔ **結束 / 離開**（非退出）
     - `Account` ➔ **帳號**（非賬戶 / 賬號）
     - `Shortcut` ➔ **快速鍵**（非快捷鍵）
     - `Clipboard` ➔ **剪貼簿**（非剪貼板）
     - `Screenshot` ➔ **螢幕截圖**（非截屏）
     - `Prompt` ➔ **提示詞 / 提示**
     - `Extension / Plugin` ➔ **擴充功能 / 外掛程式**（非插件）
     - `Session` ➔ **對話 / 工作階段**（非會話）

3. **具備小版本更新自愈能力 (Auto-Heal)**
   - Claude Desktop 在自動發布小版本更新後會建立全新版本目錄並重置資源檔案。
   - 本套件在安裝時會自動建立輕量級排程任務 `Claude-zh-TW-AutoHeal`，於使用者登入或啟動時以毫秒級速度檢查。若偵測到 Claude 版本已更新，將於背景**自動重新解鎖目錄權限並無縫補丁**，徹底解決「每次更新都要手動重裝」的痛點。

4. **多端可用 (Windows / macOS / Linux)**
   - **Windows**：原生 PowerShell + BAT，具備自動 UAC 系統管理員權限提升與 MSIX / WindowsApps 安全目錄接管能力。
   - **macOS**：支援 `.command` 雙擊安裝與 Python 3 指令碼，自動處理 macOS 原生授權對話框（`Localizable.strings`）並自動進行 Ad-hoc 代碼重簽名（`codesign`），防止 Gatekeeper 攔截。

---

## 🚀 快速使用指南

### Windows 使用方式

#### 一鍵安裝
- 滑鼠連按兩下執行 **`安裝繁體中文語言包.bat`**。
- 系統若彈出「使用者帳戶控制 (UAC)」提示，請點選**「是」**允許提升管理員身分。
- 程式將自動偵測 Claude 安裝目錄、解鎖系統權限、部署臺灣正體中文資源，並在完成後自動重啟 Claude Desktop。

#### 一鍵解除安裝（還原英文原版）
- 滑鼠連按兩下執行 **`解除安裝繁體中文語言包.bat`** 即可。

---

### macOS 使用方式

#### 一鍵安裝
- 連按兩下執行 **`安裝繁體中文語言包.command`**（或開啟終端機執行 `python3 LanguagePack.py --install`）。
- 程式會自動補丁 `/Applications/Claude.app`，並自動修復代碼簽名。

#### 一鍵解除安裝
- 連按兩下執行 **`解除安裝繁體中文語言包.command`**（或在終端機執行 `python3 LanguagePack.py --uninstall`）。

---

## 📁 檔案結構說明

```text
Claude_zh-TW_LanguagePack/
│
├── 安裝繁體中文語言包.bat        # Windows 一鍵安裝啟動器 (自動提權)
├── 解除安裝繁體中文語言包.bat    # Windows 一鍵解除安裝 (還原英文)
├── LanguagePack.ps1              # Windows 核心處理引擎 (支援 -Install / -Uninstall / -AutoHeal)
│
├── 安裝繁體中文語言包.command    # macOS 一鍵安裝啟動器
├── 解除安裝繁體中文語言包.command# macOS 一鍵解除安裝啟動器
├── LanguagePack.py               # 跨平台 (macOS / Linux / Windows) 安裝與守護腳本
│
├── locales/                      # 臺灣正體中文在地化語系檔案目錄
│   ├── ion-dist.json             # 前端完整介面在地化 (18,363 條詞條)
│   ├── desktop-shell.json        # 視窗外框與系統功能表選單在地化 (837 條詞條)
│   ├── statsig.json              # 模型特徵與功能描述
│   ├── overrides.json            # 預防前端 404 的佔位設定檔
│   └── Localizable.strings       # macOS 系統原生對話框與存取權限提示
│
└── README.md                     # 本說明文件
```

---

## ⚙️ 進階參數 (PowerShell)

您也可以在 PowerShell 管理員主控台直接執行 `LanguagePack.ps1` 並傳入參數：

```powershell
# 完整安裝繁體中文語言包 (預設重啟 Claude)
.\LanguagePack.ps1 -Install

# 僅安裝但不自動重新啟動應用程式
.\LanguagePack.ps1 -Install -NoRestart

# 解除安裝繁體中文語言包並恢復官方設定
.\LanguagePack.ps1 -Uninstall

# 執行靜默自愈檢查 (小版本更新檢查)
.\LanguagePack.ps1 -AutoHeal -Silent
```

---

## 📜 授權與維護說明

- 本在地化語言包僅供學習交流與個人使用。
- Claude Desktop 的相關商標與軟體版權歸 **Anthropic, PBC** 所有。
