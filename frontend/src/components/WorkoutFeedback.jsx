import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Star, Clock, CheckCircle2, XCircle, Activity, X } from 'lucide-react';
import { submitWorkoutFeedback } from '../services/api';
import toast from 'react-hot-toast';

export default function WorkoutFeedback({ workoutId, onClose, onSuccess }) {
    const [status, setStatus] = useState('completed'); // completed, skipped, partial
    const [difficulty, setDifficulty] = useState('just_right'); // too_easy, just_right, too_hard
    const [rating, setRating] = useState(0);
    const [hoverRating, setHoverRating] = useState(0);
    const [duration, setDuration] = useState('');
    const [notes, setNotes] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [showSuccess, setShowSuccess] = useState(false);

    const handleSubmit = async () => {
        if (!rating && status !== 'skipped') {
            toast.error('Please provide a rating');
            return;
        }

        setIsSubmitting(true);
        try {
            await submitWorkoutFeedback({
                workout_id: workoutId,
                status,
                difficulty,
                rating,
                duration_minutes: duration ? parseInt(duration) : null,
                notes
            });
            
            setShowSuccess(true);
            setTimeout(() => {
                if (onSuccess) onSuccess();
                if (onClose) onClose();
            }, 2000);
        } catch (error) {
            toast.error('Failed to submit feedback');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <motion.div 
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="w-full max-w-md glass-card overflow-hidden relative"
            >
                <button onClick={onClose} className="absolute top-4 right-4 text-muted hover:text-white transition-colors">
                    <X size={20} />
                </button>

                <AnimatePresence mode="wait">
                    {showSuccess ? (
                        <motion.div 
                            key="success"
                            initial={{ scale: 0.8, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            className="p-10 flex flex-col items-center justify-center text-center space-y-4"
                        >
                            <div className="w-20 h-20 bg-green-500/20 text-green-400 rounded-full flex items-center justify-center pulse-glow">
                                <CheckCircle2 size={40} />
                            </div>
                            <h3 className="text-2xl font-bold gradient-text">Workout Logged!</h3>
                            <p className="text-muted">Great job staying consistent.</p>
                        </motion.div>
                    ) : (
                        <motion.div key="form" className="p-6">
                            <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                                <Activity className="text-purple-500" /> Session Feedback
                            </h2>

                            <div className="space-y-6">
                                {/* Status */}
                                <div>
                                    <label className="block text-sm font-medium text-muted mb-3">How did it go?</label>
                                    <div className="flex gap-2">
                                        {[
                                            { id: 'completed', icon: CheckCircle2, label: 'Completed ✓', color: 'green' },
                                            { id: 'partial', icon: Activity, label: 'Partial ◑', color: 'orange' },
                                            { id: 'skipped', icon: XCircle, label: 'Skipped ✗', color: 'red' }
                                        ].map(s => (
                                            <button
                                                key={s.id}
                                                onClick={() => setStatus(s.id)}
                                                className={`flex-1 flex flex-col items-center gap-2 p-3 rounded-xl border transition-all ${status === s.id ? `bg-${s.color}-500/20 border-${s.color}-500 text-${s.color}-400` : 'border-white/10 text-muted hover:bg-white/5'}`}
                                            >
                                                <span className="text-sm font-medium">{s.label}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {status !== 'skipped' && (
                                    <>
                                        {/* Difficulty */}
                                        <div className="animate-fade-in">
                                            <label className="block text-sm font-medium text-muted mb-3">Difficulty</label>
                                            <div className="flex gap-2">
                                                {[
                                                    { id: 'too_easy', emoji: '😊', label: 'Too Easy' },
                                                    { id: 'just_right', emoji: '💪', label: 'Just Right' },
                                                    { id: 'too_hard', emoji: '😤', label: 'Too Hard' }
                                                ].map(d => (
                                                    <button
                                                        key={d.id}
                                                        onClick={() => setDifficulty(d.id)}
                                                        className={`flex-1 py-3 rounded-xl border transition-all flex flex-col items-center gap-1 ${difficulty === d.id ? 'bg-purple-500/20 border-purple-500 text-purple-300' : 'border-white/10 text-muted hover:bg-white/5'}`}
                                                    >
                                                        <span className="text-2xl">{d.emoji}</span>
                                                        <span className="text-xs font-medium">{d.label}</span>
                                                    </button>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Duration */}
                                        <div className="flex items-center gap-4">
                                            <div className="flex-1">
                                                <label className="block text-sm font-medium text-muted mb-2">Duration (mins)</label>
                                                <div className="relative">
                                                    <Clock className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" size={16} />
                                                    <input 
                                                        type="number" 
                                                        className="input-dark pl-10" 
                                                        placeholder="e.g. 45"
                                                        value={duration}
                                                        onChange={e => setDuration(e.target.value)}
                                                    />
                                                </div>
                                            </div>
                                            
                                            {/* Star Rating */}
                                            <div className="flex-1">
                                                <label className="block text-sm font-medium text-muted mb-2">Rating</label>
                                                <div className="flex gap-1 items-center h-[42px]">
                                                    {[1, 2, 3, 4, 5].map(star => (
                                                        <button
                                                            key={star}
                                                            onMouseEnter={() => setHoverRating(star)}
                                                            onMouseLeave={() => setHoverRating(0)}
                                                            onClick={() => setRating(star)}
                                                            className="focus:outline-none transition-transform hover:scale-110"
                                                        >
                                                            <Star 
                                                                size={24} 
                                                                className={`${(hoverRating || rating) >= star ? 'fill-yellow-400 text-yellow-400' : 'text-gray-600'}`} 
                                                            />
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </>
                                )}

                                {/* Notes */}
                                <div>
                                    <label className="block text-sm font-medium text-muted mb-2">Notes (Optional)</label>
                                    <textarea 
                                        className="input-dark min-h-[80px]" 
                                        placeholder="How did you feel? Any pain or PRs?"
                                        value={notes}
                                        onChange={e => setNotes(e.target.value)}
                                    />
                                </div>

                                {/* Submit */}
                                <button 
                                    onClick={handleSubmit} 
                                    disabled={isSubmitting}
                                    className="btn-primary w-full justify-center"
                                >
                                    {isSubmitting ? 'Saving...' : 'Save Feedback'}
                                </button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>
        </div>
    );
}
