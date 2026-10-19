#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Desktop 臺灣正體中文語言包 (zh-TW) - 多平台安裝與守護程式
跨平台支援: macOS / Linux / Windows
道地臺灣習慣用語 · 全自動動態路徑檢測 · 小版本更新自愈維護
"""

import os
import sys
import re
import json
import shutil
import platform
import subprocess
import glob

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCALES_DIR = os.path.join(CURRENT_DIR, "locales")
SYSTEM = platform.system()

def print_banner():
    print("")
    print("  ========================================================")
    print("        Claude Desktop 臺灣正體中文語言包 (zh-TW)        ")
    print(f"       道地臺灣習慣用語 · 多端支援 ({SYSTEM})            ")
    print("  ========================================================")
    print("")

def read_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json_file(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def write_text_file(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

# ==================== macOS 動態路徑檢測與處理 ====================
def find_macos_claude(manual_path=None, silent=False):
    # 0. 手動指定路徑優先
    if manual_path and os.path.exists(manual_path):
        manual_path = manual_path.rstrip("/\\")
        if manual_path.endswith(".app"):
            return manual_path
        if os.path.exists(os.path.join(manual_path, "Claude.app")):
            return os.path.join(manual_path, "Claude.app")
        return manual_path

    # 1. 執行中行程即時動態偵測 (無論安裝於任何路徑，只要正在執行即可精準定位實體路徑)
    try:
        out = subprocess.check_output(["ps", "-eo", "comm"], text=True, errors="ignore")
        for line in out.splitlines():
            line = line.strip()
            if "Claude.app" in line:
                idx = line.find("Claude.app")
                candidate = line[:idx + len("Claude.app")]
                if os.path.isdir(candidate):
                    return candidate
    except Exception:
        pass

    # 2. macOS 系統 Spotlight 索引動態檢索 (依據 Bundle Identifier)
    try:
        out = subprocess.check_output(["mdfind", 'kMDItemCFBundleIdentifier == "com.anthropic.claude"'], text=True, errors="ignore").strip()
        if out:
            first = out.splitlines()[0].strip()
            if os.path.isdir(first):
                return first
    except Exception:
        pass

    # 3. macOS 系統 Spotlight 索引動態檢索 (依據檔名)
    try:
        out = subprocess.check_output(["mdfind", 'kMDItemFSName == "Claude.app"'], text=True, errors="ignore").strip()
        if out:
            first = out.splitlines()[0].strip()
            if os.path.isdir(first):
                return first
    except Exception:
        pass

    # 4. 常見目錄動態檢索
    candidates = [
        "/Applications/Claude.app",
        os.path.expanduser("~/Applications/Claude.app"),
        "/Applications/Utilities/Claude.app",
        "/System/Applications/Claude.app"
    ]
    for c in candidates:
        if os.path.isdir(c):
            return c

    # 5. 互動式輸入後備提示 (絕不寫死，允許使用者拖曳輸入)
    if not silent and sys.stdin.isatty():
        print("  [提示] 系統多層動態檢索未能自動鎖定 Claude.app。")
        val = input("請輸入或拖曳 Claude.app 路徑 (例如 /Applications/Claude.app): ").strip().strip('\'"')
        if val and os.path.isdir(val):
            return val

    return None

def install_macos(manual_path=None, silent=False):
    app_path = find_macos_claude(manual_path=manual_path, silent=silent)
    if not app_path:
        raise RuntimeError("找不到已安裝的 Claude.app！請確認 Claude Desktop 是否已安裝。")

    if not silent:
        print(f"發現 Claude.app 目錄: {app_path}")

    # 1. 系統原生多語言目錄 (.lproj)
    contents_res = os.path.join(app_path, "Contents", "Resources")
    strings_src = os.path.join(LOCALES_DIR, "Localizable.strings")
    if os.path.exists(strings_src):
        for lproj in ["zh-TW.lproj", "zh-Hant.lproj"]:
            lproj_dir = os.path.join(contents_res, lproj)
            os.makedirs(lproj_dir, exist_ok=True)
            shutil.copy2(strings_src, os.path.join(lproj_dir, "Localizable.strings"))
        if not silent:
            print("  已安裝 macOS 原生對話框本地化 (zh-TW.lproj)")

    # 2. Electron 前端資源目錄動態定位
    res_candidates = [
        os.path.join(contents_res, "app", "resources"),
        os.path.join(contents_res, "resources"),
        contents_res
    ]
    res_path = None
    for r in res_candidates:
        if os.path.exists(os.path.join(r, "ion-dist")):
            res_path = r
            break
    
    if not res_path:
        res_path = os.path.join(contents_res, "app", "resources")
        os.makedirs(res_path, exist_ok=True)

    # 複製語系檔案
    copy_locale_files(res_path, silent=silent)

    # 3. 修補 JS 語言白名單
    patch_js_language(res_path, silent=silent)

    # 4. 更新偏好設定
    update_macos_config("zh-TW", silent=silent)

    # 5. macOS 代碼簽名修復 (防止 AMFI / Gatekeeper 攔截修改過的 Bundle)
    resign_macos_app(app_path, silent=silent)

    if not silent:
        print("\n=========================================")
        print("  恭喜！繁體中文語言包已順利安裝完成！  ")
        print("=========================================")

def uninstall_macos(manual_path=None, silent=False):
    app_path = find_macos_claude(manual_path=manual_path, silent=silent)
    if not app_path:
        raise RuntimeError("找不到已安裝的 Claude.app")

    contents_res = os.path.join(app_path, "Contents", "Resources")
    for lproj in ["zh-TW.lproj", "zh-Hant.lproj"]:
        p = os.path.join(contents_res, lproj)
        if os.path.exists(p):
            shutil.rmtree(p, ignore_errors=True)

    res_candidates = [
        os.path.join(contents_res, "app", "resources"),
        os.path.join(contents_res, "resources"),
        contents_res
    ]
    for r in res_candidates:
        if os.path.exists(r):
            clean_locale_files(r)
            unpatch_js_language(r, silent=silent)

    update_macos_config("en-US", silent=silent)
    resign_macos_app(app_path, silent=silent)

    if not silent:
        print("\n=== 繁體中文語言包解除安裝完成 ===")

def update_macos_config(locale, silent=False):
    cfg_path = os.path.expanduser("~/Library/Application Support/Claude/config.json")
    if not os.path.exists(cfg_path):
        return
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["locale"] = locale
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        if not silent:
            print(f"  偏好設定已更新 (locale: {locale})")
    except Exception as e:
        if not silent:
            print(f"  [警告] 更新設定檔失敗: {e}")

def resign_macos_app(app_path, silent=False):
    if not silent:
        print("  正在修復 macOS 應用程式本機簽名 (Ad-hoc codesign)...")
    try:
        subprocess.run(["codesign", "--force", "--deep", "--sign", "-", app_path],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if not silent:
            print("  應用程式代碼簽名修復完成！")
    except Exception as e:
        if not silent:
            print(f"  [提示] 簽名步驟略過: {e}")

# ==================== 通用檔案複製與補丁 ====================
def copy_locale_files(resources_path, silent=False):
    i18n_dir = os.path.join(resources_path, "ion-dist", "i18n")
    statsig_dir = os.path.join(i18n_dir, "statsig")
    os.makedirs(i18n_dir, exist_ok=True)
    os.makedirs(statsig_dir, exist_ok=True)

    # 1. ion-dist.json
    ion_src = os.path.join(LOCALES_DIR, "ion-dist.json")
    if os.path.exists(ion_src):
        shutil.copy2(ion_src, os.path.join(i18n_dir, "zh-TW.json"))
        shutil.copy2(ion_src, os.path.join(i18n_dir, "zh-Hant.json"))
        if not silent:
            print("  → ion-dist/i18n/zh-TW.json (前端介面在地化)")

    # 2. desktop-shell.json
    shell_src = os.path.join(LOCALES_DIR, "desktop-shell.json")
    if os.path.exists(shell_src):
        shutil.copy2(shell_src, os.path.join(resources_path, "zh-TW.json"))
        shutil.copy2(shell_src, os.path.join(resources_path, "zh-Hant.json"))
        if not silent:
            print("  → zh-TW.json (視窗與系統選單在地化)")

    # 3. statsig.json
    statsig_src = os.path.join(LOCALES_DIR, "statsig.json")
    if os.path.exists(statsig_src):
        shutil.copy2(statsig_src, os.path.join(statsig_dir, "zh-TW.json"))
        shutil.copy2(statsig_src, os.path.join(statsig_dir, "zh-Hant.json"))
        if not silent:
            print("  → ion-dist/i18n/statsig/zh-TW.json (模型與功能提示文案)")

    # 4. overrides.json
    write_text_file(os.path.join(i18n_dir, "zh-TW.overrides.json"), "{}\n")
    write_text_file(os.path.join(i18n_dir, "zh-Hant.overrides.json"), "{}\n")

def clean_locale_files(resources_path):
    targets = [
        os.path.join(resources_path, "ion-dist", "i18n", "zh-TW.json"),
        os.path.join(resources_path, "ion-dist", "i18n", "zh-TW.overrides.json"),
        os.path.join(resources_path, "ion-dist", "i18n", "zh-Hant.json"),
        os.path.join(resources_path, "ion-dist", "i18n", "zh-Hant.overrides.json"),
        os.path.join(resources_path, "zh-TW.json"),
        os.path.join(resources_path, "zh-Hant.json"),
        os.path.join(resources_path, "ion-dist", "i18n", "statsig", "zh-TW.json"),
        os.path.join(resources_path, "ion-dist", "i18n", "statsig", "zh-Hant.json")
    ]
    for t in targets:
        if os.path.exists(t):
            try:
                os.remove(t)
            except Exception:
                pass

def patch_js_language(resources_path, silent=False):
    assets_dir = os.path.join(resources_path, "ion-dist", "assets", "v1")
    if not os.path.exists(assets_dir):
        return False

    pattern = re.compile(r'((?:[\w$]+)=\["en-US"(?:,"[^"]+")+)(\])')
    # 優先檢索 shared-*.js（語言白名單位於 shared-*.js 中），避免遍歷數千無關檔案
    js_files = glob.glob(os.path.join(assets_dir, "shared-*.js"))
    if not js_files:
        js_files = glob.glob(os.path.join(assets_dir, "*.js"))

    patched = False
    for js in js_files:
        try:
            with open(js, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if '["en-US"' not in content:
                continue
            if '"zh-TW"' in content:
                if not silent:
                    print(f"  已註冊語言: {os.path.basename(js)}")
                patched = True
                continue

            new_content = pattern.sub(r'\1,"zh-TW"]', content, count=1)
            if new_content != content:
                with open(js, "w", encoding="utf-8") as f:
                    f.write(new_content)
                if not silent:
                    print(f"  JS 語言白名單已修補: {os.path.basename(js)}")
                patched = True
        except Exception as e:
            if not silent:
                print(f"  修補 {os.path.basename(js)} 失敗: {e}")

    return patched

def unpatch_js_language(resources_path, silent=False):
    assets_dir = os.path.join(resources_path, "ion-dist", "assets", "v1")
    if not os.path.exists(assets_dir):
        return

    pattern = re.compile(r'((?:[\w$]+)=\[(?:"[^"]+",)+)"zh-TW"\]')
    js_files = glob.glob(os.path.join(assets_dir, "shared-*.js"))
    if not js_files:
        js_files = glob.glob(os.path.join(assets_dir, "*.js"))

    for js in js_files:
        try:
            with open(js, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if '"zh-TW"' not in content:
                continue
            new_content = pattern.sub(r'\1]', content, count=1)
            if new_content != content:
                with open(js, "w", encoding="utf-8") as f:
                    f.write(new_content)
                if not silent:
                    print(f"  語言註冊已還原: {os.path.basename(js)}")
        except Exception:
            pass

# ==================== Linux 動態路徑檢測與處理 ====================
def find_linux_claude(manual_path=None, silent=False):
    # 0. 手動指定路徑優先
    if manual_path and os.path.exists(manual_path):
        manual_path = manual_path.rstrip("/\\")
        for res_cand in [
            os.path.join(manual_path, "resources"),
            os.path.join(manual_path, "app", "resources"),
            manual_path
        ]:
            if os.path.exists(os.path.join(res_cand, "ion-dist")):
                return res_cand

    # 1. 執行中行程即時動態偵測
    try:
        out = subprocess.check_output(["pgrep", "-a", "-f", "claude"], text=True, errors="ignore")
        for line in out.splitlines():
            parts = line.split()
            if len(parts) > 1:
                exe = parts[1]
                if os.path.exists(exe):
                    parent = os.path.dirname(exe)
                    for res_cand in [
                        os.path.join(parent, "resources"),
                        os.path.join(parent, "app", "resources")
                    ]:
                        if os.path.exists(res_cand):
                            return res_cand
    except Exception:
        pass

    # 2. Linux .desktop 啟動檔動態解析
    desktop_dirs = [
        os.path.expanduser("~/.local/share/applications"),
        "/usr/share/applications",
        "/usr/local/share/applications"
    ]
    for dd in desktop_dirs:
        if os.path.exists(dd):
            for df in glob.glob(os.path.join(dd, "*claude*.desktop")):
                try:
                    with open(df, "r", encoding="utf-8", errors="ignore") as f:
                        for dline in f:
                            if dline.startswith("Exec="):
                                exec_part = dline.split("=", 1)[1].split()[0].strip().strip('"\'')
                                if os.path.exists(exec_part):
                                    parent = os.path.dirname(exec_part)
                                    for res_cand in [
                                        os.path.join(parent, "resources"),
                                        os.path.join(parent, "app", "resources")
                                    ]:
                                        if os.path.exists(res_cand):
                                            return res_cand
                except Exception:
                    pass

    # 3. 常見 Linux 安裝目錄動態掃描
    candidates = [
        "/opt/Claude/resources",
        "/opt/claude/resources",
        os.path.expanduser("~/.local/share/Claude/resources"),
        os.path.expanduser("~/.local/share/claude/resources"),
        "/usr/lib/claude/resources",
        "/usr/share/claude/resources",
        "/var/lib/flatpak/app/com.anthropic.Claude/current/active/files/resources",
        os.path.expanduser("~/.var/app/com.anthropic.Claude/data/resources")
    ]
    for c in candidates:
        if os.path.exists(c):
            return c

    # 4. 互動式輸入後備提示 (絕不寫死)
    if not silent and sys.stdin.isatty():
        print("  [提示] 系統多層動態檢索未能自動鎖定 Claude resources 目錄。")
        val = input("請輸入或拖曳 Claude resources 目錄路徑: ").strip().strip('\'"')
        if val and os.path.exists(val):
            return val

    return None

def install_linux(manual_path=None, silent=False):
    res_path = find_linux_claude(manual_path=manual_path, silent=silent)
    if not res_path:
        raise RuntimeError("找不到已安裝的 Claude Desktop resources 目錄！")
    copy_locale_files(res_path, silent=silent)
    patch_js_language(res_path, silent=silent)
    cfg = os.path.expanduser("~/.config/Claude/config.json")
    if os.path.exists(cfg):
        try:
            with open(cfg, "r", encoding="utf-8") as f:
                d = json.load(f)
            d["locale"] = "zh-TW"
            with open(cfg, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    if not silent:
        print("\nLinux 繁體中文語言包安裝完成！")

# ==================== 跨平台重啟 ====================
def restart_claude():
    if SYSTEM == "Darwin":
        try:
            subprocess.run(["killall", "Claude"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["open", "-a", "Claude"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("Claude Desktop 已重新啟動！")
        except Exception:
            pass
    elif SYSTEM == "Windows":
        ps1 = os.path.join(CURRENT_DIR, "LanguagePack.ps1")
        if os.path.exists(ps1):
            subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1, "-Install"])

# ==================== 主入口點 ====================
def main():
    args = sys.argv[1:]
    is_install = "--install" in args
    is_uninstall = "--uninstall" in args
    is_autoheal = "--autoheal" in args
    silent = "-s" in args or "--silent" in args or is_autoheal

    # 解析手動指定路徑 (-p / --path)
    custom_path = None
    for i, a in enumerate(args):
        if a in ("--path", "-p") and i + 1 < len(args):
            custom_path = args[i + 1]
        elif a.startswith("--path="):
            custom_path = a.split("=", 1)[1]

    if SYSTEM == "Windows" and not (is_autoheal or is_install or is_uninstall):
        # 在 Windows 上若直接執行 Python，委託給具備完整管理員提權與自愈註冊的 PS1
        ps1 = os.path.join(CURRENT_DIR, "LanguagePack.ps1")
        cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1]
        if custom_path:
            cmd.extend(["-Path", custom_path])
        subprocess.run(cmd)
        return

    if is_uninstall:
        if SYSTEM == "Darwin":
            uninstall_macos(manual_path=custom_path, silent=silent)
        elif SYSTEM == "Linux":
            r = find_linux_claude(manual_path=custom_path, silent=silent)
            if r:
                clean_locale_files(r)
                unpatch_js_language(r, silent=silent)
        elif SYSTEM == "Windows":
            ps1 = os.path.join(CURRENT_DIR, "LanguagePack.ps1")
            cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1, "-Uninstall"]
            if custom_path:
                cmd.extend(["-Path", custom_path])
            subprocess.run(cmd)
        return

    if is_install or is_autoheal:
        if SYSTEM == "Darwin":
            install_macos(manual_path=custom_path, silent=silent)
            if not is_autoheal:
                restart_claude()
        elif SYSTEM == "Linux":
            install_linux(manual_path=custom_path, silent=silent)
        elif SYSTEM == "Windows":
            ps1 = os.path.join(CURRENT_DIR, "LanguagePack.ps1")
            flag = "-AutoHeal" if is_autoheal else "-Install"
            cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1, flag]
            if custom_path:
                cmd.extend(["-Path", custom_path])
            subprocess.run(cmd)
        return

    # 互動式選單 (macOS / Linux)
    print_banner()
    print("請選擇您要執行的操作：")
    print("  [1] 安裝繁體中文語言包 (zh-TW)")
    print("  [2] 解除安裝繁體中文語言包 (還原為英文原版)")
    print("  [0] 離開")
    print("")
    choice = input("請輸入選項編號 [預設: 1]: ").strip()
    if choice == "2":
        if SYSTEM == "Darwin":
            uninstall_macos(manual_path=custom_path)
        elif SYSTEM == "Linux":
            r = find_linux_claude(manual_path=custom_path)
            if r:
                clean_locale_files(r)
                unpatch_js_language(r)
    elif choice == "0":
        return
    else:
        if SYSTEM == "Darwin":
            install_macos(manual_path=custom_path)
            restart_claude()
        elif SYSTEM == "Linux":
            install_linux(manual_path=custom_path)

if __name__ == "__main__":
    main()
