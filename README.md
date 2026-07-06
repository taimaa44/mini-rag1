# AI Food Nutrition Analyzer

AI Food Nutrition Analyzer is a FastAPI-based web application that analyzes food items using nutrition datasets and AI-generated Arabic recommendations.

The system allows users to enter one or more food names, then returns nutrition information, health scores, comparisons, and personalized advice in Arabic.

## Project Idea

The goal of this project is to help users understand the nutritional value of different foods in a simple and interactive way.

The application searches inside food datasets, extracts nutrition values, calculates a health score, compares foods, and generates an Arabic explanation using Groq AI.

## Features

- Analyze one or multiple food items
- Translate user input automatically to English
- Search food data from multiple CSV datasets
- Calculate a Health Score from 1 to 10
- Show calories, protein, fat, carbs, sugars, and fiber
- Compare foods and identify the healthiest option
- Generate Arabic AI nutrition analysis
- Suggest similar foods
- FastAPI backend
- Simple web interface

## Technologies Used

- Python
- FastAPI
- Pandas
- Groq API
- Deep Translator
- CSV datasets
- HTML / CSS / JavaScript

## Project Structure

```text
mini-rag1/
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env
│   └── static/
│       └── index.html
│
├── data/
│   ├── FOOD-DATA-GROUP1.csv
│   ├── FOOD-DATA-GROUP2.csv
│   ├── FOOD-DATA-GROUP3.csv
│   ├── FOOD-DATA-GROUP4.csv
│   └── FOOD-DATA-GROUP5.csv
│
└── README.md


## Screenshots

| Home Page | Analysis Result |
|----------|----------------|
| <img width="300" alt="Home Page" src="https://github.com/user-attachments/assets/019f1fb6-4bce-4c2e-b011-db2e651d3eba" /> | <img width="300" alt="Analysis Result" src="https://github.com/user-attachments/assets/4ef5e6e7-03be-4a39-83a9-42d5b73d2809" /> |
