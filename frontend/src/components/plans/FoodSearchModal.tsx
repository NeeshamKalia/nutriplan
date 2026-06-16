import React, { useState, useEffect, useRef } from 'react';
import { foodsApi } from '../../api/foods';
import type { FoodItem } from '../../types/plan';
import { LoadingSpinner } from '../ui/LoadingSpinner';

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
  const searchTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (isOpen) {
      handleSearch('');
      setQuery('');
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

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
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => {
      handleSearch(val);
    }, 300);
  };

  const handleClear = () => {
    setQuery('');
    handleSearch('');
  };

  if (!isOpen) return null;

  return (
    <div 
      className="modal-overlay" 
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="food-search-title"
    >
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2 id="food-search-title">Search Food Database</h2>
          <button className="btn-close" onClick={onClose} aria-label="Close modal">&times;</button>
        </div>
        
        <div className="modal-body">
          <div style={{ position: 'relative', marginBottom: '1rem' }}>
            <input 
              type="text" 
              className="food-search-input" 
              placeholder="Search for roti, paneer, chicken..." 
              value={query}
              onChange={handleQueryChange}
              autoFocus
              style={{ width: '100%', paddingRight: '2.5rem' }}
            />
            {query && (
              <button 
                onClick={handleClear}
                style={{
                  position: 'absolute',
                  right: '0.75rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  fontSize: '1.2rem'
                }}
                aria-label="Clear search"
              >
                &times;
              </button>
            )}
          </div>

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
