'use client';

import { ReactNode } from 'react';
import Button from './ui/Button';

export interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  primaryAction?: {
    label: string;
    onClick: () => void;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export default function EmptyState({
  icon,
  title,
  description,
  primaryAction,
  secondaryAction,
  className,
}: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center px-4 py-12 text-center ${className || ''}`}>
      {/* Icon */}
      {icon && (
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-[#F8F9FA] text-4xl">
          {icon}
        </div>
      )}

      {/* Title */}
      <h3 className="text-[20px] font-semibold text-[#343A40] mb-2">
        {title}
      </h3>

      {/* Description */}
      {description && (
        <p className="text-base text-[#6C757D] max-w-md mb-6">
          {description}
        </p>
      )}

      {/* Actions */}
      {(primaryAction || secondaryAction) && (
        <div className="flex flex-col sm:flex-row gap-3">
          {primaryAction && (
            <Button
              onClick={primaryAction.onClick}
              variant="primary"
              size="medium"
            >
              {primaryAction.label}
            </Button>
          )}
          {secondaryAction && (
            <Button
              onClick={secondaryAction.onClick}
              variant="text"
              size="medium"
            >
              {secondaryAction.label}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

