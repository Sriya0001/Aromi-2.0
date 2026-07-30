import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X, Send, Minus, Bot } from 'lucide-react';
import useStore from '../store/useStore';
import { aiAPI, workoutAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function AROMIAssistant() {
    const { chatOpen, toggleChatOpen, chatHistory, addChatMessage, setChatHistory, user, setWorkoutPlan } = useStore();
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const scrollRef = useRef(null);

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [chatHistory, chatOpen]);

    // Load history if empty
    useEffect(() => {
        if (chatOpen && chatHistory.length === 0) {
            aiAPI.getChatHistory().then(r => setChatHistory(r.data.history || [])).catch(() => { });
        }
    }, [chatOpen]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMsg = input.trim();
        setInput('');
        addChatMessage({ message: userMsg, response: '...', timestamp: new Date().toISOString(), loading: true });
        setLoading(true);

        try {
            const { data } = await aiAPI.chat(userMsg);
            setChatHistory([...chatHistory, { message: userMsg, response: data.response, timestamp: data.timestamp }]);

            if (data.plan_modified) {
                toast.success('AROMI updated your plan! 🔄');
                try {
                    const planRes = await workoutAPI.getPlan();
                    const newPlan = planRes.data.plan || [];
                    // Force a new array reference to ensure sync
                    setWorkoutPlan([...newPlan]);
                } catch (err) {
                    console.error("Soft refresh failed:", err);
                }
            }
        } catch (err) {
            toast.error('AROMI is resting. Try again in a bit! 🙏');
            setChatHistory(chatHistory.filter(m => !m.loading));
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            {/* Floating Button */}
            <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={toggleChatOpen}
                className="fixed bottom-6 right-6 w-14 h-14 rounded-full icon-purple text-white shadow-2xl z-50 flex items-center justify-center pulse-glow"
            >
                {chatOpen ? <X size={24} /> : <MessageCircle size={24} />}
            </motion.button>

            {/* Chat Window */}
            <AnimatePresence>
                {chatOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 100, scale: 0.8 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 100, scale: 0.8 }}
                        className="fixed bottom-24 right-6 w-[90vw] sm:w-[400px] h-[500px] glass z-50 flex flex-col overflow-hidden shadow-2xl border border-brand-border"
                    >
                        {/* Header */}
                        <div className="p-4 border-b border-brand-border flex items-center justify-between icon-purple text-white">
                            <div className="flex items-center gap-2">
                                <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
                                    <Bot size={18} />
                                </div>
                                <div>
                                    <h3 className="font-bold text-sm">AROMI AI Coach</h3>
                                    <p className="text-[10px] text-purple-200">Online • Your Fitness Buddy</p>
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <button onClick={toggleChatOpen} className="hover:bg-white/10 p-1 rounded transition-colors">
                                    <Minus size={16} />
                                </button>
                            </div>
                        </div>

                        {/* Messages */}
                        <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 bg-mesh">
                            {chatHistory.length === 0 ? (
                                <div className="text-center py-10">
                                    <div className="w-16 h-16 rounded-2xl icon-purple flex items-center justify-center text-3xl mx-auto mb-4 animate-float">🤖</div>
                                    <h4 className="text-white font-semibold">Namaste {user?.username || 'Ji'}!</h4>
                                    <p className="text-slate-400 text-xs px-10">I am AROMI, your AI fitness coach. How can I help you today?</p>
                                </div>
                            ) : (
                                chatHistory.map((chat, i) => (
                                    <React.Fragment key={i}>
                                        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="chat-user text-white text-sm">
                                            {chat.message}
                                        </motion.div>
                                        <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="chat-aromi text-slate-300 text-sm">
                                            {chat.response === '...' ? (
                                                <div className="flex gap-1 py-1">
                                                    <div className="typing-dot" />
                                                    <div className="typing-dot" />
                                                    <div className="typing-dot" />
                                                </div>
                                            ) : chat.response}
                                        </motion.div>
                                    </React.Fragment>
                                ))
                            )}
                        </div>

                        {/* Input */}
                        <form onSubmit={handleSend} className="p-4 border-t border-brand-border bg-brand-dark/50 flex gap-2">
                            <input
                                type="text"
                                className="input-dark text-sm flex-1"
                                placeholder="Ask AROMI anything..."
                                value={input}
                                onChange={e => setInput(e.target.value)}
                                disabled={loading}
                            />
                            <button
                                type="submit"
                                disabled={loading || !input.trim()}
                                className="w-10 h-10 rounded-xl icon-purple flex items-center justify-center text-white disabled:opacity-50"
                            >
                                <Send size={18} />
                            </button>
                        </form>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}
