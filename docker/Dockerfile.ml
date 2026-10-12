# Phase 3: Basis auf Intel OpenVINO-Image umstellen und onnxruntime-openvino installieren.
FROM python:3.12-slim
WORKDIR /app
COPY apps/ml/app.py apps/ml/requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt  # ab Phase 3 aktiv
ENV FF_ML_PORT=8081
EXPOSE 8081
CMD ["python", "app.py"]
