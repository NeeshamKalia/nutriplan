import React, { useState, useEffect } from 'react';
import { foodsApi } from '../../api/foods';
import { FoodItem } from '../../types/plan';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { Button } from '../ui/Button';

import './FoodSearchModal.css';

interface FoodSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (food: FoodItem) => void;
}

export const FoodSearchModal: React.FC<FoodSearchModalProps> = ({ isOpen, onClose, onSelect }) => {
  const [query, setQuery] = useState('');
  const [foods, setFoods] = useState<FoodItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      handleSearch('');
    }
  }, [isOpen]);

  const handleSearch = async (searchQuery: string) => {
    setLoading(true);
    try {
      const data = await foodsApi.searchFoods({ q: searchQuery });
      setFoods(data.items);
    } catch (err) {
      console.error('Failed to search foods', err);
    } finally {
      setLoading(false);
    }
  };

  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    // basic debounce
    if (window.searchTimeout) clearTimeout(window.searchTimeout);
    window.searchTimeout = setTimeout(() => {
      handleSearch(val);
    }, 300);
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Search Food Database</h2>
          <button className="btn-close" onClick={onClose}>&times;</button>
        </div>
        
        <div className="modal-body">
          <input 
            type="text" 
            className="food-search-input" 
            placeholder="Search for roti, paneer, chicken..." 
            value={query}
            onChange={handleQueryChange}
            autoFocus
          />

          <div className="food-results">
            {loading ? (
              <div className="loading-container"><LoadingSpinner /></div>
            ) : foods.length === 0 ? (
              <div className="empty-results">No foods found.</div>
            ) : (
              foods.map(food => (
                <div key={food.id} className="food-result-card" onClick={() => onSelect(food)}>
                  <div className="food-info">
                    <h4>{food.name} {food.name_hindi && <span className="hindi-name">({food.name_hindi})</span>}</h4>
                    <span className="food-portion">{food.default_serving_description || `${food.default_serving_grams}g`}</span>
                  </div>
                  <div className="food-macros">
                    <span className="macro-badge macro-cal">{food.calories_per_100g} kcal</span>
                    <span className="macro-badge macro-p">P: {food.protein_per_100g}g</span>
                    <span className="macro-badge macro-c">C: {food.carbs_per_100g}g</span>
                    <span className="macro-badge macro-f">F: {food.fat_per_100g}g</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Typescript declaration for window
declare global {
  interface Window {
    searchTimeout: any;
  }
}
