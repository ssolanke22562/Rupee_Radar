import React, { useEffect, useRef, useState } from 'react';

interface ScrollAnimateProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  animationClass?: 'fade-in-up' | 'zoom-in' | 'slide-in-left' | 'slide-in-right';
}

export function ScrollAnimate({ 
  children, 
  className = '', 
  style = {}, 
  animationClass = 'fade-in-up' 
}: ScrollAnimateProps) {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Check if IntersectionObserver is supported
    if (!('IntersectionObserver' in window)) {
      setIsVisible(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          // Once visible, stop observing to keep element in state
          observer.unobserve(entry.target);
        }
      },
      {
        threshold: 0.08, // Trigger when 8% of the card is visible
        rootMargin: '0px 0px -40px 0px' // Offset to trigger slightly before/as it enters view
      }
    );

    const currentRef = ref.current;
    if (currentRef) {
      observer.observe(currentRef);
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef);
      }
    };
  }, []);

  return (
    <div
      ref={ref}
      className={`scroll-animate ${animationClass} ${isVisible ? 'visible' : ''} ${className}`}
      style={style}
    >
      {children}
    </div>
  );
}
