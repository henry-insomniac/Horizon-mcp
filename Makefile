PYTHON ?= python3

.PHONY: test check-mcp
test:
	$(PYTHON) -m pytest -q

check-mcp:
	$(PYTHON) scripts/check_mcp.py
