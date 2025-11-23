'use client';

import { useState, useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';

interface PlaceholdersAndVanishInputProps {
  placeholders: string[];
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
  value: string;
  className?: string;
  disabled?: boolean;
  maxLength?: number;
  minHeight?: string;
  onSendClick?: () => void;
  isSubmitting?: boolean;
}

export function PlaceholdersAndVanishInput({
  placeholders,
  onChange,
  onSubmit,
  value,
  className,
  disabled = false,
  maxLength = 5000,
  minHeight = '120px',
  onSendClick,
  isSubmitting = false,
}: PlaceholdersAndVanishInputProps) {
  const [currentPlaceholder, setCurrentPlaceholder] = useState(0);
  const [isVanish, setIsVanish] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const placeholderRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (value) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      return;
    }

    const startInterval = () => {
      intervalRef.current = setInterval(() => {
        setIsAnimating(true);
        setTimeout(() => {
          setCurrentPlaceholder((prev) => (prev + 1) % placeholders.length);
          setIsAnimating(false);
        }, 300);
      }, 3000);
    };

    startInterval();
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [placeholders.length, value]);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!value.trim() || disabled) return;
    
    setIsVanish(true);
    setTimeout(() => {
      onSubmit(e);
      setIsVanish(false);
    }, 300);
  };

  const handleSendClick = () => {
    if (onSendClick) {
      onSendClick();
    } else {
      const form = document.getElementById('userIdeaForm') as HTMLFormElement;
      if (form) {
        form.requestSubmit();
      }
    }
  };

  return (
    <form
      id="userIdeaForm"
      className={cn(
        'relative w-full',
        isVanish && 'opacity-0 scale-95 transition-all duration-300',
        className
      )}
      onSubmit={handleSubmit}
    >
      <div className="relative w-full">
        <textarea
          value={value}
          onChange={onChange}
          disabled={disabled}
          placeholder=""
          maxLength={maxLength}
          aria-label="Enter your project idea"
          aria-describedby="charCount"
          className={cn(
            'w-full rounded-2xl border border-gray-300 bg-white px-4 py-3 pr-14 text-gray-900',
            'focus:border-[#007BFF] focus:outline-none focus:ring-2 focus:ring-[#007BFF]',
            'disabled:cursor-not-allowed disabled:opacity-50',
            'transition-all duration-200 resize-none',
            'min-h-[120px] max-h-[300px]'
          )}
          style={{ minHeight }}
          suppressHydrationWarning
        />
        
        {/* Animated Placeholder */}
        {!value && (
          <div
            ref={placeholderRef}
            className={cn(
              'absolute left-4 top-3 pointer-events-none text-gray-400 transition-all duration-300',
              isAnimating && 'opacity-0 -translate-y-2'
            )}
            suppressHydrationWarning
          >
            {placeholders[currentPlaceholder]}
          </div>
        )}

        {/* Send Button - Inside input box, bottom right */}
        <button
          type="submit"
          aria-label={isSubmitting ? 'Submitting project idea' : 'Submit project idea'}
          disabled={disabled || !value.trim() || isSubmitting}
          onClick={handleSendClick}
          className={cn(
            'absolute bottom-3 right-3 flex h-8 w-8 items-center justify-center rounded-full z-10',
            'bg-[#007BFF] text-white transition-colors',
            'hover:bg-[#0056b3] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-[#007BFF]',
            'focus:outline-none focus:ring-2 focus:ring-[#007BFF] focus:ring-offset-2'
          )}
          suppressHydrationWarning
        >
          {isSubmitting ? (
            <svg
              className="h-4 w-4 animate-spin text-white"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          ) : (
            <svg
              className="h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
              />
            </svg>
          )}
        </button>
      </div>
    </form>
  );
}

