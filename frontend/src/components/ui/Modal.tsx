"use client";

import { AnimatePresence, motion } from "motion/react";

export default function Modal({
  open,
  onClose,
  children,
  wide = false,
}: {
  open: boolean;
  onClose?: () => void;
  children: React.ReactNode;
  wide?: boolean;
}) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            role="dialog"
            aria-modal="true"
            className={`w-full ${wide ? "max-w-xl" : "max-w-md"} rounded-3xl bg-surface p-6 text-center shadow-2xl`}
            initial={{ scale: 0.85, y: 30 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 20, opacity: 0 }}
            transition={{ type: "spring", damping: 18, stiffness: 260 }}
            onClick={(e) => e.stopPropagation()}
          >
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
