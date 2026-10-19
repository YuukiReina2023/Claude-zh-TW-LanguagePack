#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Desktop 臺灣正體中文語言包 (zh-TW) - 多平台安裝與守護程式
跨平台支援: macOS / Linux / Windows
道地臺灣習慣用語 · 小版本更新自愈維護
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

# ==================== macOS 專用處理 ====================
def find_macos_claude():
    candidates = [
        "/Applications/Claude.app",
        os.path.expanduser("~/Applications/Claude.app")
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def install_macos(silent=False):
    app_path = find_macos_claude()
    if not app_path:
        raise RuntimeError("找不到已安裝的 Claude.app！請確認 Claude Desktop 是否已安裝至 /Applications 目錄。")

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

    # 2. Electron 前端資源目錄
    # macOS 上資源可能位於 Contents/Resources/app/resources 或 Contents/Resources/resources
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
        # 若為標準結構但目錄尚未完全解鎖，預設取 app/resources
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

def uninstall_macos(silent=False):
    app_path = find_macos_claude()
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
    # 優先檢索 shared-*.js（白名單位於 shared-*.js 中），若無則掃描所有 js
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

# ==================== Linux 專用處理 ====================
def find_linux_claude():
    candidates = [
        "/opt/Claude/resources",
        os.path.expanduser("~/.local/share/Claude/resources"),
        "/usr/lib/claude/resources",
        "/usr/share/claude/resources"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def install_linux(silent=False):
    res_path = find_linux_claude()
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

    if SYSTEM == "Windows" and not (is_autoheal or is_install or is_uninstall):
        # 在 Windows 上若直接執行 Python，委託給具備完整管理員提權與自愈註冊的 PS1
        ps1 = os.path.join(CURRENT_DIR, "LanguagePack.ps1")
        subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1])
        return

    if is_uninstall:
        if SYSTEM == "Darwin":
            uninstall_macos(silent=silent)
        elif SYSTEM == "Linux":
            r = find_linux_claude()
            if r:
                clean_locale_files(r)
                unpatch_js_language(r, silent=silent)
        elif SYSTEM == "Windows":
            ps1 = os.path.join(CURRENT_DIR, "LanguagePack.ps1")
            subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1, "-Uninstall"])
        return

    if is_install or is_autoheal:
        if SYSTEM == "Darwin":
            install_macos(silent=silent)
            if not is_autoheal:
                restart_claude()
        elif SYSTEM == "Linux":
            install_linux(silent=silent)
        elif SYSTEM == "Windows":
            ps1 = os.path.join(CURRENT_DIR, "LanguagePack.ps1")
            flag = "-AutoHeal" if is_autoheal else "-Install"
            subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1, flag])
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
            uninstall_macos()
        elif SYSTEM == "Linux":
            r = find_linux_claude()
            if r:
                clean_locale_files(r)
                unpatch_js_language(r)
    elif choice == "0":
        return
    else:
        if SYSTEM == "Darwin":
            install_macos()
            restart_claude()
        elif SYSTEM == "Linux":
            install_linux()

if __name__ == "__main__":
    main()
