lint: ## Проверить линтерами код в репозитории
	ruff check ./src

format: ## Запустить автоформатер
	ruff check --fix ./src

list: ## Показать список доступных команд
	@echo Список доступных команд:
	@powershell -NoProfile -Command "Select-String -Path '$(MAKEFILE_LIST)' -Pattern '^[a-zA-Z_-]+:.*?## .*$$'
