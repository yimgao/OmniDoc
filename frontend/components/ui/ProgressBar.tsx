'use client';

import { clsx } from 'clsx';

export interface ProgressBarProps {
  value: number; // 0-100
  max?: number;
  showLabel?: boolean;
  label?: string;
  size?: 'small' | 'medium' | 'large';
  variant?: 'primary' | 'secondary' | 'accent';
  className?: string;
}

export default function ProgressBar({
  value,
  max = 100,
  showLabel = false,
  label,
  size = 'medium',
  variant = 'primary',
  className,
}: ProgressBarProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  const sizes = {
    small: 'h-1',
    medium: 'h-2',
    large: 'h-3',
  };

  const variants = {
    primary: 'bg-[#007BFF]',
    secondary: 'bg-[#6C757D]',
    accent: 'bg-[#28A745]',
  };

  return (
    <div className={clsx('w-full', className)}>
      {(showLabel || label) && (
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-[#343A40]">
            {label || `${Math.round(percentage)}%`}
          </span>
          {showLabel && label && (
            <span className="text-sm text-[#6C757D]">
              {Math.round(percentage)}%
            </span>
          )}
        </div>
      )}
      <div className={clsx('w-full bg-[#F8F9FA] rounded-full overflow-hidden', sizes[size])}>
        <div
          className={clsx(
            'h-full transition-all duration-300 ease-out rounded-full',
            variants[variant]
          )}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
          aria-label={label || `Progress: ${Math.round(percentage)}%`}
        />
      </div>
    </div>
  );
}

// Step-by-step progress indicator
export interface StepProgressProps {
  steps: string[];
  currentStep: number;
  className?: string;
}

export function StepProgress({ steps, currentStep, className }: StepProgressProps) {
  const currentIndex = Math.min(Math.max(currentStep - 1, 0), steps.length - 1);

  return (
    <div className={clsx('w-full', className)}>
      <div className="flex items-center justify-between mb-4">
        {steps.map((step, index) => {
          const isCompleted = index < currentIndex;
          const isCurrent = index === currentIndex;
          const isPending = index > currentIndex;

          return (
            <div key={index} className="flex flex-col items-center flex-1">
              {/* Step Circle */}
              <div
                className={clsx(
                  'flex items-center justify-center w-8 h-8 rounded-full border-2 transition-colors',
                  isCompleted && 'bg-[#28A745] border-[#28A745] text-white',
                  isCurrent && 'bg-[#007BFF] border-[#007BFF] text-white',
                  isPending && 'bg-white border-[#ADB5BD] text-[#6C757D]'
                )}
              >
                {isCompleted ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                ) : (
                  <span className="text-sm font-semibold">{index + 1}</span>
                )}
              </div>
              {/* Step Label */}
              <span
                className={clsx(
                  'mt-2 text-xs text-center max-w-[80px]',
                  isCurrent && 'font-semibold text-[#007BFF]',
                  !isCurrent && 'text-[#6C757D]'
                )}
              >
                {step}
              </span>
            </div>
          );
        })}
      </div>
      {/* Connecting Lines */}
      <div className="relative -mt-6 mb-6">
        {steps.slice(0, -1).map((_, index) => {
          const isCompleted = index < currentIndex;
          return (
            <div
              key={index}
              className={clsx(
                'absolute h-0.5 top-4 transition-colors',
                isCompleted ? 'bg-[#28A745]' : 'bg-[#ADB5BD]'
              )}
              style={{
                left: `${(index * 100) / (steps.length - 1)}%`,
                width: `${100 / (steps.length - 1)}%`,
              }}
            />
          );
        })}
      </div>
    </div>
  );
}

