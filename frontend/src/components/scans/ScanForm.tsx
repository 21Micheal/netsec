import React, { useState } from "react";
import { API_BASE_URL } from "../../config/runtime";

type Props = {
  onCreated?: (jobId: string) => void; // callback when job created
};

export default function StartScanForm({ onCreated }: Props) {
  const [target, setTarget] = useState("");
  const [profile, setProfile] = useState("default");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    setError(null);

    if (!target) {
      setError("Target is required (IP or hostname).");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/scans/combined`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target, profile }),
      });

      if (!res.ok) {
        // Try to parse error message from response
        let errorMessage = "Failed to create scan job";
        try {
          const errorData = await res.json();
          errorMessage = errorData.error || errorMessage;
        } catch {
          errorMessage = `HTTP error! status: ${res.status}`;
        }
        throw new Error(errorMessage);
      }

      const data = await res.json();
      
      // Clear form and notify parent
      setTarget("");
      setProfile("default");
      if (onCreated && data.job_id) {
        onCreated(data.job_id);
      }
    } catch (err) {
      console.error("Scan submission error:", err);
      setError(err instanceof Error ? err.message : "Network error — could not reach backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto p-4 bg-gray-900 rounded-md border border-gray-700">
      <div className="flex flex-col sm:flex-row gap-3 items-start">
        <input
          className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
          placeholder="Enter target (e.g. scanme.nmap.org or 192.168.1.1)"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          aria-label="scan target"
        />

        <select
          className="w-40 px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-white"
          value={profile}
          onChange={(e) => setProfile(e.target.value)}
          aria-label="scan profile"
        >
          <option value="default">Default</option>
          <option value="fast">Fast</option>
          <option value="full">Full</option>
          <option value="web">Web-only</option>
        </select>

        <button
          type="submit"
          className="px-4 py-2 bg-sky-600 hover:bg-sky-500 disabled:opacity-60 text-white rounded text-sm"
          disabled={loading}
        >
          {loading ? "Starting…" : "Start New Scan"}
        </button>
      </div>

      {error && (
        <div className="mt-3 p-2 bg-red-900 border border-red-700 rounded text-red-200 text-sm">
          {error}
        </div>
      )}

      <div className="mt-3 text-xs text-gray-400">
        <span className="text-gray-300">Tip:</span> prefer scan profiles `<code>fast</code>` for quick sweeps.
      </div>
    </form>
  );
}

// import { useState } from "react";

// type Props = {
//   onSubmit: () => void;
// };

// export default function ScanForm({ onSubmit }: Props) {
//   const [target, setTarget] = useState("");
//   const [profile, setProfile] = useState("default");

//   const handleSubmit = async (e: React.FormEvent) => {
//     e.preventDefault();
//     await fetch("http://localhost:5000/api/scans", {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({ target, profile }),
//     });
//     setTarget("");
//     setProfile("default");
//     onSubmit();
//   };

//   return (
//     <form
//       onSubmit={handleSubmit}
//       className="flex flex-col md:flex-row gap-3 mb-8"
//     >
//       <input
//         type="text"
//         value={target}
//         onChange={(e) => setTarget(e.target.value)}
//         placeholder="Target (IP or domain)"
//         className="px-3 py-2 rounded text-black flex-1"
//         required
//       />
//       <select
//         value={profile}
//         onChange={(e) => setProfile(e.target.value)}
//         className="px-3 py-2 rounded text-black"
//       >
//         <option value="default">Default</option>
//         <option value="fast">Fast</option>
//         <option value="full">Full</option>
//       </select>
//       <button
//         type="submit"
//         className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded"
//       >
//         Run Scan
//       </button>
//     </form>
//   );
// }
