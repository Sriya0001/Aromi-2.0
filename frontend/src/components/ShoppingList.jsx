import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Check, ShoppingCart, ExternalLink } from 'lucide-react';

export default function ShoppingList({ items: initialItems, bigbasketUrl }) {
    const [items, setItems] = useState([]);

    useEffect(() => {
        if (!initialItems || initialItems.length === 0) {
            setItems([]);
            return;
        }
        const saved = localStorage.getItem('arogyamitra_shopping_list');
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    const merged = initialItems.map(initItem => {
                        const found = parsed.find(p => p.name === initItem.name);
                        return found ? { ...initItem, ...found } : initItem;
                    });
                    setItems(merged);
                } else {
                    setItems(initialItems);
                }
            } catch (e) {
                setItems(initialItems);
            }
        } else {
            setItems(initialItems);
        }
    }, [initialItems]);

    useEffect(() => {
        if (items.length > 0) {
            localStorage.setItem('arogyamitra_shopping_list', JSON.stringify(items));
        }
    }, [items]);

    const toggleCheck = (name) => {
        setItems(prev => prev.map(item =>
            item.name === name ? { ...item, checked: !item.checked } : item
        ));
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <ShoppingCart className="text-purple-400" /> Weekly Shopping List
                </h2>
            </div>

            <div className="space-y-2">
                {items.map((item, i) => (
                    <motion.div
                        key={item.name}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.05 }}
                        className={`glass-card p-4 flex items-center justify-between group transition-all ${!item.checked ? 'opacity-50' : ''}`}
                    >
                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => toggleCheck(item.name)}
                                className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${item.checked
                                    ? 'bg-green-500 border-green-500 text-white'
                                    : 'border-slate-600 hover:border-slate-400'
                                    }`}
                            >
                                {item.checked && <Check size={14} strokeWidth={3} />}
                            </button>

                            <span className={`text-white font-medium ${!item.checked ? 'line-through text-slate-500' : ''}`}>
                                {item.name}
                            </span>
                        </div>

                        <div className="flex items-center gap-6">
                            <a
                                href={`https://www.bigbasket.com/ps/?q=${encodeURIComponent(item.name)}`}
                                target="_blank"
                                rel="noreferrer"
                                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-orange-500 text-white text-xs font-bold hover:bg-orange-600 transition-all shadow-lg shadow-orange-500/20"
                            >
                                <ShoppingCart size={12} /> Buy <ExternalLink size={10} />
                            </a>
                        </div>
                    </motion.div>
                ))}
        </div>
    </div>
    );
}
