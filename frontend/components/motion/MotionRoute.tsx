"use client";

import type { ReactNode } from "react";
import { motion, useReducedMotion } from "framer-motion";

import { motionTokens, routeVariants } from "@/lib/motion";

interface MotionRouteProps {
  routeKey: string;
  children: ReactNode;
}

export function MotionRoute({ routeKey, children }: MotionRouteProps) {
  const reduced = useReducedMotion();

  return (
    <motion.div
      key={routeKey}
      initial={reduced ? false : "initial"}
      animate="enter"
      exit="exit"
      variants={reduced ? { enter: { opacity: 1 } } : routeVariants}
      transition={{ ...motionTokens.route, ease: motionTokens.ease }}
      className="min-h-full"
    >
      {children}
    </motion.div>
  );
}
