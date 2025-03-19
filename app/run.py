from flask import Flask, render_template, request, redirect, url_for, flash
import boto3
import json
import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Descargar stopwords si no están disponibles
nltk.download("punkt")
nltk.download("stopwords")

app = Flask(__name__)
app.secret_key = "super_secret_key"

# 📌 Configuración de AWS
AWS_REGION = "us-east-1"
comprehend_medical = boto3.client("comprehendmedical", region_name=AWS_REGION)
translate = boto3.client("translate", region_name=AWS_REGION)
s3 = boto3.client("s3", region_name=AWS_REGION)

# 📌 Configuración de paralelismo
MAX_WORKERS = 5  # Número de hilos para procesamiento paralelo

def translate_text(text, source_lang="auto", target_lang="en"):
    """Traduce el texto al inglés usando Amazon Translate."""
    try:
        response = translate.translate_text(
            Text=text,
            SourceLanguageCode=source_lang,
            TargetLanguageCode=target_lang
        )
        return response["TranslatedText"]
    except Exception:
        return text  # Retorna el texto original si hay un error


def clean_text(text):
    """Elimina palabras irrelevantes (stopwords) del contexto de la lesión."""
    stop_words = set(stopwords.words("english"))
    words = word_tokenize(text.lower())
    filtered_words = [word for word in words if word.isalnum() and word not in stop_words]
    return " ".join(filtered_words)


def parse_s3_url(s3_url):
    match = re.match(r"https://([^.]+).s3.[^.]+.amazonaws.com/(.+)", s3_url)
    if not match:
        raise ValueError("URL de S3 no válida")
    return match.group(1), match.group(2)


def read_excel_from_s3(s3_url):
    bucket_name, key = parse_s3_url(s3_url)
    s3 = boto3.client("s3", region_name=AWS_REGION)
    response = s3.get_object(Bucket=bucket_name, Key=key)
    df = pd.read_excel(response["Body"])
    return df.head(400)  # Limitar a 400 registros para optimización


def get_all_injury_variations(injury_type):
    """Usa AWS Comprehend Medical para obtener variaciones y términos médicos relacionados en batch."""
    injury_variations = set()
    try:
        icd_response = comprehend_medical.infer_icd10_cm(Text=f"The patient has {injury_type}")
        for entity in icd_response["Entities"]:
            if "ICD10CMConcepts" in entity:
                for concept in entity["ICD10CMConcepts"]:
                    injury_variations.add(concept["Description"].lower())

        detect_response = comprehend_medical.detect_entities(Text=injury_type)
        for entity in detect_response["Entities"]:
            if entity["Category"] == "MEDICAL_CONDITION":
                injury_variations.add(entity["Text"].lower())

        print(f"✅ Variaciones detectadas para '{injury_type}': {injury_variations}")

    except Exception:
        pass

    return injury_variations


def batch_detect_injuries(texts, injury_variations):
    """Procesa múltiples textos en batch para detectar condiciones médicas."""
    detected_conditions = {}

    try:
        responses = comprehend_medical.batch_detect_entities(TextList=texts)
        for i, response in enumerate(responses["ResultList"]):
            detected_conditions[texts[i]] = {
                entity["Text"].lower()
                for entity in response["Entities"]
                if entity["Category"] == "MEDICAL_CONDITION"
            }

    except Exception as e:
        print(f"❌ Error en batch detect_entities: {e}")

    # Filtrar por variaciones de la lesión ingresada
    filtered_results = {
        text: conditions
        for text, conditions in detected_conditions.items()
        if any(var in conditions for var in injury_variations)
    }

    return filtered_results


def filter_records(df, injury_type, injury_context, start_date=None, end_date=None,
                   column_name="Event Description English"):
    """Filtra registros por lesión médica detectada y palabras clave en el contexto."""
    if column_name not in df.columns:
        return pd.DataFrame()

    # 📌 Traducir `injury_type` y `injury_context` al inglés
    injury_type_translated = translate_text(injury_type)
    injury_context_translated = translate_text(injury_context)

    print(f"🔹 Injury Type traducido: {injury_type} ➝ {injury_type_translated}")
    print(f"🔹 Injury Context traducido: {injury_context} ➝ {injury_context_translated}")

    injury_variations = get_all_injury_variations(injury_type_translated)
    context_keywords = set(clean_text(injury_context_translated).split())

    # 📌 Convertir fechas a datetime
    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    # 📌 Filtrar registros que cumplan la fecha antes de procesar con AWS
    if "Event Date Time" in df.columns:
        df["Event Date Time"] = pd.to_datetime(df["Event Date Time"], errors="coerce").dt.date
        df = df[(df["Event Date Time"] >= start_date) & (df["Event Date Time"] <= end_date)]

    # 📌 Obtener todos los textos relevantes
    texts = df[column_name].dropna().astype(str).str.lower().tolist()

    # 📌 Analizar en paralelo usando batch detect
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_results = executor.submit(batch_detect_injuries, texts, injury_variations)
        detected_results = future_results.result()

    # 📌 Filtrar registros con palabras del contexto de la lesión
    filtered_records = []
    for _, row in df.iterrows():
        event_text = str(row[column_name]).lower()

        if event_text in detected_results and any(word in event_text for word in context_keywords):
            row_dict = row.to_dict()
            row_dict["Detected Conditions"] = ", ".join(detected_results[event_text])
            filtered_records.append(row_dict)

    return pd.DataFrame(filtered_records)


@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    filtered_records = []
    s3_url = request.form.get("s3_url", "").strip()
    injury_type = request.form.get("injury_type", "").strip()
    injury_context = request.form.get("injury_context", "").strip()
    start_date = request.form.get("start_date", "").strip()
    end_date = request.form.get("end_date", "").strip()

    if request.method == "POST":
        if not s3_url or not injury_type or not injury_context:
            flash("Debe ingresar la URL del archivo, el tipo de lesión y el contexto.", "danger")
            return redirect(url_for("analyze"))

        df = read_excel_from_s3(s3_url)

        filtered_df = filter_records(df, injury_type, injury_context, start_date, end_date)
        filtered_records = filtered_df.to_dict(orient="records")

        if filtered_df.empty:
            flash(f"No se encontraron registros relacionados con '{injury_type}' y contexto '{injury_context}'.",
                  "warning")

    return render_template("analyze.html", s3_url=s3_url, records=filtered_records, injury_type=injury_type)


if __name__ == "__main__":
    app.run(debug=True)