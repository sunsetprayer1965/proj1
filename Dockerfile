# --- Base image ---
FROM nikolaik/python-nodejs:python3.10-nodejs20-slim

# --- System dependencies for MetaGPT ---
RUN apt update && \
    apt install -y libgomp1 git chromium \
    fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg \
    fonts-kacst-one fonts-freefont-ttf libxss1 --no-install-recommends file && \
    apt clean && rm -rf /var/lib/apt/lists/*

# --- Mermaid CLI ---
ENV CHROME_BIN="/usr/bin/chromium" \
    puppeteer_config="/app/metagpt/config/puppeteer-config.json" \
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD="true"
RUN npm install -g @mermaid-js/mermaid-cli && npm cache clean --force

# --- Copy local project ---
COPY . /app
WORKDIR /app

# --- Install local MetaGPT with compatible CLI versions ---
RUN mkdir -p metagpt/workspace && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e . && \
    pip install --no-cache-dir "typer<0.9" "click<8.1.4" importlib-metadata

# --- Default command ---
CMD ["sh", "-c", "tail -f /dev/null"]
