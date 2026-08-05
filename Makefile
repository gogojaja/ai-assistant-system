.PHONY: help check diagnose start stop restart test monitor

help:
	@echo "AI Assistant System shortcuts"
	@echo "  make check      -> python3 scripts/check_env.py"
	@echo "  make diagnose   -> python3 scripts/diagnose.py"
	@echo "  make start      -> bash scripts/start_all_services.sh"
	@echo "  make stop       -> bash scripts/stop_all_services.sh"
	@echo "  make restart    -> bash scripts/restart_callback.sh"
	@echo "  make test       -> venv/bin/python3 scripts/regression_test.py"
	@echo "  make monitor    -> bash monitor_services.sh"

check:
	python3 scripts/check_env.py

diagnose:
	python3 scripts/diagnose.py

start:
	bash scripts/start_all_services.sh

stop:
	bash scripts/stop_all_services.sh

restart:
	bash scripts/restart_callback.sh

test:
	venv/bin/python3 scripts/regression_test.py

monitor:
	bash monitor_services.sh
