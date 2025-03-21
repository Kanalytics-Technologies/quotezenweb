from flask import Flask, render_template, request, redirect, url_for, flash
import boto3
import json
from io import BytesIO
import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

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

# 📌 Número de hilos para procesamiento en paralelo
MAX_WORKERS = 10


def translate_text(text, source_lang="auto", target_lang="en"):
    """Traduce el texto al inglés usando Amazon Translate."""
    try:
        response = translate.translate_text(
            Text=text,
            SourceLanguageCode=source_lang,
            TargetLanguageCode=target_lang
        )
        return response["TranslatedText"]
    except Exception as e:
        print(f"❌ Error en la traducción con Amazon Translate: {e}")
        return text  # Retorna el texto original si hay un error


def clean_injury_context(context):
    """Elimina palabras irrelevantes (stopwords) del contexto de la lesión."""
    stop_words = set(stopwords.words("english"))
    words = word_tokenize(context.lower())
    filtered_words = [word for word in words if word.isalnum() and word not in stop_words]
    return " ".join(filtered_words)


def parse_s3_url(s3_url):
    match = re.match(r"https://([^.]+).s3.[^.]+.amazonaws.com/(.+)", s3_url)
    if not match:
        raise ValueError("URL de S3 no válida")
    return match.group(1), match.group(2)


def read_excel_from_s3(s3_url):
    bucket_name, key = parse_s3_url(s3_url)
    response = s3.get_object(Bucket=bucket_name, Key=key)
    file_stream = BytesIO(response["Body"].read())
    df = pd.read_excel(file_stream)
    return df.head(500)  # 🔹 Se limita a 400 registros para optimización


def get_all_injury_variations(injury_type):
    """Usa AWS Comprehend Medical para obtener variaciones y términos médicos relacionados."""
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

    except Exception as e:
        print(f"❌ Error en Comprehend Medical: {e}")

    return injury_variations


def detect_injury_with_comprehend(text, injury_variations):
    """Busca términos médicos relacionados en un texto."""
    detected_conditions = set()
    try:
        response = comprehend_medical.detect_entities(Text=text)
        for entity in response["Entities"]:
            entity_text = entity["Text"].lower()
            if entity["Category"] == "MEDICAL_CONDITION":
                detected_conditions.add(entity_text)

        related_conditions = {cond for cond in detected_conditions if any(var in cond for var in injury_variations)}
        return related_conditions

    except Exception as e:
        print(f"❌ Error en Comprehend Medical: {e}")
        return set()


def process_record(row, injury_variations, context_keywords):
    """Procesa un registro en paralelo: detecta lesiones y filtra por contexto."""
    event_text = str(row["Event Description English"]).lower()
    detected_conditions = detect_injury_with_comprehend(event_text, injury_variations)

    # 📌 Filtrar solo si se detectó una lesión y contiene palabras clave del contexto
    if detected_conditions and any(word in event_text for word in context_keywords):
        row_dict = row.to_dict()
        row_dict["Detected Conditions"] = ", ".join(detected_conditions)
        return row_dict
    return None


def filter_records(df, injury_type, injury_context, start_date=None, end_date=None):
    """Filtra registros por lesión médica detectada, palabras clave en el contexto y rango de fechas."""
    if "Event Description English" not in df.columns:
        return pd.DataFrame()

    # 📌 Traducir injury_type y injury_context al inglés antes de analizarlos
    injury_type_translated = translate_text(injury_type)
    injury_context_translated = translate_text(injury_context)

    print(f"🔹 Injury Type traducido: {injury_type} ➝ {injury_type_translated}")
    print(f"🔹 Injury Context traducido: {injury_context} ➝ {injury_context_translated}")

    injury_variations = get_all_injury_variations(injury_type_translated)
    injury_context_nltk = clean_injury_context(injury_context_translated)
    context_keywords = set(injury_context_nltk.lower().split())

    filtered_records = []
    detected_terms = set()

    # 📌 Procesamiento en paralelo
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_record, row, injury_variations, context_keywords): row for _, row in
                   df.iterrows()}

        for future in as_completed(futures):
            result = future.result()
            if result:
                filtered_records.append(result)
                detected_terms.update(result["Detected Conditions"].split(", "))

    print(f"\n✅ 🔥 Términos finales detectados relacionados con '{injury_type_translated}': {detected_terms}")
    return pd.DataFrame(filtered_records), detected_terms


@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    filtered_records = []
    s3_url = request.form.get("s3_url", "").strip()
    injury_type = request.form.get("injury_type", "").strip()
    injury_context = request.form.get("injury_context", "").strip()
    start_date = request.form.get("start_date", "").strip()
    end_date = request.form.get("end_date", "").strip()
    detected_terms = set()

    if request.method == "POST":
        if not s3_url or not injury_type or not injury_context:
            flash("Debe ingresar la URL del archivo, el tipo de lesión y el contexto.", "danger")
            return redirect(url_for("analyze"))

        df = read_excel_from_s3(s3_url)

        filtered_df, detected_terms = filter_records(df, injury_type, injury_context, start_date, end_date)
        filtered_records = filtered_df.to_dict(orient="records")

        if filtered_df.empty:
            flash(f"No se encontraron registros relacionados con '{injury_type}' y contexto '{injury_context}'.",
                  "warning")

    return render_template("analyze.html", s3_url=s3_url, records=filtered_records,
                           detected_terms=list(detected_terms), injury_type=injury_type)


if __name__ == "__main__":
    app.run(debug=True)