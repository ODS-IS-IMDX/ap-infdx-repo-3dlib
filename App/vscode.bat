rem © 2025 NTT DATA Japan Co., Ltd. & NTT InfraNet All Rights Reserved.

@echo off
cd /d %~dp0
call ".\.venv\Scripts\activate.bat"
call code .
exit
