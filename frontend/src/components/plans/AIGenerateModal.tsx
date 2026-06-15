import React, { useState, useEffect } from 'react';
import { Button } from '../ui/Button';
import { LoadingSpinner } from '../ui/LoadingSpinner';

interface AIGenerateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onGenerate: (instructions: string) => Promise<void>;
  isLoading: boolean;
}

export const AIGenerateModal: React.FC<AIGenerateModalProps> = ({
  isOpen,
  onClose,
  onGenerate,
  isLoading
}) => {
  const [instructions, setInstructions] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !isLoading) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isLoading, onClose]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="ai-modal-title"
    >
      <div className="bg-white dark:bg-gray-800 rounded-xl w-full max-w-lg shadow-xl overflow-hidden flex flex-col">
        <div className="p-6">
          <h2 id="ai-modal-title" className="text-xl font-bold mb-2">Generate Plan with AI</h2>
          
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            The AI will generate a 7-day plan based on the client's health profile, allergies, and preferences.
          </p>

          <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-md text-sm">
            <p className="font-medium">⏱️ Estimated time: 10-25 seconds</p>
            <p>💡 Uses Gemini 2.0 Flash (Free Tier) - No cost</p>
          </div>

          <div className="mb-6">
            <label htmlFor="ai-instructions" className="block text-sm font-medium mb-2">Custom Instructions (Optional)</label>
            <textarea
              id="ai-instructions"
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder="e.g., Focus on anti-inflammatory foods, keep dinners light..."
              className="w-full min-h-[100px] p-3 rounded-md border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 focus:ring-2 focus:ring-primary-500 outline-none"
              disabled={isLoading}
              autoFocus
            />
          </div>

          <div className="flex justify-end gap-3">
            <Button variant="ghost" onClick={onClose} disabled={isLoading} aria-label="Cancel AI generation">
              Cancel
            </Button>
            <Button 
              variant="primary" 
              onClick={() => onGenerate(instructions)} 
              disabled={isLoading}
              className="flex items-center gap-2"
            >
              {isLoading && <LoadingSpinner size="sm" />}
              {isLoading ? 'Generating...' : 'Generate Plan'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
