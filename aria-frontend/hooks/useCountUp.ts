"use client";

import { useEffect, useMemo, useState } from "react";

interface UseCountUpOptions {
  duration?: number;
  decimals?: number;
}

export const useCountUp = (target: number, options: UseCountUpOptions = {}): number => {
  const duration = options.duration ?? 1200;
  const decimals = options.decimals ?? (Number.isInteger(target) ? 0 : 1);

  const [value, setValue] = useState(0);

  useEffect(() => {
    let raf = 0;
    const start = performance.now();

    const step = (time: number) => {
      const elapsed = time - start;
      const progress = Math.min(elapsed / duration, 1);
      const next = target * progress;
      setValue(next);

      if (progress < 1) {
        raf = requestAnimationFrame(step);
      }
    };

    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [duration, target]);

  return useMemo(() => Number(value.toFixed(decimals)), [decimals, value]);
};
