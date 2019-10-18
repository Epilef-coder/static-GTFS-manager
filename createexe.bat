conda create -n exe python=3.6 --yes
conda activate exe
pip install pypiwin32 pyinstaller
pip install -r requirements.txt
pyinstaller --hidden-import pandas._libs.tslibs.timedeltas --clean --icon=website/favicon.ico --onefile GTFSManager.py
move "dist\GTFSManager.exe" .\
rmdir /s /q "dist" "build" "__pycache__"
conda deactivate
conda env remove --name exe