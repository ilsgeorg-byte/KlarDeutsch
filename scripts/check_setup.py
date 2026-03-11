#!/usr/bin/env python3
"""
KlarDeutsch - скрипт проверки конфигурации
Проверяет все необходимые компоненты перед запуском
"""

import os
import sys
import subprocess
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{'='*50}{Colors.END}")
    print(f"{Colors.BLUE}{text:^50}{Colors.END}")
    print(f"{Colors.BLUE}{'='*50}{Colors.END}\n")

def check_python():
    """Проверка Python версии"""
    print("🐍 Проверка Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"{Colors.GREEN}✓{Colors.END} Python {version.major}.{version.minor} OK")
        return True
    else:
        print(f"{Colors.RED}✗{Colors.END} Python 3.8+ требуется (найден {version.major}.{version.minor})")
        return False

def check_nodejs():
    """Проверка Node.js"""
    print("📦 Проверка Node.js...")
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        version = result.stdout.strip()
        print(f"{Colors.GREEN}✓{Colors.END} Node.js {version} OK")
        return True
    except FileNotFoundError:
        print(f"{Colors.RED}✗{Colors.END} Node.js не установлен")
        return False

def check_npm():
    """Проверка npm"""
    print("📚 Проверка npm...")
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        version = result.stdout.strip()
        print(f"{Colors.GREEN}✓{Colors.END} npm {version} OK")
        return True
    except FileNotFoundError:
        print(f"{Colors.RED}✗{Colors.END} npm не установлен")
        return False

def check_postgresql():
    """Проверка PostgreSQL"""
    print("🗄️ Проверка PostgreSQL...")
    try:
        subprocess.run(['psql', '--version'], capture_output=True, check=True)
        print(f"{Colors.GREEN}✓{Colors.END} PostgreSQL установлен")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        print(f"{Colors.YELLOW}⚠{Colors.END} PostgreSQL не найден (может работать через remote)")
        return False

def check_env_file():
    """Проверка .env.local"""
    print("🔐 Проверка .env.local...")
    if Path('.env.local').exists():
        with open('.env.local', 'r') as f:
            content = f.read()
            if 'POSTGRES_URL' in content:
                print(f"{Colors.GREEN}✓{Colors.END} .env.local найден с POSTGRES_URL")
                return True
            else:
                print(f"{Colors.RED}✗{Colors.END} POSTGRES_URL не найден в .env.local")
                return False
    else:
        print(f"{Colors.YELLOW}⚠{Colors.END} .env.local не найден")
        print(f"   Создайте из .env.local.example")
        return False

def check_node_modules():
    """Проверка node_modules"""
    print("📦 Проверка node_modules...")
    if Path('node_modules').exists():
        print(f"{Colors.GREEN}✓{Colors.END} node_modules найден")
        return True
    else:
        print(f"{Colors.YELLOW}⚠{Colors.END} node_modules не найден (запустите npm install)")
        return False

def check_venv():
    """Проверка Python venv"""
    print("🐍 Проверка Python venv...")
    venv_paths = [
        Path('api/venv'),
        Path('.venv'),
        Path('venv')
    ]
    
    for venv_path in venv_paths:
        if venv_path.exists():
            print(f"{Colors.GREEN}✓{Colors.END} venv найден: {venv_path}")
            return True
    
    print(f"{Colors.YELLOW}⚠{Colors.END} venv не найден (запустите python -m venv api/venv)")
    return False

def check_flask_routes():
    """Проверка Flask маршрутов"""
    print("🛣️ Проверка Flask маршрутов...")
    routes = [
        'api/routes/words.py',
        'api/routes/audio.py',
        'api/routes/__init__.py'
    ]
    
    all_exist = True
    for route in routes:
        if Path(route).exists():
            print(f"{Colors.GREEN}✓{Colors.END} {route}")
        else:
            print(f"{Colors.RED}✗{Colors.END} {route} не найден")
            all_exist = False
    
    return all_exist

def check_components():
    """Проверка React компонентов"""
    print("⚛️ Проверка React компонентов...")
    components = [
        'app/components/ErrorBoundary.tsx',
        'app/styles/Shared.module.css',
        'app/layout.tsx',
        'app/page.tsx',
        'app/trainer/page.tsx',
        'app/audio/page.tsx'
    ]
    
    all_exist = True
    for component in components:
        if Path(component).exists():
            print(f"{Colors.GREEN}✓{Colors.END} {component}")
        else:
            print(f"{Colors.RED}✗{Colors.END} {component} не найден")
            all_exist = False
    
    return all_exist

def check_database():
    """Проверка подключения к БД"""
    print("🗄️ Проверка подключения к БД...")
    try:
        import psycopg2
        from dotenv import load_dotenv
        
        load_dotenv('.env.local')
        url = os.getenv('POSTGRES_URL')
        
        if not url:
            print(f"{Colors.YELLOW}⚠{Colors.END} POSTGRES_URL не установлен")
            return False
        
        # Попытка подключиться
        conn = psycopg2.connect(url)
        conn.close()
        print(f"{Colors.GREEN}✓{Colors.END} Подключение к БД успешно")
        return True
    except ImportError:
        print(f"{Colors.YELLOW}⚠{Colors.END} psycopg2 не установлен (установите requirements.txt)")
        return False
    except Exception as e:
        print(f"{Colors.RED}✗{Colors.END} Ошибка подключения: {str(e)[:50]}")
        return False

def main():
    print_header("KlarDeutsch - Проверка конфигурации")
    
    results = {
        'Python': check_python(),
        'Node.js': check_nodejs(),
        'npm': check_npm(),
        'PostgreSQL': check_postgresql(),
        '.env.local': check_env_file(),
        'node_modules': check_node_modules(),
        'venv': check_venv(),
        'Flask маршруты': check_flask_routes(),
        'React компоненты': check_components(),
        'БД подключение': check_database(),
    }
    
    print_header("Результаты")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = f"{Colors.GREEN}✓{Colors.END}" if result else f"{Colors.RED}✗{Colors.END}"
        print(f"{status} {name}")
    
    print(f"\n{Colors.BLUE}Пройдено: {passed}/{total}{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{'='*50}{Colors.END}")
        print(f"{Colors.GREEN}✓ Все проверки пройдены!{Colors.END}")
        print(f"{Colors.GREEN}{'='*50}{Colors.END}")
        print("\n🚀 Готово запускать:")
        print("   Терминал 1: cd api && python app.py")
        print("   Терминал 2: npm run dev")
        return 0
    else:
        print(f"\n{Colors.RED}{'='*50}{Colors.END}")
        print(f"{Colors.RED}✗ Есть проблемы! Смотрите выше.{Colors.END}")
        print(f"{Colors.RED}{'='*50}{Colors.END}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
