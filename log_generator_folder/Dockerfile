# 使用Python 3.11官方镜像作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制requirements.txt（即使是空的也要复制，保持规范）
COPY requirements.txt .

# 安装依赖（如果有的话）
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app.py .

# 设置启动命令
CMD ["python", "app.py"]
