# 终端1 启动 FastAPI
uv run uvicorn app.main:app --reload

# 终端2 启动 Worker
uv run arq app.worker.settings.WorkerSettings

# 打开swagger
http://127.0.0.1:8000/docs