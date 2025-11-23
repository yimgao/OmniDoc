'use client';

import { clsx } from 'clsx';

export interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  animation?: 'pulse' | 'wave' | 'none';
}

export default function Skeleton({
  className,
  variant = 'rectangular',
  width,
  height,
  animation = 'pulse',
}: SkeletonProps) {
  const baseStyles = 'bg-[#F8F9FA] rounded-[4px]';
  
  const variants = {
    text: 'h-4 rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-[4px]',
  };

  const animations = {
    pulse: 'animate-pulse',
    wave: 'animate-[wave_1.6s_ease-in-out_0.5s_infinite]',
    none: '',
  };

  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === 'number' ? `${width}px` : width;
  if (height) style.height = typeof height === 'number' ? `${height}px` : height;

  return (
    <div
      className={clsx(
        baseStyles,
        variants[variant],
        animations[animation],
        className
      )}
      style={style}
      aria-busy="true"
      aria-label="Loading"
    />
  );
}

// Pre-built skeleton components for common use cases
export function DocumentListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center space-x-4 p-4 border border-[#ADB5BD] rounded-[8px]">
          <Skeleton variant="circular" width={40} height={40} />
          <div className="flex-1 space-y-2">
            <Skeleton variant="text" width="60%" height={16} />
            <Skeleton variant="text" width="40%" height={12} />
          </div>
        </div>
      ))}
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="p-6 border border-[#ADB5BD] rounded-[8px] space-y-4">
      <Skeleton variant="text" width="80%" height={20} />
      <Skeleton variant="text" width="100%" height={14} />
      <Skeleton variant="text" width="90%" height={14} />
      <Skeleton variant="text" width="60%" height={14} />
    </div>
  );
}

export function ContentAreaSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton variant="text" width="40%" height={32} />
      <div className="space-y-3">
        <Skeleton variant="text" width="100%" height={16} />
        <Skeleton variant="text" width="100%" height={16} />
        <Skeleton variant="text" width="95%" height={16} />
        <Skeleton variant="text" width="100%" height={16} />
        <Skeleton variant="text" width="90%" height={16} />
      </div>
      <div className="space-y-3 mt-8">
        <Skeleton variant="text" width="35%" height={24} />
        <Skeleton variant="text" width="100%" height={16} />
        <Skeleton variant="text" width="100%" height={16} />
      </div>
    </div>
  );
}

