FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 TZ=Asia/Seoul
WORKDIR /app
COPY src/trading_agent /app/trading_agent
RUN mkdir /state && chown 10001:10001 /state
USER 10001:10001
CMD ["python", "-m", "trading_agent.service"]
