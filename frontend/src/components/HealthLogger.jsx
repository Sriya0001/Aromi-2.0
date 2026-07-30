import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Moon, Droplets, TrendingUp, Check } from 'lucide-react';
import { logSleep, logHydration, logProgress } from '../services/api';
import toast from 'react-hot-toast';

export default function HealthLogger({ isOpen, onClose }) {
    const [activeTab, setActiveTab] = useState('sleep');
    const [isSubmitting, setIsSubmitting] = useState(false);
    
    // States
    const [sleepData, setSleepData] = useState({ date: new Date().toISOString().split('T')[0], hours: '', quality: 5, hrv: '' });
    const [hydrationData, setHydrationData] = useState({ amount_ml: 0 });
    const [progressData, setProgressData] = useState({ weight_kg: '', body_fat_pct: '', notes: '' });

    const handleSubmit = async () => {
        setIsSubmitting(true);
        try {
            if (activeTab === 'sleep') {
                if (!sleepData.hours) throw new Error("Please enter sleep hours");
                await logSleep({
                    date: sleepData.date,
                    hours: parseFloat(sleepData.hours),
                    quality_score: sleepData.quality,
                    hrv_score: sleepData.hrv ? parseInt(sleepData.hrv) : null
                });
            } else if (activeTab === 'hydration') {
                if (hydrationData.amount_ml <= 0) throw new Error("Please add some water");
                await logHydration({
                    date: new Date().toISOString().split('T')[0],
                    amount_ml: hydrationData.amount_ml
                });
                setHydrationData({ amount_ml: 0 }); // reset
            } else if (activeTab === 'progress') {
                if (!progressData.weight_kg) throw new Error("Please enter weight");
                await logProgress({
                    date: new Date().toISOString().split('T')[0],
                    weight_kg: parseFloat(progressData.weight_kg),
                    body_fat_pct: progressData.body_fat_pct ? parseFloat(progressData.body_fat_pct) : null,
                    notes: progressData.notes
                });
            }
            toast.success(`${activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} logged successfully!`);
            if (activeTab !== 'hydration') onClose();
        } catch (error) {
            toast.error(error.message || 'Failed to log data');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div 
                        initial={{ opacity: 0 }} 
                        animate={{ opacity: 1 }} 
                        exit={{ opacity: 0 }} 
                        onClick={onClose}
                        className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
                    />
                    
                    {/* Panel */}
                    <motion.div
                        initial={{ x: '100%' }}
                        animate={{ x: 0 }}
                        exit={{ x: '100%' }}
                        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                        className="fixed top-0 right-0 h-full w-full max-w-md z-50 glass border-l border-white/10 shadow-2xl flex flex-col"
                    >
                        <div className="flex items-center justify-between p-6 border-b border-white/10">
                            <h2 className="text-xl font-bold gradient-text">Health Logger</h2>
                            <button onClick={onClose} className="p-2 bg-white/5 rounded-full text-muted hover:text-white transition-colors">
                                <X size={20} />
                            </button>
                        </div>

                        {/* Tabs */}
                        <div className="flex p-4 gap-2 border-b border-white/10">
                            {[
                                { id: 'sleep', icon: Moon, label: 'Sleep' },
                                { id: 'hydration', icon: Droplets, label: 'Water' },
                                { id: 'progress', icon: TrendingUp, label: 'Progress' }
                            ].map(tab => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-medium transition-all ${activeTab === tab.id ? 'bg-purple-500 text-white shadow-lg shadow-purple-500/20' : 'text-muted hover:bg-white/5'}`}
                                >
                                    <tab.icon size={16} /> {tab.label}
                                </button>
                            ))}
                        </div>

                        {/* Content */}
                        <div className="flex-1 overflow-y-auto p-6">
                            {activeTab === 'sleep' && (
                                <div className="space-y-6 animate-fade-in">
                                    <div>
                                        <label className="block text-sm text-muted mb-2">Date</label>
                                        <input type="date" className="input-dark" value={sleepData.date} onChange={e => setSleepData({...sleepData, date: e.target.value})} />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-muted mb-2">Hours Slept</label>
                                        <input type="number" step="0.5" className="input-dark" value={sleepData.hours} onChange={e => setSleepData({...sleepData, hours: e.target.value})} placeholder="e.g. 7.5" />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-muted mb-2 flex justify-between">
                                            <span>Sleep Quality</span>
                                            <span className="text-purple-400">{sleepData.quality}/10</span>
                                        </label>
                                        <input type="range" min="1" max="10" className="w-full accent-purple-500" value={sleepData.quality} onChange={e => setSleepData({...sleepData, quality: parseInt(e.target.value)})} />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-muted mb-2">HRV (Optional, ms)</label>
                                        <input type="number" className="input-dark" value={sleepData.hrv} onChange={e => setSleepData({...sleepData, hrv: e.target.value})} placeholder="e.g. 45" />
                                    </div>
                                </div>
                            )}

                            {activeTab === 'hydration' && (
                                <div className="space-y-8 animate-fade-in text-center">
                                    <div className="pt-8">
                                        <div className="w-32 h-32 mx-auto rounded-full border-4 border-cyan-500/30 flex items-center justify-center relative overflow-hidden mb-4">
                                            <div className="absolute bottom-0 w-full bg-cyan-500/20 transition-all duration-500" style={{ height: `${Math.min((hydrationData.amount_ml / 3000) * 100, 100)}%` }} />
                                            <span className="text-3xl font-bold text-cyan-400 z-10">{hydrationData.amount_ml} <span className="text-sm text-cyan-600">ml</span></span>
                                        </div>
                                        <p className="text-muted text-sm">Target: 3000 ml</p>
                                    </div>
                                    
                                    <div className="grid grid-cols-3 gap-3">
                                        {[250, 500, 750].map(amount => (
                                            <button 
                                                key={amount}
                                                onClick={() => setHydrationData(prev => ({ amount_ml: prev.amount_ml + amount }))}
                                                className="py-3 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 rounded-xl border border-cyan-500/30 transition-all font-medium flex flex-col items-center gap-1"
                                            >
                                                <Droplets size={18} />
                                                +{amount}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {activeTab === 'progress' && (
                                <div className="space-y-6 animate-fade-in">
                                    <div>
                                        <label className="block text-sm text-muted mb-2">Weight (kg)</label>
                                        <input type="number" step="0.1" className="input-dark" value={progressData.weight_kg} onChange={e => setProgressData({...progressData, weight_kg: e.target.value})} placeholder="e.g. 70.5" />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-muted mb-2">Body Fat % (Optional)</label>
                                        <input type="number" step="0.1" className="input-dark" value={progressData.body_fat_pct} onChange={e => setProgressData({...progressData, body_fat_pct: e.target.value})} placeholder="e.g. 15.2" />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-muted mb-2">Notes</label>
                                        <textarea className="input-dark min-h-[100px]" value={progressData.notes} onChange={e => setProgressData({...progressData, notes: e.target.value})} placeholder="How are you feeling today?" />
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Footer */}
                        <div className="p-6 border-t border-white/10 bg-black/20">
                            <button 
                                onClick={handleSubmit} 
                                disabled={isSubmitting}
                                className={`w-full py-3 rounded-xl font-bold flex items-center justify-center gap-2 transition-all ${activeTab === 'hydration' ? 'bg-cyan-500 text-white hover:shadow-[0_0_20px_rgba(6,182,212,0.4)]' : 'btn-primary'}`}
                            >
                                {isSubmitting ? 'Saving...' : <>Log {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} <Check size={18} /></>}
                            </button>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
