# AroMi – AI Fitness & Wellness Coach

An AI-powered fitness and wellness platform that generates **personalized workout and nutrition plans** based on user data, goals, and progress.

---

## Features

-  AI-powered adaptive coaching using LLaMA (Groq)
-  Personalized workout plans based on fitness level & goals
-  Smart nutrition planning with Spoonacular API integration
-  Calendar-based scheduling for workouts and meals
-  Progress tracking with dynamic dashboards
-  Secure authentication using JWT
-  YouTube integration for guided exercises

---

## Tech Stack

### Backend
- FastAPI
- SQLite
- JWT Authentication
- LLaMA-3.3-70B (Groq SDK)
- REST APIs

### Frontend
- React.js
- Tailwind CSS
- Zustand
- Vite

---

## Setup Instructions

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
