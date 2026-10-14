FROM python:3.12-slim

LABEL org.opencontainers.image.title="signals-api-mcp" \
      org.opencontainers.image.description="MCP server for AI signals data (daily AI signals, what changed, ranked models/repos)" \
      org.opencontainers.image.source="https://github.com/jiangzhangcc-glitch/signals-api-mcp" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app
COPY mcp_server.py /app/mcp_server.py

# stdio MCP server: it reads JSON-RPC lines on stdin and writes responses on stdout,
# so there is no port to expose. It only needs outbound HTTPS to the data API
# (and it always sends a User-Agent — see the README note about 403s).
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["python3", "/app/mcp_server.py"]
