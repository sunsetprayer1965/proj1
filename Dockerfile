FROM nikolaik/python-nodejs:python3.10-nodejs20-slim

# dependencies
RUN apt update && apt install -y git chromium \
    fonts-ipafont-gothic fonts-wqy-zenhei fonts-freefont-ttf libxss1 \
    && apt clean && rm -rf /var/lib/apt/lists/*

# mermaid
ENV CHROME_BIN="/usr/bin/chromium" \
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD="true"
RUN npm install -g @mermaid-js/mermaid-cli && npm cache clean --force

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ⚠️ 不安装 pip 版本 MetaGPT！
# 我们要让 Docker 直接使用 /app/metagpt（由用户挂载进容器）

CMD ["bash"]
