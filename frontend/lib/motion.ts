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

export const motionTokens = {
  ease: [0.22, 1, 0.36, 1] as const,
  route: { duration: 0.72 },
  reveal: { duration: 0.58 },
  quick: { duration: 0.2 },
  spring: {
    type: "spring" as const,
    stiffness: 260,
    damping: 30,
    mass: 0.8,
  },
};

export const routeVariants = {
  initial: { opacity: 0, y: 16, filter: "blur(10px)" },
  enter: { opacity: 1, y: 0, filter: "blur(0px)" },
  exit: { opacity: 0, y: -10, filter: "blur(8px)" },
};
