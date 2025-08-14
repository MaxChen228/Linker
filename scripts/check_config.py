#!/usr/bin/env python3
"""
配置健康檢查腳本

用於驗證 Linker 應用程式的配置狀態，包括：
- 環境變數設置
- 資料庫連線
- 檔案系統權限
- 依賴套件安裝
"""

import os
import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def check_environment():
    """檢查環境變數配置"""
    print("\n📋 環境變數檢查")
    print("-" * 40)

    env_vars = {
        'GEMINI_API_KEY': {
            'required': True,
            'default': None,
            'sensitive': True
        },
        'USE_DATABASE': {
            'required': False,
            'default': 'false',
            'sensitive': False
        },
        'DATABASE_URL': {
            'required': False,
            'default': 'postgresql://postgres:password@localhost:5432/linker',
            'sensitive': True
        },
        'LOG_LEVEL': {
            'required': False,
            'default': 'INFO',
            'sensitive': False
        },
        'DATA_DIR': {
            'required': False,
            'default': './data',
            'sensitive': False
        }
    }

    has_errors = False

    for var, config in env_vars.items():
        value = os.getenv(var, config['default'])

        if config['required'] and not value:
            print(f"❌ {var}: 未設置（必填）")
            has_errors = True
        elif not value:
            print(f"⚠️  {var}: 未設置（使用預設值: {config['default']}）")
        elif config['sensitive']:
            # 不顯示敏感資訊的完整值
            if value == config['default']:
                print(f"⚠️  {var}: 使用預設值（請修改）")
            else:
                masked = value[:4] + "*" * (min(len(value) - 4, 20))
                print(f"✅ {var}: 已設置 ({masked})")
        else:
            print(f"✅ {var}: {value}")

    return not has_errors


def check_dependencies():
    """檢查必要的 Python 套件"""
    print("\n📦 依賴套件檢查")
    print("-" * 40)

    required_packages = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('pydantic', 'Pydantic'),
        ('jinja2', 'Jinja2'),
        ('google.generativeai', 'Google Generative AI'),
        ('asyncpg', 'AsyncPG (PostgreSQL)'),
        ('dotenv', 'Python-dotenv')
    ]

    has_errors = False

    for package, name in required_packages:
        try:
            if '.' in package:
                # 處理子模組
                parts = package.split('.')
                __import__(parts[0])
                module = sys.modules[parts[0]]
                for part in parts[1:]:
                    module = getattr(module, part)
            else:
                __import__(package)
            print(f"✅ {name}: 已安裝")
        except ImportError:
            print(f"❌ {name}: 未安裝")
            has_errors = True

    return not has_errors


def check_file_system():
    """檢查檔案系統權限和目錄結構"""
    print("\n📁 檔案系統檢查")
    print("-" * 40)

    from core.config import DATA_DIR

    checks = [
        (DATA_DIR, "資料目錄", True),
        (project_root / ".env", ".env 配置檔", False),
        (project_root / ".env.example", ".env.example 範本", False),
        (project_root / "web" / "templates", "模板目錄", True),
        (project_root / "web" / "static", "靜態檔案目錄", True)
    ]

    has_errors = False

    for path, name, is_dir in checks:
        path = Path(path)

        if path.exists():
            if is_dir and not path.is_dir():
                print(f"❌ {name}: 存在但不是目錄 ({path})")
                has_errors = True
            elif not is_dir and not path.is_file():
                print(f"❌ {name}: 存在但不是檔案 ({path})")
                has_errors = True
            else:
                # 檢查權限
                if os.access(path, os.R_OK):
                    if os.access(path, os.W_OK):
                        print(f"✅ {name}: 可讀寫 ({path})")
                    else:
                        print(f"⚠️  {name}: 只讀 ({path})")
                else:
                    print(f"❌ {name}: 無法讀取 ({path})")
                    has_errors = True
        else:
            if name == ".env 配置檔":
                print(f"⚠️  {name}: 不存在（使用 .env.example 或環境變數）")
            else:
                print(f"❌ {name}: 不存在 ({path})")
                if is_dir:
                    has_errors = True

    return not has_errors


def check_configuration():
    """檢查 config.py 配置驗證"""
    print("\n⚙️  配置驗證檢查")
    print("-" * 40)

    try:
        from core.config import get_config_summary, validate_config

        is_valid, errors, warnings = validate_config()

        if errors:
            print("❌ 配置錯誤:")
            for error in errors:
                print(f"   {error}")

        if warnings:
            print("⚠️  配置警告:")
            for warning in warnings:
                print(f"   {warning}")

        if is_valid:
            print("✅ 配置驗證通過")

        # 顯示配置摘要
        summary = get_config_summary()
        print("\n📊 配置摘要:")
        print(f"   儲存模式: {summary['storage_mode']}")
        print(f"   資料目錄: {summary['data_directory']}")
        print(f"   日誌級別: {summary['log_level']}")
        print(f"   開發模式: {'是' if summary['dev_mode'] else '否'}")
        print(f"   API Key: {'已設置' if summary['api_key_set'] else '未設置'}")

        return is_valid

    except Exception as e:
        print(f"❌ 配置驗證失敗: {e}")
        return False


def check_database():
    """檢查資料庫連線（如果啟用）"""
    print("\n🗄️  資料庫檢查")
    print("-" * 40)

    try:
        from core.config import USE_DATABASE, check_database_health

        if not USE_DATABASE:
            print("ℹ️  資料庫模式未啟用（使用 JSON 儲存）")
            return True

        is_healthy, message = check_database_health()

        if is_healthy:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
            print("   建議: 檢查 DATABASE_URL 設置或切換到 JSON 模式")

        return is_healthy

    except Exception as e:
        print(f"❌ 資料庫檢查失敗: {e}")
        return False


def main():
    """主程式"""
    print("=" * 50)
    print("       Linker 配置健康檢查")
    print("=" * 50)

    # 執行所有檢查
    results = {
        '環境變數': check_environment(),
        '依賴套件': check_dependencies(),
        '檔案系統': check_file_system(),
        '配置驗證': check_configuration(),
        '資料庫連線': check_database()
    }

    # 總結
    print("\n" + "=" * 50)
    print("       檢查結果總結")
    print("=" * 50)

    all_passed = True
    for name, passed in results.items():
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 50)

    if all_passed:
        print("✅ 所有檢查通過！應用程式可以正常運行。")
    else:
        print("❌ 部分檢查失敗，請根據上述提示修復問題。")
        print("\n建議步驟:")
        print("1. 複製 .env.example 為 .env")
        print("2. 編輯 .env 設置必要的環境變數")
        print("3. 安裝缺失的依賴: pip install -r requirements.txt")
        print("4. 確保所有必要的目錄存在且有適當權限")
        print("5. 重新運行此腳本驗證修復")

    # 返回狀態碼
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
