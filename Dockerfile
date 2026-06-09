# Gunakan image resmi Python 3.10 slim
FROM python:3.10-slim

# Tentukan direktori kerja di dalam container
WORKDIR /app

# Instal dependensi sistem yang dibutuhkan untuk kompilasi (misal untuk pylibjpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Salin file requirements.txt dan instal dependensi Python
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# Salin semua kode sumber backend ke dalam container
COPY . .

# Ekspos port 5001 (sesuai port Flask yang diinginkan di VPS)
EXPOSE 5001

# Jalankan server produksi Gunicorn binding ke port 5001
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--threads", "4", "--timeout", "120", "app:create_app()"]
