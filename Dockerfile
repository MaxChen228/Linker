FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 創建數據目錄
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "8000"]