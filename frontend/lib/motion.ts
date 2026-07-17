export const easeOut = [0.22, 1, 0.36, 1] as const;

export const durations = {
  fast: 0.16,
  medium: 0.28,
  slow: 0.48,
} as const;

export const fadeUp = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0 },
};

export const fadeIn = {
  hidden: { opacity: 0 },
  show: { opacity: 1 },
};

export const staggerContainer = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.07,
    },
  },
};
