$ErrorActionPreference = "Stop"

python -m pip install -r requirements.txt
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --name DevConvert --add-data "static;static" launcher.py

Write-Host "Built dist\\DevConvert.exe"
