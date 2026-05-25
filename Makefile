.PHONY: run dev test install clean

install:
	pip install -r requirements.txt
	playwright install chromium
	playwright install-deps

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

test:
	pytest -v

xhs-login:
	python app/scrapers/xiaohongshu_login.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf data/cache/*