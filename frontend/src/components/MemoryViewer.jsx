import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Brain, Sparkles, RefreshCw, AlertCircle, Database } from 'lucide-react';
import { getMemories, triggerMemoryExtraction } from '../services/api';
import toast from 'react-hot-toast';

export default function MemoryViewer() {
    const [memories, setMemories] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isExtracting, setIsExtracting] = useState(false);

    const fetchMemories = async () => {
        setIsLoading(true);
        try {
            const res = await getMemories();
            const memoryList = res.data?.memories || (Array.isArray(res.data) ? res.data : []);
            setMemories(memoryList);
        } catch (error) {
            console.error(error);
            toast.error("Failed to load memories");
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchMemories();
    }, []);

    const handleExtraction = async () => {
        setIsExtracting(true);
        try {
            await triggerMemoryExtraction();
            toast.success("Memory extraction completed!");
            await fetchMemories();
        } catch (error) {
            toast.error("Extraction failed");
        } finally {
            setIsExtracting(false);
        }
    };

    const groupedMemories = memories.reduce((acc, mem) => {
        let cat = mem.type || mem.category || 'other';
        if (cat === 'preference') cat = 'preferences';
        else if (cat === 'avoidance') cat = 'avoidances';
        else if (cat === 'pattern') cat = 'patterns';
        else if (cat === 'achievement') cat = 'achievements';
        else if (cat === 'injury') cat = 'injuries';
        
        if (!acc[cat]) acc[cat] = [];
        acc[cat].push(mem);
        return acc;
    }, {});

    const categories = ['preferences', 'injuries', 'patterns', 'avoidances', 'achievements', 'other'];

    const getConfidenceColor = (conf) => {
        if (conf > 0.7) return 'bg-green-500';
        if (conf >= 0.4) return 'bg-yellow-500';
        return 'bg-red-500';
    };

    return (
        <div className="min-h-screen bg-mesh pt-24 pb-12 px-4">
            <div className="max-w-6xl mx-auto">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
                    <div>
                        <h1 className="text-3xl font-bold gradient-text flex items-center gap-3">
                            <Brain className="text-purple-500" /> AroMi Memory Core
                        </h1>
                        <p className="text-muted mt-2">What I've learned about you over time to personalize your coaching.</p>
                    </div>
                    <button 
                        onClick={handleExtraction}
                        disabled={isExtracting}
                        className="btn-primary cursor-pointer disabled:opacity-60"
                    >
                        <RefreshCw size={18} className={isExtracting ? 'animate-spin' : ''} />
                        {isExtracting ? 'Analyzing Chats...' : 'Update Memories'}
                    </button>
                </div>

                {isLoading ? (
                    <div className="flex justify-center items-center h-64">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
                    </div>
                ) : memories.length === 0 ? (
                    <div className="glass-card p-12 text-center flex flex-col items-center">
                        <div className="w-32 h-32 bg-purple-500/10 rounded-full flex items-center justify-center mb-6 pulse-glow">
                            <Sparkles size={48} className="text-purple-400" />
                        </div>
                        <h2 className="text-2xl font-bold mb-2">AroMi is still learning about you...</h2>
                        <p className="text-muted max-w-md mx-auto mb-8">
                            As you interact with me, log workouts, and ask questions, I will build a personalized knowledge base here.
                        </p>
                        <button onClick={handleExtraction} className="btn-secondary cursor-pointer">
                            Trigger Manual Extraction
                        </button>
                    </div>
                ) : (
                    <div className="space-y-12">
                        {categories.map(cat => {
                            if (!groupedMemories[cat] || groupedMemories[cat].length === 0) return null;
                            return (
                                <div key={cat} className="animate-fade-in">
                                    <h2 className="text-xl font-bold mb-6 capitalize flex items-center gap-2 border-b border-white/10 pb-2">
                                        <Database className="text-purple-500" size={20} /> {cat}
                                    </h2>
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                        {groupedMemories[cat].map(mem => {
                                            const conf = mem.confidence || 0.5;
                                            return (
                                                <motion.div 
                                                    whileHover={{ y: -5 }}
                                                    key={mem.id} 
                                                    className="glass-card p-5 relative overflow-hidden"
                                                >
                                                    <div className="absolute top-4 right-4 text-xs font-medium px-2 py-1 bg-white/5 rounded-md text-muted border border-white/10">
                                                        {mem.source || 'chat'}
                                                    </div>
                                                    
                                                    <h3 className="font-semibold text-lg text-white mb-1 pr-16 capitalize">{mem.key.replace(/_/g, ' ')}</h3>
                                                    <p className="text-gray-300 text-sm mb-6">{mem.value}</p>
                                                    
                                                    <div className="mt-auto pt-4 border-t border-white/5">
                                                        <div className="flex justify-between items-center mb-2">
                                                            <span className="text-xs text-muted">Confidence</span>
                                                            <span className="text-xs font-medium text-white">{Math.round(conf * 100)}%</span>
                                                        </div>
                                                        <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                                                            <div 
                                                                className={`h-full ${getConfidenceColor(conf)} rounded-full`}
                                                                style={{ width: `${conf * 100}%` }}
                                                            />
                                                        </div>
                                                        {mem.last_reinforced && (
                                                            <p className="text-[10px] text-muted mt-3 text-right">
                                                                Last reinforced: {new Date(mem.last_reinforced).toLocaleDateString()}
                                                            </p>
                                                        )}
                                                    </div>
                                                </motion.div>
                                            );
                                        })}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
