// src/components/StatusBadge.tsx
import React from "react";

const statusColors: Record<string, string> = {
  finished: "bg-green-600 text-white",
  failed: "bg-red-600 text-white",
  running: "bg-yellow-500 text-black",
  pending: "bg-gray-500 text-white",
};

export const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const color = statusColors[status.toLowerCase()] || "bg-gray-700 text-white";
  return (
    <span
      className={`px-2 py-1 rounded-full text-xs font-semibold ${color}`}
    >
      {status}
    </span>
  );
};
