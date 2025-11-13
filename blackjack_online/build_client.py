# -*- coding: utf-8 -*-
"""
클라이언트 실행 파일 빌드 스크립트

사용법:
1. PyInstaller 설치: pip install pyinstaller
2. 이 스크립트 실행: python build_client.py
3. dist/blackjack_client 폴더에 실행 파일 생성됨
"""

import os
import subprocess
import sys


def build_client():
    print("="*60)
    print("블랙잭 클라이언트 빌드 시작")
    print("="*60)

    # PyInstaller 설치 확인
    try:
        import PyInstaller
    except ImportError:
        print("\n[오류] PyInstaller가 설치되어 있지 않습니다.")
        install = input("지금 설치하시겠습니까? [Y/N]: ").strip().upper()
        if install == 'Y':
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        else:
            print("빌드를 중단합니다.")
            return

    # PyInstaller 명령어 구성
    cmd = [
        "pyinstaller",
        "--onefile",                    # 단일 실행 파일로 생성
        "--name=blackjack_client",      # 실행 파일 이름
        "--clean",                       # 이전 빌드 정리
        "--noconfirm",                   # 확인 없이 덮어쓰기
        "client.py"
    ]

    print("\n[빌드] PyInstaller 실행 중...")
    print(f"명령어: {' '.join(cmd)}\n")

    try:
        subprocess.check_call(cmd)

        print("\n" + "="*60)
        print("✅ 빌드 완료!")
        print("="*60)
        print("\n실행 파일 위치:")

        if sys.platform == "win32":
            print("  → dist/blackjack_client.exe")
        else:
            print("  → dist/blackjack_client")

        print("\n배포 방법:")
        print("  1. dist 폴더의 실행 파일을 클라이언트 PC에 복사")
        print("  2. 더블클릭 또는 터미널에서 실행:")
        print("     Windows: blackjack_client.exe")
        print("     Mac/Linux: ./blackjack_client")
        print("\n" + "="*60)

    except subprocess.CalledProcessError as e:
        print(f"\n[오류] 빌드 실패: {e}")
        return


if __name__ == "__main__":
    build_client()
