#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Knowledge Hub - Quick Start Script (Windows)
参考 start.bat 重写，保持当前窗口运行，实时显示日志
"""

import os
import sys
import subprocess
import platform
import time
from pathlib import Path

# 确保 UTF-8 输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)


def print_banner():
    """打印启动横幅"""
    print("""
============================================================
         AI Knowledge Hub - Quick Start Script
============================================================
""")


def print_step(msg):
    """打印步骤信息"""
    print(f"[>] {msg}")


def print_ok(msg):
    """打印成功信息"""
    print(f"[OK] {msg}")


def print_error(msg):
    """打印错误信息"""
    print(f"[ERROR] {msg}")


def print_warning(msg):
    """打印警告信息"""
    print(f"[WARN] {msg}")


def run_command(cmd, cwd=None, env=None, shell=False):
    """运行命令并返回是否成功"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            shell=shell,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def check_python():
    """检查 Python 环境"""
    print_step("Checking Python environment...")
    success, stdout, stderr = run_command([sys.executable, "--version"])
    if not success:
        print_error("Python not found. Please install Python 3.10+")
        return False
    version = stdout.strip() or stderr.strip()
    print_ok(f"Python version: {version}")
    return True


def check_nodejs():
    """检查 Node.js 环境"""
    print_step("Checking Node.js environment...")
    success, stdout, stderr = run_command(["node", "--version"])
    if not success:
        print_error("Node.js not found. Please install Node.js 18+")
        return False
    print_ok(f"Node.js version: {stdout.strip()}")
    return True


def create_venv(venv_dir):
    """创建虚拟环境"""
    print_step("Setting up Python virtual environment...")
    if venv_dir.exists():
        print_ok("Virtual environment already exists")
        return True

    success, stdout, stderr = run_command([sys.executable, "-m", "venv", str(venv_dir)])
    if success:
        print_ok("Virtual environment created")
        return True
    else:
        print_error(f"Failed to create virtual environment: {stderr}")
        return False


def install_backend_deps(backend_dir, venv_dir):
    """安装后端依赖"""
    print_step("Installing backend dependencies...")

    pip_path = venv_dir / "Scripts" / "pip.exe"
    env = os.environ.copy()
    env["PIP_CONFIG_FILE"] = str(backend_dir / "pip.ini")

    # 升级 pip
    print("  Upgrading pip (using Tsinghua mirror)...")
    run_command([str(pip_path), "install", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "--upgrade", "pip"])

    # 安装依赖
    print("  Installing requirements (using Tsinghua mirror)...")
    req_file = backend_dir / "requirements.txt"
    success, stdout, stderr = run_command(
        [str(pip_path), "install", "--only-binary", ":all:", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "-r", str(req_file)],
        env=env
    )

    if success:
        print_ok("Backend dependencies installed")
        return True
    else:
        print_error(f"Failed to install backend dependencies: {stderr}")
        return False


def check_env_file(backend_dir):
    """检查环境配置文件"""
    print_step("Checking environment configuration...")
    env_file = backend_dir / ".env"
    if env_file.exists():
        print_ok("Environment configuration file found")
    else:
        print_warning(".env file not found, will use default configuration")
        print("       Please copy backend\\.env.example to backend\\.env for customization")


def install_frontend_deps(frontend_dir):
    """安装前端依赖"""
    print_step("Installing frontend dependencies...")

    if (frontend_dir / "node_modules").exists():
        print_ok("Frontend dependencies already exist")
        return True

    success, stdout, stderr = run_command(["pnpm", "install"], cwd=frontend_dir)
    if success:
        print_ok("Frontend dependencies installed")
        return True
    else:
        print_error(f"Failed to install frontend dependencies: {stderr}")
        return False


def start_services(backend_dir, frontend_dir, venv_dir):
    """启动前后端服务"""
    print()

    # 准备环境变量
    backend_env = os.environ.copy()
    backend_env["PYTHONIOENCODING"] = "utf-8"
    backend_env["PYTHONUNBUFFERED"] = "1"
    backend_env["CHCP"] = "65001"

    activate_script = venv_dir / "Scripts" / "activate.bat"

    # 启动后端
    print_step("Starting backend service...")
    backend_cmd = f'cd /d "{backend_dir}" && call "{activate_script}" && chcp 65001 >nul && python -u -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000'
    backend_proc = subprocess.Popen(
        ["cmd", "/c", backend_cmd],
        env=backend_env,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    print(f"  Backend URL: http://localhost:8000")
    print(f"  API Docs:    http://localhost:8000/docs")
    print()

    # 等待后端启动
    time.sleep(3)

    # 启动前端
    print_step("Starting frontend service...")
    frontend_cmd = f'cd /d "{frontend_dir}" && pnpm run dev'
    frontend_proc = subprocess.Popen(
        ["cmd", "/c", frontend_cmd],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    print(f"  Frontend URL: http://localhost:5173")
    print()

    return backend_proc, frontend_proc


def print_final_info():
    """打印最终信息"""
    print("""
============================================================
[OK] All services started!

Access URLs:
  Frontend:     http://localhost:5173
  Backend API:  http://localhost:8000
  API Docs:     http://localhost:8000/docs

How to stop:
  Simply close the opened command line windows
============================================================
""")


def main():
    print_banner()

    # 检查 Windows 系统
    if platform.system() != "Windows":
        print_error("This script is designed for Windows. Please use start.sh for Linux/Mac.")
        return 1

    # 获取项目路径
    project_dir = Path(__file__).parent.resolve()
    backend_dir = project_dir / "backend"
    frontend_dir = project_dir / "frontend"
    venv_dir = backend_dir / ".venv"

    print(f"Project Directory: {project_dir}")
    print()

    # 检查环境
    if not check_python():
        input("Press any key to exit...")
        return 1
    if not check_nodejs():
        input("Press any key to exit...")
        return 1

    # 创建虚拟环境
    if not create_venv(venv_dir):
        input("Press any key to exit...")
        return 1

    # 安装后端依赖
    if not install_backend_deps(backend_dir, venv_dir):
        input("Press any key to exit...")
        return 1

    # 检查环境配置
    check_env_file(backend_dir)
    print()

    # 安装前端依赖
    if not install_frontend_deps(frontend_dir):
        input("Press any key to exit...")
        return 1

    # 启动服务
    backend_proc, frontend_proc = start_services(backend_dir, frontend_dir, venv_dir)

    print_final_info()

    # 等待用户按键
    input("Press any key to stop all services and exit...")

    # 终止服务
    print("\nStopping services...")
    backend_proc.terminate()
    frontend_proc.terminate()
    print("Services stopped.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
