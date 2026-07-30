import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, ChevronLeft, Check, User, Activity, Target, Utensils, HeartPulse, Sparkles } from 'lucide-react';
import { authAPI, addMedicalCondition } from '../services/api';
import toast from 'react-hot-toast';

const SECTIONS = [
    { id: 1, title: 'Biometrics', icon: User },
    { id: 2, title: 'Fitness Context', icon: Activity },
    { id: 3, title: 'Goals', icon: Target },
    { id: 4, title: 'Diet & Lifestyle', icon: Utensils },
    { id: 5, title: 'Medical', icon: HeartPulse },
    { id: 6, title: 'Motivation', icon: Sparkles }
];

export default function Onboarding() {
    const navigate = useNavigate();
    const [currentStep, setCurrentStep] = useState(1);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [formData, setFormData] = useState({
        // 1. Biometrics
        age: 25, gender: 'male', height_cm: 170, weight_kg: 70, body_fat_pct: 15,
        // 2. Fitness Context
        fitness_level: 'beginner', activity_level: 'light', occupation_type: 'desk',
        years_training: 0, available_days_per_week: 3, session_duration_min: 45,
        preferred_workout_time: 'morning', workout_location: 'gym',
        // 3. Goals
        primary_goal: 'muscle_gain', secondary_goal: 'strength', target_weight_kg: 75, goal_deadline_weeks: 12,
        // 4. Diet & Lifestyle
        diet_type: 'omnivore', meal_frequency: 3, food_allergies: [], cuisine_preference: 'any',
        sleep_hours_avg: 7, sleep_quality: 'good', stress_level: 5, water_intake_liters: 2,
        smoking: false, alcohol_units_week: 0,
        // 5. Medical
        medical_conditions: [], is_pregnant: false, pregnancy_trimester: 1,
        // 6. Motivation
        motivation_level: 8, past_program_adherence: 'medium', reason_for_starting: '',
        equipment_available: []
    });

    const updateForm = (key, value) => {
        setFormData(prev => ({ ...prev, [key]: value }));
    };

    const toggleArrayItem = (key, value) => {
        setFormData(prev => {
            const arr = prev[key];
            if (arr.includes(value)) {
                return { ...prev, [key]: arr.filter(item => item !== value) };
            }
            return { ...prev, [key]: [...arr, value] };
        });
    };

    const handleComplete = async () => {
        try {
            setIsSubmitting(true);
            const { medical_conditions, ...profileData } = formData;
            
            // Format profile data correctly if needed
            await authAPI.updateProfile(profileData);
            
            // Add medical conditions
            if (medical_conditions && medical_conditions.length > 0) {
                for (const condition of medical_conditions) {
                    await addMedicalCondition({ condition_name: condition, notes: 'Added during onboarding' });
                }
            }
            
            toast.success("Profile completed successfully!");
            navigate('/dashboard');
        } catch (error) {
            toast.error("Failed to save profile.");
            console.error(error);
        } finally {
            setIsSubmitting(false);
        }
    };

    const nextStep = () => setCurrentStep(prev => Math.min(prev + 1, 6));
    const prevStep = () => setCurrentStep(prev => Math.max(prev - 1, 1));

    const renderStep = () => {
        switch (currentStep) {
            case 1: return (
                <div className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-muted mb-2">Age</label>
                            <input type="number" className="input-dark" value={formData.age} onChange={e => updateForm('age', Number(e.target.value))} />
                        </div>
                        <div>
                            <label className="block text-sm text-muted mb-2">Gender</label>
                            <select className="input-dark" value={formData.gender} onChange={e => updateForm('gender', e.target.value)}>
                                <option value="male">Male</option>
                                <option value="female">Female</option>
                                <option value="other">Other</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm text-muted mb-2">Height (cm)</label>
                            <input type="number" className="input-dark" value={formData.height_cm} onChange={e => updateForm('height_cm', Number(e.target.value))} />
                        </div>
                        <div>
                            <label className="block text-sm text-muted mb-2">Weight (kg)</label>
                            <input type="number" className="input-dark" value={formData.weight_kg} onChange={e => updateForm('weight_kg', Number(e.target.value))} />
                        </div>
                        <div>
                            <label className="block text-sm text-muted mb-2">Body Fat % (Optional)</label>
                            <input type="number" className="input-dark" value={formData.body_fat_pct} onChange={e => updateForm('body_fat_pct', Number(e.target.value))} />
                        </div>
                    </div>
                </div>
            );
            case 2: return (
                <div className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-muted mb-2">Fitness Level</label>
                            <select className="input-dark" value={formData.fitness_level} onChange={e => updateForm('fitness_level', e.target.value)}>
                                <option value="beginner">Beginner</option>
                                <option value="intermediate">Intermediate</option>
                                <option value="advanced">Advanced</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm text-muted mb-2">Activity Level</label>
                            <select className="input-dark" value={formData.activity_level} onChange={e => updateForm('activity_level', e.target.value)}>
                                <option value="sedentary">Sedentary</option>
                                <option value="light">Lightly Active</option>
                                <option value="moderate">Moderately Active</option>
                                <option value="active">Very Active</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm text-muted mb-2">Available Days / Week</label>
                            <input type="number" className="input-dark" value={formData.available_days_per_week} onChange={e => updateForm('available_days_per_week', Number(e.target.value))} />
                        </div>
                        <div>
                            <label className="block text-sm text-muted mb-2">Session Duration (min)</label>
                            <input type="number" className="input-dark" value={formData.session_duration_min} onChange={e => updateForm('session_duration_min', Number(e.target.value))} />
                        </div>
                        <div>
                            <label className="block text-sm text-muted mb-2">Preferred Workout Time</label>
                            <select className="input-dark" value={formData.preferred_workout_time} onChange={e => updateForm('preferred_workout_time', e.target.value)}>
                                <option value="morning">Morning</option>
                                <option value="afternoon">Afternoon</option>
                                <option value="evening">Evening</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm text-muted mb-2">Workout Location</label>
                            <select className="input-dark" value={formData.workout_location} onChange={e => updateForm('workout_location', e.target.value)}>
                                <option value="home">Home</option>
                                <option value="gym">Gym</option>
                                <option value="outdoors">Outdoors</option>
                            </select>
                        </div>
                    </div>
                </div>
            );
            case 3: return (
                <div className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-muted mb-2">Primary Goal</label>
                            <select className="input-dark" value={formData.primary_goal} onChange={e => updateForm('primary_goal', e.target.value)}>
                                <option value="fat_loss">Fat Loss</option>
                                <option value="muscle_gain">Muscle Gain</option>
                                <option value="strength">Strength</option>
                                <option value="endurance">Endurance</option>
                                <option value="maintenance">Maintenance</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm text-muted mb-2">Secondary Goal</label>
                            <select className="input-dark" value={formData.secondary_goal} onChange={e => updateForm('secondary_goal', e.target.value)}>
                                <option value="fat_loss">Fat Loss</option>
                                <option value="muscle_gain">Muscle Gain</option>
                                <option value="strength">Strength</option>
                                <option value="endurance">Endurance</option>
                                <option value="flexibility">Flexibility</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm text-muted mb-2">Target Weight (kg)</label>
                            <input type="number" className="input-dark" value={formData.target_weight_kg} onChange={e => updateForm('target_weight_kg', Number(e.target.value))} />
                        </div>
                        <div>
                            <label className="block text-sm text-muted mb-2">Goal Deadline (weeks)</label>
                            <input type="number" className="input-dark" value={formData.goal_deadline_weeks} onChange={e => updateForm('goal_deadline_weeks', Number(e.target.value))} />
                        </div>
                    </div>
                </div>
            );
            case 4: return (
                <div className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-muted mb-2">Diet Type</label>
                            <select className="input-dark" value={formData.diet_type} onChange={e => updateForm('diet_type', e.target.value)}>
                                <option value="omnivore">Omnivore</option>
                                <option value="vegetarian">Vegetarian</option>
                                <option value="vegan">Vegan</option>
                                <option value="keto">Keto</option>
                                <option value="paleo">Paleo</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm text-muted mb-2">Meal Frequency</label>
                            <input type="number" className="input-dark" value={formData.meal_frequency} onChange={e => updateForm('meal_frequency', Number(e.target.value))} />
                        </div>
                        <div className="col-span-2">
                            <label className="block text-sm text-muted mb-2">Food Allergies</label>
                            <div className="flex flex-wrap gap-2">
                                {['gluten', 'lactose', 'nuts', 'shellfish', 'eggs', 'soy'].map(item => (
                                    <button key={item} onClick={() => toggleArrayItem('food_allergies', item)}
                                        className={`px-4 py-1 rounded-full text-sm font-medium border transition-all ${formData.food_allergies.includes(item) ? 'bg-purple-500/20 border-purple-500 text-purple-400' : 'border-white/10 text-muted hover:border-white/30'}`}>
                                        {item}
                                    </button>
                                ))}
                            </div>
                        </div>
                        <div className="col-span-2">
                            <label className="block text-sm text-muted mb-2">Stress Level (1-10): {formData.stress_level}</label>
                            <input type="range" min="1" max="10" className="w-full accent-purple-500" value={formData.stress_level} onChange={e => updateForm('stress_level', Number(e.target.value))} />
                        </div>
                        <div>
                            <label className="block text-sm text-muted mb-2">Sleep Hours (Avg)</label>
                            <input type="number" className="input-dark" value={formData.sleep_hours_avg} onChange={e => updateForm('sleep_hours_avg', Number(e.target.value))} />
                        </div>
                        <div>
                            <label className="block text-sm text-muted mb-2">Water Intake (Liters)</label>
                            <input type="number" step="0.1" className="input-dark" value={formData.water_intake_liters} onChange={e => updateForm('water_intake_liters', Number(e.target.value))} />
                        </div>
                    </div>
                </div>
            );
            case 5: return (
                <div className="space-y-6">
                    <div className="col-span-2">
                        <label className="block text-sm text-muted mb-2">Medical Conditions</label>
                        <div className="flex flex-wrap gap-2">
                            {['Hypertension', 'Type2Diabetes', 'HeartDisease', 'Arthritis', 'PCOS', 'Asthma', 'KneePain', 'BackPain', 'ShoulderPain'].map(item => (
                                <button key={item} onClick={() => toggleArrayItem('medical_conditions', item)}
                                    className={`px-4 py-2 rounded-xl text-sm font-medium border transition-all ${formData.medical_conditions.includes(item) ? 'bg-pink-500/20 border-pink-500 text-pink-400' : 'border-white/10 text-muted hover:border-white/30'}`}>
                                    {item}
                                </button>
                            ))}
                        </div>
                    </div>
                    {formData.gender === 'female' && (
                        <div className="flex items-center gap-4 mt-6">
                            <label className="flex items-center gap-2 cursor-pointer text-main">
                                <input type="checkbox" checked={formData.is_pregnant} onChange={e => updateForm('is_pregnant', e.target.checked)} className="accent-pink-500 w-4 h-4" />
                                Is Pregnant
                            </label>
                            {formData.is_pregnant && (
                                <select className="input-dark w-48" value={formData.pregnancy_trimester} onChange={e => updateForm('pregnancy_trimester', Number(e.target.value))}>
                                    <option value="1">Trimester 1</option>
                                    <option value="2">Trimester 2</option>
                                    <option value="3">Trimester 3</option>
                                </select>
                            )}
                        </div>
                    )}
                </div>
            );
            case 6: return (
                <div className="space-y-6">
                    <div>
                        <label className="block text-sm text-muted mb-2">Motivation Level (1-10): {formData.motivation_level}</label>
                        <input type="range" min="1" max="10" className="w-full accent-purple-500" value={formData.motivation_level} onChange={e => updateForm('motivation_level', Number(e.target.value))} />
                    </div>
                    <div className="col-span-2 mt-4">
                        <label className="block text-sm text-muted mb-2">Available Equipment</label>
                        <div className="flex flex-wrap gap-2">
                            {['barbell', 'dumbbells', 'resistance_bands', 'pull_up_bar', 'treadmill', 'kettlebells'].map(item => (
                                <button key={item} onClick={() => toggleArrayItem('equipment_available', item)}
                                    className={`px-4 py-2 rounded-xl text-sm font-medium border transition-all ${formData.equipment_available.includes(item) ? 'bg-cyan-500/20 border-cyan-500 text-cyan-400' : 'border-white/10 text-muted hover:border-white/30'}`}>
                                    {item.replace(/_/g, ' ')}
                                </button>
                            ))}
                        </div>
                    </div>
                    <div className="mt-4">
                        <label className="block text-sm text-muted mb-2">Reason for Starting</label>
                        <textarea className="input-dark min-h-[100px]" value={formData.reason_for_starting} onChange={e => updateForm('reason_for_starting', e.target.value)} placeholder="Tell AroMi why you're starting this journey..." />
                    </div>
                </div>
            );
            default: return null;
        }
    };

    return (
        <div className="min-h-screen bg-mesh flex flex-col items-center justify-center p-4">
            <div className="w-full max-w-3xl glass-card overflow-hidden">
                <div className="p-8">
                    {/* Progress Header */}
                    <div className="flex justify-between items-center mb-8">
                        {SECTIONS.map((section, idx) => {
                            const Icon = section.icon;
                            const isActive = currentStep === section.id;
                            const isPast = currentStep > section.id;
                            return (
                                <div key={section.id} className="flex flex-col items-center gap-2 relative z-10 flex-1">
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${isActive ? 'bg-purple-500 text-white shadow-[0_0_15px_rgba(124,58,237,0.5)]' : isPast ? 'bg-purple-500/20 text-purple-400' : 'bg-white/5 text-muted'}`}>
                                        <Icon size={20} />
                                    </div>
                                    <span className={`text-xs font-medium hidden sm:block ${isActive ? 'text-main' : 'text-muted'}`}>{section.title}</span>
                                </div>
                            );
                        })}
                        {/* Connecting Line */}
                        <div className="absolute top-12 left-10 right-10 h-1 bg-white/5 -z-0 hidden sm:block">
                            <div className="h-full bg-purple-500 transition-all duration-500" style={{ width: `${((currentStep - 1) / 5) * 100}%` }} />
                        </div>
                    </div>

                    {/* Content */}
                    <div className="min-h-[400px]">
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={currentStep}
                                initial={{ x: 20, opacity: 0 }}
                                animate={{ x: 0, opacity: 1 }}
                                exit={{ x: -20, opacity: 0 }}
                                transition={{ duration: 0.3 }}
                            >
                                <h2 className="text-2xl font-bold mb-6 gradient-text">{SECTIONS[currentStep - 1].title}</h2>
                                {renderStep()}
                            </motion.div>
                        </AnimatePresence>
                    </div>

                    {/* Footer Buttons */}
                    <div className="flex justify-between mt-10 pt-6 border-t border-white/10">
                        <button
                            onClick={prevStep}
                            disabled={currentStep === 1}
                            className={`btn-secondary flex items-center gap-2 ${currentStep === 1 ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            <ChevronLeft size={18} /> Back
                        </button>
                        {currentStep < 6 ? (
                            <button onClick={nextStep} className="btn-primary flex items-center gap-2">
                                Next <ChevronRight size={18} />
                            </button>
                        ) : (
                            <button onClick={handleComplete} disabled={isSubmitting} className="btn-primary flex items-center gap-2 bg-gradient-to-r from-green-500 to-emerald-500 hover:shadow-[0_0_20px_rgba(16,185,129,0.4)]">
                                {isSubmitting ? 'Saving...' : 'Complete Profile'} <Check size={18} />
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
