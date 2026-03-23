FROM python:3.12-slim

WORKDIR /app

COPY . /app

EXPOSE 8877

ENV PORT=8877

CMD ["sh", "-c", "python run_conginurohub.py --host 0.0.0.0 --port ${PORT}"]