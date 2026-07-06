from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path
from deep_translator import GoogleTranslator
import pandas as pd
import os
import difflib
import re


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
STATIC_DIR = BASE_DIR / "static"

load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = FastAPI()

groq_client = Groq(api_key=GROQ_API_KEY)


class UserInput(BaseModel):
    text: str


def load_food_data():
    files = [
        DATA_DIR / "FOOD-DATA-GROUP1.csv",
        DATA_DIR / "FOOD-DATA-GROUP2.csv",
        DATA_DIR / "FOOD-DATA-GROUP3.csv",
        DATA_DIR / "FOOD-DATA-GROUP4.csv",
        DATA_DIR / "FOOD-DATA-GROUP5.csv",
    ]

    df_list = []

    for file in files:
        if file.exists():
            df_list.append(pd.read_csv(file))

    if not df_list:
        raise Exception("No CSV files found inside data folder")

    df = pd.concat(df_list, ignore_index=True)

    needed_columns = [
        "food",
        "Caloric Value",
        "Protein",
        "Fat",
        "Carbohydrates",
        "Sugars",
        "Dietary Fiber",
    ]

    df = df[needed_columns]
    df = df.dropna(subset=["food"])

    return df


foods_df = load_food_data()


def translate_to_english(text):
    try:
        translated = GoogleTranslator(
            source="auto",
            target="en"
        ).translate(text)

        if translated:
            return translated

        return text

    except:
        return text


def split_foods(text):
    parts = re.split(r",|&|\band\b|و", text)
    return [p.strip() for p in parts if p.strip()]


def calculate_health_score(calories, protein, fat, carbs, sugars, fiber):
    score = 10

    if calories > 250:
        score -= 2
    elif calories > 180:
        score -= 1
    elif calories > 120:
        score -= 0.5

    if sugars > 20:
        score -= 2
    elif sugars > 12:
        score -= 1

    if fat > 10:
        score -= 2
    elif fat > 5:
        score -= 1

    if fiber >= 4:
        score += 1
    elif fiber >= 2:
        score += 0.5

    if protein >= 10:
        score += 0.5

    score = max(1, min(10, score))

    return round(score, 1)


def health_label(score):
    if score >= 8:
        return "Healthy"
    elif score >= 6:
        return "Moderate"
    else:
        return "Needs attention"


def row_to_dict(row):
    calories = float(row["Caloric Value"])
    protein = float(row["Protein"])
    fat = float(row["Fat"])
    carbs = float(row["Carbohydrates"])
    sugars = float(row["Sugars"])
    fiber = float(row["Dietary Fiber"])

    score = calculate_health_score(
        calories,
        protein,
        fat,
        carbs,
        sugars,
        fiber
    )

    return {
        "food": str(row["food"]),
        "calories": calories,
        "protein": protein,
        "fat": fat,
        "carbs": carbs,
        "sugars": sugars,
        "fiber": fiber,
        "health_score": score,
        "health_label": health_label(score)
    }


def find_main_food(query):
    query = query.lower().strip()

    food_lower = foods_df["food"].astype(str).str.lower()

    exact_results = foods_df[food_lower == query]

    if not exact_results.empty:
        return exact_results.head(1)

    pattern = r"\b" + re.escape(query) + r"\b"

    word_results = foods_df[
        food_lower.str.contains(pattern, na=False, regex=True)
    ]

    if not word_results.empty:
        return word_results.head(1)

    food_names = food_lower.tolist()

    close_matches = difflib.get_close_matches(
        query,
        food_names,
        n=1,
        cutoff=0.55
    )

    if close_matches:
        fuzzy_results = foods_df[food_lower == close_matches[0]]
        return fuzzy_results.head(1)

    return pd.DataFrame()


def find_similar_foods(food_name, limit=5):
    food_name = food_name.lower().strip()

    food_lower = foods_df["food"].astype(str).str.lower()

    pattern = r"\b" + re.escape(food_name) + r"\b"

    similar_results = foods_df[
        food_lower.str.contains(pattern, na=False, regex=True)
        & (food_lower != food_name)
    ]

    if len(similar_results) < limit:
        food_names = food_lower.tolist()

        close_matches = difflib.get_close_matches(
            food_name,
            food_names,
            n=limit + 5,
            cutoff=0.45
        )

        fuzzy_results = foods_df[
            food_lower.isin(close_matches)
            & (food_lower != food_name)
        ]

        similar_results = pd.concat(
            [similar_results, fuzzy_results],
            ignore_index=True
        )

    similar_results = similar_results.drop_duplicates(subset=["food"])

    return similar_results.head(limit)


def create_comparison(matches):
    if not matches:
        return {}

    healthiest = max(matches, key=lambda x: x["health_score"])
    highest_calories = max(matches, key=lambda x: x["calories"])
    highest_sugar = max(matches, key=lambda x: x["sugars"])
    highest_fiber = max(matches, key=lambda x: x["fiber"])
    highest_protein = max(matches, key=lambda x: x["protein"])
    lowest_fat = min(matches, key=lambda x: x["fat"])

    return {
        "healthiest": healthiest["food"],
        "healthiest_score": healthiest["health_score"],
        "highest_calories": highest_calories["food"],
        "highest_calories_value": highest_calories["calories"],
        "highest_sugar": highest_sugar["food"],
        "highest_sugar_value": highest_sugar["sugars"],
        "highest_fiber": highest_fiber["food"],
        "highest_fiber_value": highest_fiber["fiber"],
        "highest_protein": highest_protein["food"],
        "highest_protein_value": highest_protein["protein"],
        "lowest_fat": lowest_fat["food"],
        "lowest_fat_value": lowest_fat["fat"]
    }


def create_final_recommendation(matches):
    if not matches:
        return "No recommendation available."

    healthiest = max(matches, key=lambda x: x["health_score"])
    highest_sugar = max(matches, key=lambda x: x["sugars"])
    highest_fat = max(matches, key=lambda x: x["fat"])

    recommendation = f"🎯 أفضل خيار صحي هو: {healthiest['food']} لأنه حصل على Health Score = {healthiest['health_score']}/10."

    if highest_sugar["sugars"] > 15:
        recommendation += f"\n⚠️ انتبه من السكر في {highest_sugar['food']} لأنه يحتوي على {highest_sugar['sugars']}g sugar."

    if highest_fat["fat"] > 5:
        recommendation += f"\n⚠️ انتبه من الدهون في {highest_fat['food']} لأنه يحتوي على {highest_fat['fat']}g fat."

    recommendation += "\n💡 النصيحة العامة: اختر الطعام الأعلى بالألياف والأقل بالدهون والسكريات قدر الإمكان."

    return recommendation


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/analyze")
def analyze_food(data: UserInput):

    user_text = data.text.strip()

    if not user_text:
        return {
            "error": "Please enter food name"
        }

    english_text = translate_to_english(user_text)

    food_queries = split_foods(english_text)

    all_results = []

    for food_query in food_queries:
        result = find_main_food(food_query)

        if not result.empty:
            all_results.append(result)

    if not all_results:
        return {
            "error": "No food found in the dataset"
        }

    results = pd.concat(all_results, ignore_index=True)
    results = results.drop_duplicates(subset=["food"])

    context = ""
    matches = []

    for _, row in results.iterrows():

        item = row_to_dict(row)
        matches.append(item)

        context += f"""
Food: {item["food"]}
Calories: {item["calories"]}
Protein: {item["protein"]}
Fat: {item["fat"]}
Carbs: {item["carbs"]}
Sugars: {item["sugars"]}
Fiber: {item["fiber"]}
Health Score: {item["health_score"]}/10
Health Label: {item["health_label"]}
"""

    comparison = create_comparison(matches)
    final_recommendation = create_final_recommendation(matches)

    prompt = f"""
أنت مساعد تغذية عربي.

مهم جدًا:
- استخدم فقط الأطعمة والأرقام الموجودة في قاعدة البيانات.
- لا تضف أطعمة جديدة.
- لا تبدأ بعبارات مثل حسناً أو بالتأكيد.
- ابدأ مباشرة بالتحليل.

المستخدم كتب:
{user_text}

هذه النتائج الأساسية من قاعدة البيانات:

{context}

المطلوب:
حلل النتائج بشكل بسيط ومنظم.

لكل طعام اكتب:
🍽️ اسم الطعام
🔥 السعرات
🥩 البروتين
🍞 الكربوهيدرات
🧈 الدهون
🍬 السكريات
🌾 الألياف
⭐ Health Score من 10
😂 تعليق مضحك قصير
💡 نصيحة قصيرة

وفي النهاية:
✅ أي خيار أفضل صحيًا
⚠️ ماذا يجب الانتباه له

اكتب بالعربية فقط.
"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7
        )

        analysis = response.choices[0].message.content

    except Exception as e:
        analysis = f"حدث خطأ أثناء الاتصال بـ Groq: {str(e)}"

    return {
        "query": user_text,
        "translated_query": english_text,
        "matches": matches,
        "comparison": comparison,
        "final_recommendation": final_recommendation,
        "analysis": analysis
    }


@app.get("/similar")
def get_similar(food: str):

    results = find_similar_foods(food)

    similar = []

    for _, row in results.iterrows():
        similar.append(row_to_dict(row))

    return {
        "food": food,
        "similar": similar
    }