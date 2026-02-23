import json
import base64
import boto3
import re
from datetime import datetime

s3 = boto3.client("s3")
rekognition = boto3.client("rekognition")

BUCKET_NAME = "recognitionv-v1"
REGION = "us-east-1"

# Patrón placa ecuatoriana: 3 letras - 4 números (ej: ABC-1234)
PATRON_PLACA = re.compile(r'^[A-Z]{3}-?\d{4}$', re.IGNORECASE)


def normalizar_placa(texto):
    """Limpia y normaliza el texto para comparar con el patrón"""
    texto = texto.upper().strip()
    # Si viene sin guion, lo insertamos: ABCD1234 → ABC-1234
    sin_guion = re.sub(r'[-\s]', '', texto)
    if re.match(r'^[A-Z]{3}\d{4}$', sin_guion):
        return f"{sin_guion[:3]}-{sin_guion[3:]}"
    return texto


def lambda_handler(event, context):
    try:
        body = base64.b64decode(event["body"])

        image_id = f"placa-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.jpg"

        # Subir imagen a S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=image_id,
            Body=body,
            ContentType="image/jpeg"
        )

        # Detectar texto con Rekognition
        response = rekognition.detect_text(
            Image={'S3Object': {'Bucket': BUCKET_NAME, 'Name': image_id}}
        )

        detecciones = response.get("TextDetections", [])

        placas_encontradas = []

        for deteccion in detecciones:
            # Solo LINE o WORD con confianza alta
            if deteccion["Confidence"] < 70:
                continue

            texto_raw = deteccion["DetectedText"]
            texto_normalizado = normalizar_placa(texto_raw)

            if PATRON_PLACA.match(texto_normalizado):
                placas_encontradas.append({
                    "placa": texto_normalizado.upper(),
                    "confianza": round(deteccion["Confidence"], 2),
                    "texto_raw": texto_raw
                })

        image_url = f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{image_id}"

        if not placas_encontradas:
            return {
                "statusCode": 400,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({
                    "error": "No se detectó ninguna placa ecuatoriana válida",
                    "image_url": image_url,
                    "textos_detectados": [d["DetectedText"] for d in detecciones]
                })
            }

        # Tomar la placa con mayor confianza
        mejor_placa = max(placas_encontradas, key=lambda x: x["confianza"])

        result = {
            "image_url": image_url,
            "placa": mejor_placa["placa"],
            "confianza": mejor_placa["confianza"],
            "todas_las_placas": placas_encontradas
        }

        return {
            "statusCode": 200,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps(result)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": str(e)})
        }