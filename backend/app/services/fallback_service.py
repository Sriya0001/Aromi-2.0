"""
Fallback Service — Graceful degradation when external LLM API (Groq) is unavailable.

WHY this exists (Amazon Applied Scientist System Design Principle):
High availability and resilience. External dependencies (Groq LLM API, network connections)
can fail. The system must degrade gracefully to deterministic rule-based plans
rather than throwing 500 Internal Server Errors to the user.
"""
from typing import List, Dict, Any

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

FALLBACK_WORKOUT_PLAN = [
    {
        "day": 1,
        "day_name": "Monday",
        "focus": "Upper Body Push & Core",
        "duration_minutes": 45,
        "warmup": "5 min dynamic arm circles, jumping jacks, and torso twists",
        "exercises": [
            {
                "name": "Push-ups",
                "sets": 3,
                "reps": "10-12",
                "rest_seconds": 60,
                "muscle_group": "Chest & Triceps",
                "instructions": "Keep core engaged, lower chest to floor, push up smoothly.",
                "youtube_query": "push-ups proper form tutorial",
                "reasoning": "Standard compound push exercise for upper body strength."
            },
            {
                "name": "Dumbbell Shoulder Press",
                "sets": 3,
                "reps": "12",
                "rest_seconds": 60,
                "muscle_group": "Shoulders",
                "instructions": "Press weights overhead without arching lower back.",
                "youtube_query": "dumbbell shoulder press tutorial",
                "reasoning": "Overhead pressing strength for shoulder mobility."
            },
            {
                "name": "Plank Hold",
                "sets": 3,
                "reps": "45 sec",
                "rest_seconds": 45,
                "muscle_group": "Core",
                "instructions": "Maintain straight line from head to heels.",
                "youtube_query": "plank hold form tutorial",
                "reasoning": "Isometric core stabilization."
            }
        ],
        "cooldown": "5 min chest stretch, shoulder stretch, and child's pose",
        "tips": "Focus on controlled tempo during lowering phase.",
        "calories_estimate": 240,
        "session_reasoning": "Fallback rule-based plan: Balanced upper body pushing and core stability."
    },
    {
        "day": 2,
        "day_name": "Tuesday",
        "focus": "Lower Body & Glutes",
        "duration_minutes": 45,
        "warmup": "5 min leg swings, high knees, and ankle mobility exercises",
        "exercises": [
            {
                "name": "Bodyweight Squats",
                "sets": 4,
                "reps": "15",
                "rest_seconds": 60,
                "muscle_group": "Quadriceps & Glutes",
                "instructions": "Sit back into hips, knees tracking over toes.",
                "youtube_query": "bodyweight squat form tutorial",
                "reasoning": "Fundamental lower body movement pattern."
            },
            {
                "name": "Walking Lunges",
                "sets": 3,
                "reps": "12 per leg",
                "rest_seconds": 60,
                "muscle_group": "Quadriceps & Hamstrings",
                "instructions": "Step forward, lower rear knee toward floor, push up.",
                "youtube_query": "walking lunges tutorial",
                "reasoning": "Unilateral leg strength and balance."
            },
            {
                "name": "Glute Bridges",
                "sets": 3,
                "reps": "15",
                "rest_seconds": 45,
                "muscle_group": "Glutes & Lower Back",
                "instructions": "Drive through heels, squeeze glutes at the top.",
                "youtube_query": "glute bridge form tutorial",
                "reasoning": "Glute activation and posterior chain strength."
            }
        ],
        "cooldown": "5 min hamstring stretch, quad stretch, and hip opener",
        "tips": "Keep weight balanced across mid-foot and heel.",
        "calories_estimate": 280,
        "session_reasoning": "Fallback rule-based plan: Fundamental lower body resistance."
    },
    {
        "day": 3,
        "day_name": "Wednesday",
        "focus": "Active Recovery & Mobility",
        "duration_minutes": 30,
        "warmup": "3 min gentle joint rotations",
        "exercises": [
            {
                "name": "Dynamic Stretching Flow",
                "sets": 2,
                "reps": "10 min",
                "rest_seconds": 30,
                "muscle_group": "Full Body",
                "instructions": "Move fluidly between cat-cow, downward dog, and cobra.",
                "youtube_query": "full body dynamic stretch flow",
                "reasoning": "Promotes blood flow and joint mobility."
            },
            {
                "name": "Foam Rolling / Self-Massage",
                "sets": 1,
                "reps": "15 min",
                "rest_seconds": 0,
                "muscle_group": "Full Body",
                "instructions": "Roll slowly over quads, IT bands, calves, and upper back.",
                "youtube_query": "foam rolling guide for beginners",
                "reasoning": "Myofascial release for muscle recovery."
            }
        ],
        "cooldown": "5 min deep diaphragmatic breathing",
        "tips": "Keep intensity light and stay hydrated.",
        "calories_estimate": 120,
        "session_reasoning": "Fallback rule-based plan: Mid-week recovery to reduce fatigue."
    },
    {
        "day": 4,
        "day_name": "Thursday",
        "focus": "Upper Body Pull & Back",
        "duration_minutes": 45,
        "warmup": "5 min arm circles, cat-cow, and band pull-aparts",
        "exercises": [
            {
                "name": "Dumbbell Rows",
                "sets": 4,
                "reps": "12",
                "rest_seconds": 60,
                "muscle_group": "Lats & Rhomboids",
                "instructions": "Pull dumbbell to hip, squeezing shoulder blade.",
                "youtube_query": "dumbbell row proper form",
                "reasoning": "Primary pulling exercise for posture and back strength."
            },
            {
                "name": "Band Pull-Aparts",
                "sets": 3,
                "reps": "15",
                "rest_seconds": 45,
                "muscle_group": "Rear Deltoids & Upper Back",
                "instructions": "Pull resistance band across chest, squeezing upper back.",
                "youtube_query": "band pull-apart exercise tutorial",
                "reasoning": "Scapular stability and posture correction."
            },
            {
                "name": "Bicep Curls",
                "sets": 3,
                "reps": "12",
                "rest_seconds": 45,
                "muscle_group": "Biceps",
                "instructions": "Curl weights upward smoothly without swinging elbows.",
                "youtube_query": "bicep curls proper form",
                "reasoning": "Arm isolation strength."
            }
        ],
        "cooldown": "5 min doorframe chest stretch and lat stretch",
        "tips": "Maintain a flat spine during rows.",
        "calories_estimate": 230,
        "session_reasoning": "Fallback rule-based plan: Posterior upper body development."
    },
    {
        "day": 5,
        "day_name": "Friday",
        "focus": "Full Body Conditioning",
        "duration_minutes": 45,
        "warmup": "5 min light jogging in place and dynamic mobility",
        "exercises": [
            {
                "name": "Kettlebell / Dumbbell Swings",
                "sets": 4,
                "reps": "15",
                "rest_seconds": 60,
                "muscle_group": "Posterior Chain & Cardio",
                "instructions": "Hinge at hips, drive hips forward to swing weight to chest height.",
                "youtube_query": "kettlebell swing form tutorial",
                "reasoning": "Explosive hip extension and cardiovascular conditioning."
            },
            {
                "name": "Mountain Climbers",
                "sets": 3,
                "reps": "40 sec",
                "rest_seconds": 45,
                "muscle_group": "Core & Cardio",
                "instructions": "Drive knees rapidly toward chest in plank position.",
                "youtube_query": "mountain climbers exercise form",
                "reasoning": "High-density conditioning and core work."
            },
            {
                "name": "Bodyweight Incline Push-ups",
                "sets": 3,
                "reps": "12",
                "rest_seconds": 45,
                "muscle_group": "Chest & Core",
                "instructions": "Place hands on elevated surface, perform smooth push-ups.",
                "youtube_query": "incline push-ups tutorial",
                "reasoning": "Volume builder for chest and shoulders."
            }
        ],
        "cooldown": "5 min full body stretch",
        "tips": "Pace yourself evenly through all sets.",
        "calories_estimate": 310,
        "session_reasoning": "Fallback rule-based plan: Full body aerobic and anaerobic conditioning."
    },
    {
        "day": 6,
        "day_name": "Saturday",
        "focus": "Core & Lower Body Endurance",
        "duration_minutes": 40,
        "warmup": "5 min walking and leg swings",
        "exercises": [
            {
                "name": "Russian Twists",
                "sets": 3,
                "reps": "20 total",
                "rest_seconds": 45,
                "muscle_group": "Obliques & Abs",
                "instructions": "Sit in v-position, rotate torso gently side to side.",
                "youtube_query": "russian twist exercise tutorial",
                "reasoning": "Rotational core strength."
            },
            {
                "name": "Step-Ups",
                "sets": 3,
                "reps": "12 per leg",
                "rest_seconds": 60,
                "muscle_group": "Quadriceps & Glutes",
                "instructions": "Step onto sturdy box or bench, drive through front foot.",
                "youtube_query": "step-ups exercise tutorial",
                "reasoning": "Single-leg strength and functional endurance."
            }
        ],
        "cooldown": "5 min hip flexor and lower back stretch",
        "tips": "Focus on controlled movement, not speed.",
        "calories_estimate": 210,
        "session_reasoning": "Fallback rule-based plan: Core stability and functional lower body."
    },
    {
        "day": 7,
        "day_name": "Sunday",
        "focus": "Rest & Regeneration",
        "duration_minutes": 20,
        "warmup": "2 min gentle walking",
        "exercises": [
            {
                "name": "Light Outdoor Walk / Relaxation",
                "sets": 1,
                "reps": "20 min",
                "rest_seconds": 0,
                "muscle_group": "Full Body",
                "instructions": "Enjoy a comfortable walk in fresh air.",
                "youtube_query": "walking for recovery benefits",
                "reasoning": "Active recovery to prepare for next week."
            }
        ],
        "cooldown": "3 min deep breathing",
        "tips": "Get plenty of sleep and focus on hydration.",
        "calories_estimate": 80,
        "session_reasoning": "Fallback rule-based plan: Rest and nervous system recovery."
    }
]

FALLBACK_NUTRITION_PLAN = [
    {
        "day": 1,
        "day_name": "Monday",
        "is_workout_day": True,
        "calories": 2000,
        "protein_g": 120,
        "carbs_g": 210,
        "fat_g": 60,
        "meals": {
            "breakfast": {
                "name": "Oatmeal with Almonds & Banana",
                "calories": 420,
                "protein_g": 16,
                "ingredients": ["Oats 70g", "Milk 200ml", "Almonds 10g", "Banana 1 medium"],
                "prep_time": "10 min"
            },
            "lunch": {
                "name": "Roti with Dal Tadka & Paneer Sabzi",
                "calories": 650,
                "protein_g": 38,
                "ingredients": ["Whole Wheat Roti 2", "Yellow Dal 150g", "Paneer 100g", "Mixed Salad"],
                "prep_time": "25 min"
            },
            "pre_workout_snack": {
                "name": "Apple & Handful of Roasted Chana",
                "calories": 180,
                "protein_g": 8,
                "ingredients": ["Apple 1", "Roasted Chana 30g"],
                "prep_time": "2 min"
            },
            "dinner": {
                "name": "Brown Rice & Vegetable Sprouted Moong Khichdi",
                "calories": 550,
                "protein_g": 32,
                "ingredients": ["Brown Rice 80g", "Sprouted Moong 100g", "Curd 100g"],
                "prep_time": "25 min"
            }
        },
        "hydration_ml": 2500,
        "reasoning": "Fallback balanced diet: High protein for muscle recovery, complex carbs for energy.",
        "grocery_list": [
            {"name": "Oats", "quantity": "500g"},
            {"name": "Milk", "quantity": "2L"},
            {"name": "Whole Wheat Atta", "quantity": "2kg"},
            {"name": "Paneer", "quantity": "500g"},
            {"name": "Yellow Moong Dal", "quantity": "1kg"},
            {"name": "Almonds", "quantity": "250g"},
            {"name": "Apples", "quantity": "1kg"},
            {"name": "Bananas", "quantity": "1 dozen"}
        ]
    },
    {
        "day": 2,
        "day_name": "Tuesday",
        "is_workout_day": True,
        "calories": 2050,
        "protein_g": 125,
        "carbs_g": 215,
        "fat_g": 62,
        "meals": {
            "breakfast": {
                "name": "Vegetable Poha with Peanuts & Boiled Eggs / Spouts",
                "calories": 430,
                "protein_g": 18,
                "ingredients": ["Flattened Rice 80g", "Peanuts 15g", "Peas & Carrots 50g", "Boiled Eggs 2"],
                "prep_time": "15 min"
            },
            "lunch": {
                "name": "Multigrain Roti with Rajma Masala & Cucumber Raita",
                "calories": 680,
                "protein_g": 36,
                "ingredients": ["Multigrain Roti 2", "Rajma 180g", "Low-fat Curd 100g", "Cucumber 1"],
                "prep_time": "30 min"
            },
            "pre_workout_snack": {
                "name": "Banana & Almond Butter Toast",
                "calories": 220,
                "protein_g": 7,
                "ingredients": ["Whole Grain Bread 1 slice", "Almond Butter 1 tbsp", "Banana 1/2"],
                "prep_time": "3 min"
            },
            "dinner": {
                "name": "Tofu / Paneer Stir-fry with Quinoa & Steamed Broccoli",
                "calories": 520,
                "protein_g": 34,
                "ingredients": ["Tofu/Paneer 120g", "Quinoa 60g", "Broccoli & Bell Peppers 150g"],
                "prep_time": "20 min"
            }
        },
        "hydration_ml": 2600,
        "reasoning": "High-fiber grains and plant-based protein sources for sustained energy.",
        "grocery_list": [
            {"name": "Poha", "quantity": "500g"},
            {"name": "Rajma", "quantity": "500g"},
            {"name": "Tofu", "quantity": "400g"},
            {"name": "Quinoa", "quantity": "500g"},
            {"name": "Broccoli", "quantity": "500g"}
        ]
    },
    {
        "day": 3,
        "day_name": "Wednesday",
        "is_workout_day": False,
        "calories": 1850,
        "protein_g": 110,
        "carbs_g": 180,
        "fat_g": 55,
        "meals": {
            "breakfast": {
                "name": "Besan Chilla with Green Chutney & Paneer Filling",
                "calories": 390,
                "protein_g": 22,
                "ingredients": ["Gram Flour 60g", "Grated Paneer 50g", "Spinach 30g"],
                "prep_time": "15 min"
            },
            "lunch": {
                "name": "Brown Rice Mixed Vegetable Pulao with Soya Chunks & Curd",
                "calories": 600,
                "protein_g": 35,
                "ingredients": ["Brown Rice 70g", "Soya Chunks 40g", "Mixed Veggies 100g", "Curd 100g"],
                "prep_time": "25 min"
            },
            "evening_snack": {
                "name": "Sprouted Chana & Peanut Chaat",
                "calories": 190,
                "protein_g": 10,
                "ingredients": ["Sprouted Black Chana 80g", "Roasted Peanuts 15g", "Lemon & Spices"],
                "prep_time": "5 min"
            },
            "dinner": {
                "name": "Lauki / Bottle Gourd Sabzi with Roti & Moong Dal Soup",
                "calories": 480,
                "protein_g": 25,
                "ingredients": ["Roti 2", "Bottle Gourd 150g", "Moong Dal Soup 200ml"],
                "prep_time": "20 min"
            }
        },
        "hydration_ml": 2400,
        "reasoning": "Rest day nutrition: Slightly lower carbs, easily digestible Moong dal and hydration.",
        "grocery_list": [
            {"name": "Besan", "quantity": "500g"},
            {"name": "Soya Chunks", "quantity": "200g"},
            {"name": "Sprouted Black Chana", "quantity": "300g"},
            {"name": "Bottle Gourd", "quantity": "1kg"}
        ]
    },
    {
        "day": 4,
        "day_name": "Thursday",
        "is_workout_day": True,
        "calories": 2020,
        "protein_g": 122,
        "carbs_g": 210,
        "fat_g": 60,
        "meals": {
            "breakfast": {
                "name": "Idli with Sambar & Coconut Chutney",
                "calories": 410,
                "protein_g": 14,
                "ingredients": ["Steamed Rice Idli 3", "Vegetable Sambar 150ml", "Coconut Chutney 2 tbsp"],
                "prep_time": "15 min"
            },
            "lunch": {
                "name": "Paneer Bhurji with Whole Wheat Chapati & Salad",
                "calories": 660,
                "protein_g": 38,
                "ingredients": ["Paneer 150g", "Chapati 2", "Tomatoes & Onions 100g", "Salad"],
                "prep_time": "20 min"
            },
            "pre_workout_snack": {
                "name": "Fruit Bowl with Chia Seeds",
                "calories": 180,
                "protein_g": 4,
                "ingredients": ["Papaya & Papaya/Orange 150g", "Chia Seeds 1 tbsp"],
                "prep_time": "5 min"
            },
            "dinner": {
                "name": "Dal Makhani (Light) with Jeera Rice & Grilled Veggies",
                "calories": 560,
                "protein_g": 30,
                "ingredients": ["Black Urad Dal 100g", "Jeera Rice 80g", "Zucchini & Capsicum 100g"],
                "prep_time": "30 min"
            }
        },
        "hydration_ml": 2500,
        "reasoning": "Fermented breakfast foods for gut health + high-protein paneer bhurji for recovery.",
        "grocery_list": [
            {"name": "Idli Batter", "quantity": "1kg"},
            {"name": "Black Urad Dal", "quantity": "500g"},
            {"name": "Chia Seeds", "quantity": "250g"},
            {"name": "Papaya", "quantity": "1 whole"}
        ]
    },
    {
        "day": 5,
        "day_name": "Friday",
        "is_workout_day": True,
        "calories": 2080,
        "protein_g": 128,
        "carbs_g": 220,
        "fat_g": 62,
        "meals": {
            "breakfast": {
                "name": "Moong Dal Chilla with Mint Chutney",
                "calories": 400,
                "protein_g": 20,
                "ingredients": ["Soaked Yellow Moong Dal 80g", "Paneer Stuffing 40g", "Mint Chutney"],
                "prep_time": "15 min"
            },
            "lunch": {
                "name": "Chole (Chickpeas) with Brown Rice & Onion Salad",
                "calories": 670,
                "protein_g": 34,
                "ingredients": ["Kabuli Chana 150g", "Brown Rice 80g", "Salad & Lemon"],
                "prep_time": "30 min"
            },
            "pre_workout_snack": {
                "name": "Handful of Mixed Nuts & Dates",
                "calories": 210,
                "protein_g": 6,
                "ingredients": ["Walnuts 10g", "Almonds 10g", "Dates 2"],
                "prep_time": "1 min"
            },
            "dinner": {
                "name": "Palak Paneer with Roti & Fresh Tomato Cucumber Salad",
                "calories": 540,
                "protein_g": 32,
                "ingredients": ["Spinach 200g", "Paneer 100g", "Whole Wheat Roti 2"],
                "prep_time": "25 min"
            }
        },
        "hydration_ml": 2600,
        "reasoning": "Iron-rich spinach and micronutrient-dense legume combination.",
        "grocery_list": [
            {"name": "Kabuli Chana", "quantity": "500g"},
            {"name": "Fresh Spinach", "quantity": "500g"},
            {"name": "Walnuts & Dates", "quantity": "200g each"}
        ]
    },
    {
        "day": 6,
        "day_name": "Saturday",
        "is_workout_day": True,
        "calories": 2000,
        "protein_g": 120,
        "carbs_g": 210,
        "fat_g": 60,
        "meals": {
            "breakfast": {
                "name": "Vegetable Upma with Roasted Cashews & Buttermilk",
                "calories": 410,
                "protein_g": 14,
                "ingredients": ["Semolina / Rava 70g", "Carrots & Beans 50g", "Buttermilk 200ml"],
                "prep_time": "15 min"
            },
            "lunch": {
                "name": "Masoor Dal with Quinoa, Aloo Gobhi Sabzi & Beetroot Salad",
                "calories": 640,
                "protein_g": 32,
                "ingredients": ["Red Masoor Dal 150g", "Quinoa 70g", "Cauliflower Sabzi 120g"],
                "prep_time": "25 min"
            },
            "snack": {
                "name": "Roasted Makhana (Fox Nuts)",
                "calories": 160,
                "protein_g": 5,
                "ingredients": ["Makhana 30g", "Ghee 1 tsp", "Rock Salt & Pepper"],
                "prep_time": "5 min"
            },
            "dinner": {
                "name": "Stuffed Capsicum with Sprouted Moong & Cottage Cheese",
                "calories": 510,
                "protein_g": 30,
                "ingredients": ["Green Bell Pepper 2", "Sprouted Moong 100g", "Cottage Cheese 80g"],
                "prep_time": "25 min"
            }
        },
        "hydration_ml": 2500,
        "reasoning": "Antioxidant-rich beetroot and low-calorie crunch from roasted makhana.",
        "grocery_list": [
            {"name": "Rava", "quantity": "500g"},
            {"name": "Red Masoor Dal", "quantity": "500g"},
            {"name": "Makhana", "quantity": "200g"},
            {"name": "Cauliflower & Capsicum", "quantity": "1kg"}
        ]
    },
    {
        "day": 7,
        "day_name": "Sunday",
        "is_workout_day": False,
        "calories": 1900,
        "protein_g": 115,
        "carbs_g": 190,
        "fat_g": 58,
        "meals": {
            "breakfast": {
                "name": "Paneer Paratha (Light Ghee) with Curd",
                "calories": 460,
                "protein_g": 22,
                "ingredients": ["Whole Wheat Atta 60g", "Grated Paneer 60g", "Plain Curd 100g"],
                "prep_time": "20 min"
            },
            "lunch": {
                "name": "Kadhi Pakora (Baked/Shallow Fry) with Steamed Brown Rice",
                "calories": 620,
                "protein_g": 24,
                "ingredients": ["Gram Flour Kadhi 200ml", "Brown Rice 80g", "Green Salad"],
                "prep_time": "30 min"
            },
            "evening_snack": {
                "name": "Green Tea with Roasted Chana & Flaxseeds",
                "calories": 150,
                "protein_g": 7,
                "ingredients": ["Green Tea 1 cup", "Roasted Chana 25g", "Flaxseeds 1 tsp"],
                "prep_time": "3 min"
            },
            "dinner": {
                "name": "Light Vegetable Soup with Tofu Salad",
                "calories": 430,
                "protein_g": 28,
                "ingredients": ["Mixed Veg Soup 250ml", "Sauteed Tofu 120g", "Cherry Tomatoes & Lettuce"],
                "prep_time": "20 min"
            }
        },
        "hydration_ml": 2400,
        "reasoning": "Sunday comfort meal with healthy modifications (baked kadhi, light paneer paratha).",
        "grocery_list": [
            {"name": "Curd", "quantity": "1kg"},
            {"name": "Green Tea", "quantity": "1 box"},
            {"name": "Flaxseeds", "quantity": "200g"}
        ]
    }
]


def get_fallback_workout_plan() -> Dict[str, Any]:
    return {"plan": FALLBACK_WORKOUT_PLAN}


def get_fallback_nutrition_plan() -> Dict[str, Any]:
    return {"plan": FALLBACK_NUTRITION_PLAN}
