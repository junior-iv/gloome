#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess
import importlib
import os
import time
from tqdm import tqdm

MIN_PYTHON = (3, 8)
if sys.version_info < MIN_PYTHON:
    sys.exit(f'❌ Requires Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or later.')


def load_requirements():
    if not os.path.exists("requirements.txt"):
        print('⚠️  requirements.txt file not found. Skipping package installation.')
        return []

    with open('requirements.txt', 'r', encoding='utf-8') as f:
        packages = [
            line.strip()
            for line in f.readlines()
            if line.strip() and not line.startswith("#")
        ]
    return packages


def install_packages(packages):
    if not packages:
        return

    print('\n🔍 Checking dependencies...\n')

    installed = 0
    with tqdm(total=len(packages), bar_format='{l_bar}{bar} | {n_fmt}/{total_fmt} packages') as progress:
        for pkg in packages:
            start_time = time.time()
            module_name = pkg.split("==")[0].split(">=")[0]

            try:
                importlib.import_module(module_name)
                tqdm.write(f'✅ {pkg} is already installed.')
            except ImportError:
                tqdm.write(f'📦 Installing {pkg}...')
                try:
                    subprocess.check_call(
                        [sys.executable, '-m', 'pip', 'install', pkg],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    elapsed = time.time() - start_time
                    tqdm.write(f'✅ {pkg} was installed in ({elapsed:.1f} seconds)')
                except subprocess.CalledProcessError:
                    tqdm.write(f'❌ Installation error {pkg}')
            installed += 1
            progress.update(1)

    print('\n✅ Усі залежності готові!\n')


def main():
    # print('🚀 Launching the application...\n')

    packages = load_requirements()
    install_packages(packages)

    os.system('script/main.py')

    # import requests

    # 'git clone https://github.com/junior-iv/gloome.git;'
    # mv / lsweb / rodion / gloome / gloome / lsweb / rodion / gloome / to_del;
    # yes | cp / lsweb / rodion / gloome / to_del / * / lsweb / rodion / gloome / -arRv;
    # rm / lsweb / rodion / gloome / to_del - rf;'
    # import pandas as pd
    # import numpy as np
    #
    # print('🧠 The main logic of the application...\n')
    #
    # response = requests.get('https://api.github.com')
    # print(f'🌐 GitHub API status: {response.status_code}')
    #
    # df = pd.DataFrame({
    #     'x': np.arange(5),
    #     'x²': np.arange(5) ** 2
    # })
    # print('\n📊 Data:')
    # print(df)
    #
    # print('\n✅ The program was completed successfully!')


if __name__ == '__main__':
    try:
        try:
            import tqdm
        except ImportError:
            print('📦 Installing tqdm (for progress bars)...')
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'tqdm'])

        main()
    except KeyboardInterrupt:
        print('\n🛑 The program was interrupted by the user.')
