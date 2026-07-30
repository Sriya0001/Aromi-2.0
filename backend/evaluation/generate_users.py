"""
Synthetic User Generator — AroMi 2.1 Evaluation Framework.

Generates reproducible population datasets (500–1000 synthetic user profiles)
including 100+ clinical edge cases (elderly + hypertension, pregnancy, anorexia BMI < 16,
diabetic marathon runner, peanut allergy, surgery recovery, etc.).
"""
import random
import json
import csv
from typing import List, Dict, Any


DEMOGRAPHICS_GENDERS = ["male", "female", "other"]
GOALS = ["fat_loss", "muscle_gain", "maintenance", "endurance", "rehabilitation"]
EXPERIENCE_LEVELS = ["beginner", "intermediate", "advanced"]
MEDICAL_CONDITIONS = [
    "Hypertension", "Diabetes_T2", "Asthma", "Knee_Arthritis", 
    "Osteoporosis", "Pregnancy_T3", "Glaucoma", "Cardiac_Disease", "None"
]
INJURIES = ["knee", "shoulder", "lower_back", "neck", "ankle", "wrist", "None"]
EQUIPMENT_TYPES = [
    ["Barbell", "Dumbbells", "Pull-Up Bar"],  # Gym
    ["Dumbbells"],                            # Home Dumbbells
    ["Resistance Bands"],                     # Home Bands
    ["Bodyweight Only"]                       # Calisthenics
]
DIETS = ["vegetarian", "vegan", "omnivore", "high_protein", "low_carb"]
ALLERGENS = ["peanuts", "dairy", "gluten", "soy", "None"]
SCHEDULE_DURATIONS = [20, 30, 45, 60, 90]


class SyntheticUserGenerator:
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)

    def generate_random_user(self, user_id: int) -> Dict[str, Any]:
        """Generate a random realistic user profile."""
        gender = random.choice(DEMOGRAPHICS_GENDERS)
        age = random.randint(18, 62)
        height_cm = random.randint(155, 195)
        
        # Calculate realistic weight
        if gender == "male":
            weight_kg = round(random.uniform(60.0, 105.0), 1)
        else:
            weight_kg = round(random.uniform(48.0, 90.0), 1)

        bmi = round(weight_kg / ((height_cm / 100.0) ** 2), 1)
        
        # Conditions & Injuries
        num_conds = random.choices([0, 1, 2], weights=[0.6, 0.3, 0.1])[0]
        conditions = random.sample([c for c in MEDICAL_CONDITIONS if c != "None"], k=num_conds) if num_conds > 0 else []
        
        num_injuries = random.choices([0, 1], weights=[0.75, 0.25])[0]
        injuries = random.sample([i for i in INJURIES if i != "None"], k=num_injuries) if num_injuries > 0 else []

        # Allergens
        num_allergens = random.choices([0, 1, 2], weights=[0.7, 0.2, 0.1])[0]
        allergies = random.sample([a for a in ALLERGENS if a != "None"], k=num_allergens) if num_allergens > 0 else []

        return {
            "user_id": user_id,
            "profile_type": "standard_synthetic",
            "username": f"synth_user_{user_id}",
            "age": age,
            "gender": gender,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "bmi": bmi,
            "primary_goal": random.choice(GOALS),
            "fitness_level": random.choice(EXPERIENCE_LEVELS),
            "medical_conditions": conditions,
            "injuries": injuries,
            "sleep_hours_avg": round(random.uniform(5.0, 9.0), 1),
            "sleep_quality": random.choice(["poor", "fair", "good", "excellent"]),
            "stress_level": random.randint(1, 10),
            "water_intake_liters": round(random.uniform(1.5, 4.0), 1),
            "equipment_available": random.choice(EQUIPMENT_TYPES),
            "diet_type": random.choice(DIETS),
            "food_allergies": allergies,
            "weekly_food_budget_usd": random.randint(30, 200),
            "session_duration_min": random.choice(SCHEDULE_DURATIONS),
            "is_edge_case": False,
            "edge_case_name": None
        }

    def generate_edge_case_users(self, start_id: int, count: int = 100) -> List[Dict[str, Any]]:
        """Generate hard clinical & logistical edge cases."""
        edge_cases = []
        templates = [
            {"edge_case_name": "Elderly Hypertension", "age": 68, "medical_conditions": ["Hypertension"], "bmi": 27.5, "session_duration_min": 30},
            {"edge_case_name": "Third Trimester Pregnancy", "age": 31, "gender": "female", "medical_conditions": ["Pregnancy_T3"], "bmi": 29.0},
            {"edge_case_name": "Severe Obesity", "age": 42, "weight_kg": 135.0, "height_cm": 172, "bmi": 45.6, "medical_conditions": ["Knee_Arthritis"]},
            {"edge_case_name": "Anorexia Refusal Risk", "age": 22, "gender": "female", "weight_kg": 41.0, "height_cm": 168, "bmi": 14.5, "primary_goal": "fat_loss"},
            {"edge_case_name": "Athlete Shoulder Injury", "age": 26, "fitness_level": "advanced", "injuries": ["shoulder"], "equipment_available": ["Barbell", "Dumbbells"]},
            {"edge_case_name": "Diabetic Marathon Runner", "age": 38, "medical_conditions": ["Diabetes_T2"], "primary_goal": "endurance", "session_duration_min": 90},
            {"edge_case_name": "Vegetarian Peanut Allergy", "age": 29, "diet_type": "vegetarian", "food_allergies": ["peanuts", "dairy"]},
            {"edge_case_name": "Sleep Deprived Executive", "age": 45, "sleep_hours_avg": 4.0, "stress_level": 9, "session_duration_min": 20},
            {"edge_case_name": "Surgery Recovery", "age": 55, "primary_goal": "rehabilitation", "injuries": ["knee", "lower_back"]},
            {"edge_case_name": "Missing Data Profile", "age": None, "height_cm": None, "weight_kg": None, "primary_goal": "fat_loss"}
        ]

        for i in range(count):
            uid = start_id + i
            template = templates[i % len(templates)]
            base_user = self.generate_random_user(uid)
            base_user.update(template)
            base_user["user_id"] = uid
            base_user["username"] = f"edge_user_{uid}"
            base_user["is_edge_case"] = True
            
            # Recalculate BMI if weight/height present
            if base_user.get("weight_kg") and base_user.get("height_cm"):
                base_user["bmi"] = round(base_user["weight_kg"] / ((base_user["height_cm"] / 100.0) ** 2), 1)
                
            edge_cases.append(base_user)

        return edge_cases

    def generate_population(self, total_standard: int = 500, edge_count: int = 100) -> List[Dict[str, Any]]:
        """Generate complete synthetic user population."""
        population = []
        for uid in range(1, total_standard + 1):
            population.append(self.generate_random_user(uid))
            
        edge_users = self.generate_edge_case_users(total_standard + 1, edge_count)
        population.extend(edge_users)
        return population

    def export_to_json(self, population: List[Dict[str, Any]], filepath: str):
        with open(filepath, 'w') as f:
            json.dump(population, f, indent=2)

    def export_to_csv(self, population: List[Dict[str, Any]], filepath: str):
        if not population:
            return
        fieldnames = []
        for u in population:
            for k in u.keys():
                if k not in fieldnames:
                    fieldnames.append(k)

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for user in population:
                row = dict(user)
                for k, v in row.items():
                    if isinstance(v, list):
                        row[k] = ",".join(str(item) for item in v)
                writer.writerow(row)


if __name__ == "__main__":
    generator = SyntheticUserGenerator(seed=42)
    users = generator.generate_population(total_standard=500, edge_count=100)
    print(f"Generated {len(users)} synthetic users ({len([u for u in users if u['is_edge_case']])} edge cases).")
    generator.export_to_json(users, "synthetic_users.json")
    generator.export_to_csv(users, "synthetic_users.csv")

