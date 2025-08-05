#!/usr/bin/env python3
"""
DownList 安装脚本
自动检查环境并安装依赖
"""
import sys
import subprocess
import os

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 7):
        print("❌ Python版本过低，需要Python 3.7或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    print(f"✅ Python版本检查通过: {sys.version}")
    return True

def install_requirements():
    """安装依赖包"""
    print("📦 正在安装依赖包...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 依赖包安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖包安装失败: {e}")
        return False

def main():
    """主函数"""
    print("🎵 DownList 安装程序")
    print("=" * 40)
    
    # 检查Python版本
    if not check_python_version():
        return False
    
    # 检查requirements.txt是否存在
    if not os.path.exists("requirements.txt"):
        print("❌ 找不到requirements.txt文件")
        return False
    
    # 安装依赖
    if not install_requirements():
        return False
    
    print("\n🎉 安装完成！")
    print("现在可以运行: python app.py")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
