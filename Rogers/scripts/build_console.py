"""构建前端控制台并复制到 Rogers 包目录

用法:
    cd Rogers
    python scripts/build_console.py
"""
import shutil
import subprocess
import sys
from pathlib import Path


def check_npm_installed(console_dir: Path) -> bool:
    """检查 node_modules 是否存在，不存在则自动安装"""
    node_modules = console_dir / "node_modules"
    if node_modules.exists():
        return True
    print("\n[0/3] 安装依赖...")
    try:
        subprocess.run(
            ["npm", "install"],
            cwd=console_dir,
            check=True,
            shell=True
        )
        print("  ✓ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ 依赖安装失败: {e}")
        return False
    except FileNotFoundError:
        print("  ✗ 未找到 npm，请先安装 Node.js")
        return False


def main():
    # 项目根目录 (fit-agent/)
    project_root = Path(__file__).resolve().parent.parent.parent
    console_dir = project_root / "console"
    rogers_console_dir = project_root / "Rogers" / "console"

    print("=" * 50)
    print("  构建前端控制台")
    print("=" * 50)

    # 1. 检查 console 目录是否存在
    if not console_dir.exists():
        print(f"错误: console 目录不存在: {console_dir}")
        sys.exit(1)

    # 2. 检查并安装依赖
    if not check_npm_installed(console_dir):
        sys.exit(1)

    # 3. 构建前端
    print("\n[1/2] 构建前端项目...")
    try:
        subprocess.run(
            ["npm", "run", "build"],
            cwd=console_dir,
            check=True,
            shell=True
        )
        print("  ✓ 构建完成")
    except subprocess.CalledProcessError as e:
        print(f"  ✗ 构建失败: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("  ✗ 未找到 npm，请先安装 Node.js")
        sys.exit(1)

    # 4. 检查 dist 目录
    dist_dir = console_dir / "dist"
    if not dist_dir.exists():
        print(f"错误: dist 目录不存在: {dist_dir}")
        sys.exit(1)

    # 5. 清理旧目录并复制
    print("\n[2/2] 复制构建产物...")
    if rogers_console_dir.exists():
        shutil.rmtree(rogers_console_dir)
        print(f"  - 清理旧目录: {rogers_console_dir.name}")

    shutil.copytree(dist_dir, rogers_console_dir)
    print(f"  ✓ 已复制到: Rogers/console/")

    print("\n" + "=" * 50)
    print("  ✅ 构建完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()