#1.使用官方Python运行时作为基础镜像
FROM python:3.12-slim

#2.设置容器内工作目录
WORKDIR /app

#3.设置非root用户(安全最佳实践)
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app

#4.复制依赖文件并安装(利用Docker缓存优化构建速度)
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#5.复制应用代码
RUN mkdir src
COPY --chown=appuser:appuser src ./src
COPY --chown=appuser:appuser .env ./.env

#6.容器内端口占用
EXPOSE 8000

#7.启动命令(使用Uvicorn运行FastAPI应用) 脚本路径和参数分开写，每个部分一个字符串
CMD ["python","src/main.py", "app"]



