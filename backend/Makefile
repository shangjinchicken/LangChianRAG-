# 这个 Makefile 仅供参考，Windows 上请使用 setup.bat 和 start.bat

setup:
	python -m venv venv
	venv\Scripts\pip install -r requirements.txt
	@echo Setup complete!

run:
	venv\Scripts\python main.py

.PHONY: setup run
