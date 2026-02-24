// src/components/ScanResults.tsx
import React, { useEffect, useState } from "react";
import { socket } from "@/lib/socket";

interface ScanResultsProps {
  jobId: string;
}

const ScanResults: React.FC<ScanResultsProps> = ({ jobId }) => {
  const [logs, setLogs] = useState<string[]>([]);
  const [results, setResults] = useState<any>(null);
  const [status, setStatus] = useState<string>("pending");

  useEffect(() => {
    socket.emit("subscribe", { job_id: jobId });
    console.log(`✅ Subscribed to job_${jobId}`);

    socket.on("scan_log", (data: any) => {
      if (data.job_id === jobId) {
        setLogs((prev) => [...prev, data.log_line]);
      }
    });

    socket.on("scan_update", (data: any) => {
      if (data.job_id === jobId && data.status) {
        setStatus(data.status);
      }
    });

    socket.on("scan_complete", (data: any) => {
      if (data.job_id === jobId) {
        setStatus("completed");
        fetchResults();
      }
    });

    return () => {
      socket.emit("unsubscribe", { job_id: jobId });
      socket.off("scan_log");
      socket.off("scan_update");
      socket.off("scan_complete");
    };
  }, [jobId]);

  const fetchResults = async () => {
    try {
      const res = await fetch(`/api/scans/scan-jobs/${jobId}/results`);
      const json = await res.json();
      setResults(json);
    } catch (err) {
      console.error("Failed to fetch scan results:", err);
    }
  };

  return (
    <div className="bg-gray-900 text-gray-200 rounded-xl p-6 w-full shadow-lg">
      <h2 className="text-xl font-semibold mb-2">Scan Job ID: {jobId}</h2>
      <p className="text-sm text-gray-400 mb-4">Status: {status}</p>

      <div className="border border-gray-700 rounded-lg p-3 h-64 overflow-y-auto font-mono text-sm bg-black/40">
        {logs.length > 0 ? (
          logs.map((line, i) => (
            <div key={i} className="text-green-400">
              {line}
            </div>
          ))
        ) : (
          <div className="text-gray-500">Awaiting logs...</div>
        )}
      </div>

      {results && (
        <div className="mt-6 bg-gray-800 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-blue-300 mb-2">
            Scan Results
          </h3>
          <pre className="text-xs text-gray-300 whitespace-pre-wrap">
            {JSON.stringify(results, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default ScanResults;


// import React, { useEffect, useRef, useState } from "react";
// import { StatusBadge } from "./StatusBadge";
// import {
//   RotateCcw,
//   Pause,
//   Play,
//   Download,
//   Search,
//   X,
// } from "lucide-react";

// // Import the socket service instead of direct io import
// import socketService from "../services/socket";

// // --- INTERFACES ---

// interface ScanJob {
//   id: string;
//   target: string;
//   profile: string;
//   status: string;
//   created_at: string;
//   finished_at: string | null;
//   progress: number;
// }

// // Original Result (Port/Service Scan) - Keeping for reference, but replacing usage in the Drawer
// // For simplicity in this update, we will assume all fetched results will conform to the new WebScanResult structure
// interface PortScanResult {
//   id: number;
//   job_id: string;
//   target: string;
//   port: number | null;
//   protocol: string | null;
//   service: string | null;
//   version: string | null;
//   discovered_at: string;
// }

// // NEW Result (Web/Vulnerability Scan) from the provided snippet
// interface WebScanResult {
//   id: number;
//   url: string;
//   status: string; // e.g., 'completed', 'in-progress', 'error'
//   headers: Record<string, string>;
//   cookies: Record<string, string>;
//   issues: string[];
//   timestamp: string;
// }

// interface ScanResultsProps {
//   jobId?: string;
// }

// // --- CONSTANTS ---
// const PAGE_SIZE = 10;

// // --- MAIN COMPONENT ---
// const ScanResults: React.FC<ScanResultsProps> = ({ jobId }) => {
//   const [scans, setScans] = useState<ScanJob[]>([]);
//   // Changed state to use the new WebScanResult structure
//   const [scanResults, setScanResults] = useState<{ [jobId: string]: WebScanResult[] }>({});
//   const [page, setPage] = useState(0);
//   const [autoRefresh, setAutoRefresh] = useState(true);
//   const [highlightIds, setHighlightIds] = useState<Set<string>>(new Set());
//   const [filter, setFilter] = useState("");
//   const [selectedScan, setSelectedScan] = useState<ScanJob | null>(null);
//   // Separate state for the results of the currently selected scan
//   const [selectedScanResults, setSelectedScanResults] = useState<WebScanResult[]>([]);
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState<string | null>(null);

//   const bottomRef = useRef<HTMLDivElement | null>(null);

//   // Helper function to update a single scan in the state array
//   const updateScanInState = (
//     currentScans: ScanJob[],
//     updatedScan: Partial<ScanJob> & { id: string }
//   ): ScanJob[] => {
//     return currentScans.map((s) => {
//       // Update the main scan object
//       if (s.id === updatedScan.id) {
//         return { ...s, ...updatedScan };
//       }
//       return s;
//     });
//   };

//   const fetchScans = async () => {
//     try {
//       setError(null);
//       const url = jobId
//         ? `http://localhost:5000/api/scans/scan-jobs/${jobId}`
//         : 'http://localhost:5000/api/scans/scan-jobs';

//       const res = await fetch(url);
//       if (!res.ok) {
//         throw new Error(`HTTP error! status: ${res.status}`);
//       }

//       const data = await res.json();
//       const newScans: ScanJob[] = Array.isArray(data) ? data : [data];

//       // Logic to find new IDs for highlighting
//       const newIds = newScans
//         .map((s) => s.id)
//         .filter((id) => !scans.some((old) => old.id === id));

//       if (newIds.length > 0) {
//         setHighlightIds((prev) => new Set([...prev, ...newIds]));
//         setTimeout(() => {
//           setHighlightIds((prev) => {
//             const updated = new Set(prev);
//             newIds.forEach((id) => updated.delete(id));
//             return updated;
//           });
//         }, 3000);
//       }

//       setScans(newScans);
//     } catch (err) {
//       console.error("Error fetching scans", err);
//       setError(err instanceof Error ? err.message : 'Failed to fetch scans');
//     } finally {
//       setLoading(false);
//     }
//   };

//   const fetchScanResults = async (jobId: string): Promise<WebScanResult[]> => {
//     try {
//       const res = await fetch(`http://localhost:5000/api/scans/scan-jobs/${jobId}/results`);
//       if (!res.ok) {
//         throw new Error(`HTTP error! status: ${res.status}`);
//       }
//       // Assuming the API now returns WebScanResult[]
//       const results: WebScanResult[] = await res.json();
//       setScanResults(prev => ({
//         ...prev,
//         [jobId]: results
//       }));
//       return results;
//     } catch (err) {
//       console.error("Error fetching scan results", err);
//       return [];
//     }
//   };

//   // Socket.IO and polling logic
//   useEffect(() => {
//     // Connect to Socket.IO
//     const socket = socketService.connect();

//     // Set up Socket.IO listeners for real-time updates
//     socket.on("scan_update", (data: Partial<ScanJob> & { job_id: string }) => {
//       setScans((prevScans) => {
//         const updatedScans = updateScanInState(prevScans, {
//           id: data.job_id,
//           ...data
//         });

//         // Also update the selected scan if it's the one that changed
//         if (selectedScan && selectedScan.id === data.job_id) {
//           setSelectedScan(prev => prev ? {...prev, ...data} : null);
//         }

//         return updatedScans;
//       });
//     });

//     socket.on("scan_log", (log: { job_id: string; log_line: string }) => {
//       console.log('Scan log received:', log);
//       // You can handle log updates here if needed
//     });

//     // Initial fetch
//     fetchScans();

//     // Set up polling if auto-refresh is enabled
//     let interval: NodeJS.Timeout;
//     if (autoRefresh) {
//       interval = setInterval(fetchScans, 5000);
//     }

//     // Cleanup function
//     return () => {
//       if (interval) {
//         clearInterval(interval);
//       }
//       socketService.disconnect();
//     };
//   }, [jobId, autoRefresh, selectedScan]);

//   // Fetch results when a scan is selected
//   useEffect(() => {
//     if (selectedScan) {
//       // Check if results are already cached
//       if (scanResults[selectedScan.id]) {
//         setSelectedScanResults(scanResults[selectedScan.id]);
//       } else {
//         // Fetch and update cache/selected state
//         fetchScanResults(selectedScan.id).then(results => {
//           setSelectedScanResults(results);
//         });
//       }
//     }
//   }, [selectedScan, scanResults]);

//   const retryScan = async (scan: ScanJob) => {
//     try {
//       const res = await fetch(`http://localhost:5000/api/scans/scan-jobs/${scan.id}/retry`, {
//         method: "POST"
//       });
//       if (!res.ok) throw new Error("Retry failed");
//       await fetchScans();
//     } catch (err) {
//       console.error("Retry error", err);
//       setError('Failed to retry scan');
//     }
//   };

//   const filtered = scans.filter(
//     (s) =>
//       s.target.toLowerCase().includes(filter.toLowerCase()) ||
//       s.status.toLowerCase().includes(filter.toLowerCase()) ||
//       s.profile.toLowerCase().includes(filter.toLowerCase())
//   );

//   const start = page * PAGE_SIZE;
//   const end = start + PAGE_SIZE;

//   // Sort filtered scans to put running ones at the top, then by creation date
//   const sortedAndPaginatedScans = filtered
//     .sort((a, b) => {
//       // Running jobs first
//       if (a.status === "running" && b.status !== "running") return -1;
//       if (a.status !== "running" && b.status === "running") return 1;
//       // Then by newest created date
//       return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
//     })
//     .slice(start, end);

//   useEffect(() => {
//     const isLastPage = page === Math.max(Math.ceil(filtered.length / PAGE_SIZE) - 1, 0);
//     if (isLastPage && bottomRef.current) {
//       bottomRef.current.scrollIntoView({ behavior: "smooth" });
//     }
//   }, [filtered, page]);

//   const summary = {
//     running: scans.filter((s) => s.status === "running").length,
//     finished: scans.filter((s) => s.status === "finished").length,
//     failed: scans.filter((s) => s.status === "failed").length,
//   };

//   const exportCSV = () => {
//     const rows = [
//       ["ID", "Target", "Profile", "Status", "Progress", "Created", "Finished"],
//       ...filtered.map((s) => [
//         s.id,
//         s.target,
//         s.profile,
//         s.status,
//         s.progress,
//         s.created_at,
//         s.finished_at || "",
//       ]),
//     ];
//     const csvContent =
//       "data:text/csv;charset=utf-8," +
//       rows.map((r) => r.map((x) => `"${x}"`).join(",")).join("\n");
//     const a = document.createElement("a");
//     a.href = encodeURI(csvContent);
//     a.download = "scans.csv";
//     a.click();
//   };

//   if (loading) {
//     return (
//       <div className="flex justify-center items-center py-8">
//         <div className="text-white">Loading scans...</div>
//       </div>
//     );
//   }

//   if (error) {
//     return (
//       <div className="bg-red-900 border border-red-700 text-white p-4 rounded mb-4">
//         Error: {error}
//         <button
//           onClick={fetchScans}
//           className="ml-4 px-3 py-1 bg-red-700 rounded hover:bg-red-600"
//         >
//           Retry
//         </button>
//       </div>
//     );
//   }

//   return (
//     <div className="relative">
//       <h2 className="text-xl font-bold mb-4 flex justify-between items-center">
//         Scan Results
//         <div className="flex gap-2">
//           <button
//             onClick={() => setAutoRefresh((p) => !p)}
//             className="px-3 py-1 bg-gray-700 rounded text-white flex items-center gap-1 hover:bg-gray-600 transition-colors"
//           >
//             {autoRefresh ? <Pause size={14} /> : <Play size={14} />}
//             {autoRefresh ? "Pause" : "Resume"}
//           </button>
//           <button
//             onClick={exportCSV}
//             className="px-3 py-1 bg-blue-700 rounded text-white flex items-center gap-1 hover:bg-blue-600 transition-colors"
//           >
//             <Download size={14} /> Export CSV
//           </button>
//         </div>
//       </h2>

//       {/* Filters + Summary */}
//       <div className="flex justify-between items-center mb-3">
//         <div className="flex items-center gap-2">
//           <Search size={16} className="text-gray-400" />
//           <input
//             type="text"
//             placeholder="Filter scans..."
//             value={filter}
//             onChange={(e) => setFilter(e.target.value)}
//             className="px-2 py-1 rounded bg-gray-800 text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
//           />
//         </div>
//         <div className="text-sm text-gray-400">
//           Running: {summary.running} | Finished: {summary.finished} | Failed:{" "}
//           {summary.failed}
//         </div>
//       </div>

//       {/* Table */}
//       <table className="min-w-full border border-gray-700 text-sm">
//         <thead>
//           <tr className="bg-gray-800 text-gray-200">
//             <th className="px-4 py-2 text-left">Target</th>
//             <th className="px-4 py-2 text-left">Profile</th>
//             <th className="px-4 py-2 text-left">Status</th>
//             <th className="px-4 py-2 text-left">Progress</th>
//             <th className="px-4 py-2 text-left">Created At</th>
//             <th className="px-4 py-2 text-left">Finished At</th>
//             <th className="px-4 py-2">Actions</th>
//           </tr>
//         </thead>
//         <tbody>
//           {sortedAndPaginatedScans.map((scan) => (
//             <ScanRow
//               key={scan.id}
//               scan={scan}
//               retryScan={retryScan}
//               highlight={highlightIds.has(scan.id)}
//               onSelect={() => setSelectedScan(scan)}
//             />
//           ))}
//         </tbody>
//       </table>

//       {filtered.length === 0 && (
//         <div className="text-center py-8 text-gray-400">
//           No scans found
//         </div>
//       )}

//       <div ref={bottomRef} />

//       {/* Pagination */}
//       {filtered.length > 0 && (
//         <div className="flex justify-between items-center mt-4">
//           <button
//             onClick={() => setPage((p) => Math.max(p - 1, 0))}
//             disabled={page === 0}
//             className="px-3 py-1 rounded bg-gray-700 text-white disabled:opacity-50 hover:bg-gray-600 transition-colors"
//           >
//             Previous
//           </button>
//           <span className="text-gray-300">
//             Page {page + 1} of {Math.ceil(filtered.length / PAGE_SIZE) || 1}
//           </span>
//           <button
//             onClick={() =>
//               setPage((p) =>
//                 p + 1 < Math.ceil(filtered.length / PAGE_SIZE) ? p + 1 : p
//               )
//             }
//             disabled={end >= filtered.length}
//             className="px-3 py-1 rounded bg-gray-700 text-white disabled:opacity-50 hover:bg-gray-600 transition-colors"
//           >
//             Next
//           </button>
//         </div>
//       )}

//       {/* Drawer */}
//       {selectedScan && (
//         <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-end">
//           <div className="w-1/2 bg-gray-900 h-full shadow-xl p-6 overflow-y-auto">
//             <div className="flex justify-between items-center mb-4">
//               <h3 className="text-lg font-bold">Scan Details: {selectedScan.target}</h3>
//               <button
//                 onClick={() => setSelectedScan(null)}
//                 className="text-gray-400 hover:text-white transition-colors"
//               >
//                 <X size={20} />
//               </button>
//             </div>

//             <div className="grid grid-cols-2 gap-4 mb-6">
//               <div>
//                 <p><strong>Target:</strong> {selectedScan.target}</p>
//                 <p><strong>Profile:</strong> {selectedScan.profile}</p>
//                 <p><strong>Status:</strong> <StatusBadge status={selectedScan.status} /></p>
//               </div>
//               <div>
//                 <p><strong>Progress:</strong> {selectedScan.progress}%</p>
//                 <p><strong>Created:</strong> {new Date(selectedScan.created_at).toLocaleString()}</p>
//                 <p><strong>Finished:</strong> {selectedScan.finished_at ? new Date(selectedScan.finished_at).toLocaleString() : "-"}</p>
//               </div>
//             </div>

//             {/* NEW Scan Results Component */}
//             <h4 className="mt-4 mb-2 font-semibold">Scan Results</h4>
//             <WebScanResultsList results={selectedScanResults} />
//             {/* End of NEW Scan Results Component */}

//             <h4 className="mt-4 mb-2 font-semibold">Raw Data</h4>
//             <pre className="bg-gray-800 p-3 rounded text-xs overflow-x-auto max-h-64">
//               {JSON.stringify(selectedScan, null, 2)}
//             </pre>
//           </div>
//         </div>
//       )}
//     </div>
//   );
// };

// export default ScanResults;

// // --- ScanRow Component (Unchanged) ---
// const ScanRow: React.FC<{
//   scan: ScanJob;
//   retryScan: (scan: ScanJob) => void;
//   highlight?: boolean;
//   onSelect?: () => void;
// }> = ({ scan, retryScan, highlight, onSelect }) => {
//   return (
//     <tr
//       onClick={onSelect}
//       className={`border-b cursor-pointer transition-colors duration-500 ${
//         highlight ? "bg-green-900" : "hover:bg-gray-800"
//       }`}
//     >
//       <td className="px-4 py-2">
//         <span>{scan.target}</span>
//       </td>

//       <td className="px-4 py-2">{scan.profile}</td>
//       <td className="px-4 py-2">
//         <StatusBadge status={scan.status} />
//       </td>
//       <td className="px-4 py-2">
//         {scan.status === "running" && (
//           <div className="flex items-center gap-2">
//             <div className="w-16 bg-gray-700 rounded-full h-2">
//               <div
//                 className="bg-blue-500 h-2 rounded-full transition-all duration-300"
//                 style={{ width: `${scan.progress}%` }}
//               />
//             </div>
//             <span className="text-xs text-blue-400">{scan.progress}%</span>
//           </div>
//         )}
//         {scan.status !== "running" && "-"}
//       </td>
//       <td className="px-4 py-2">{new Date(scan.created_at).toLocaleString()}</td>
//       <td className="px-4 py-2">
//         {scan.finished_at ? new Date(scan.finished_at).toLocaleString() : "-"}
//       </td>
//       <td className="px-4 py-2">
//         <button
//           onClick={(e) => {
//             e.stopPropagation();
//             retryScan(scan);
//           }}
//           className="text-blue-400 hover:text-blue-600 flex items-center gap-1 transition-colors"
//           disabled={scan.status === "running"}
//         >
//           <RotateCcw size={14} /> Retry
//         </button>
//       </td>
//     </tr>
//   );
// };

// // --- NEW WebScanResultsList Component ---
// const WebScanResultsList: React.FC<{ results: WebScanResult[] }> = ({ results }) => {
//   if (!results.length) {
//     return (
//       <div className="bg-gray-800 rounded p-3 text-gray-400 text-center">
//         No scan results available.
//       </div>
//     );
//   }

//   return (
//     <div className="grid grid-cols-1 gap-4 max-h-96 overflow-y-auto pr-2">
//       {results.map((result) => (
//         <div
//           key={result.id}
//           className="bg-gray-800 border border-gray-700 rounded-lg p-4 shadow-md"
//         >
//           <h3 className="text-lg font-semibold text-blue-400">{result.url}</h3>
//           <p className="text-sm text-gray-400 mb-2">
//             Status:{" "}
//             <span
//               className={`${
//                 result.status === "completed"
//                   ? "text-green-400"
//                   : result.status === "in-progress"
//                   ? "text-yellow-400"
//                   : "text-red-400"
//               }`}
//             >
//               {result.status}
//             </span>
//           </p>

//           {/* Headers */}
//           <div className="mt-3">
//             <h4 className="text-md font-semibold text-gray-300 mb-1">Headers</h4>
//             <ul className="text-sm text-gray-400 list-disc ml-6 max-h-24 overflow-y-auto">
//               {Object.entries(result.headers || {}).map(([key, value]) => (
//                 <li key={key}>
//                   <strong>{key}:</strong> {value}
//                 </li>
//               ))}
//             </ul>
//           </div>

//           {/* Cookies */}
//           <div className="mt-3">
//             <h4 className="text-md font-semibold text-gray-300 mb-1">Cookies</h4>
//             <ul className="text-sm text-gray-400 list-disc ml-6 max-h-24 overflow-y-auto">
//               {Object.entries(result.cookies || {}).map(([key, value]) => (
//                 <li key={key}>
//                   <strong>{key}:</strong> {value}
//                 </li>
//               ))}
//             </ul>
//           </div>

//           {/* Issues */}
//           <div className="mt-3">
//             <h4 className="text-md font-semibold text-gray-300 mb-1">Detected Issues</h4>
//             {result.issues && result.issues.length > 0 ? (
//               <ul className="text-sm text-red-400 list-disc ml-6 max-h-24 overflow-y-auto">
//                 {result.issues.map((issue, index) => (
//                   <li key={index}>{issue}</li>
//                 ))}
//               </ul>
//             ) : (
//               <p className="text-sm text-green-400">No issues detected ✅</p>
//             )}
//           </div>

//           <p className="text-xs text-gray-500 mt-4">
//             Scanned on: {new Date(result.timestamp).toLocaleString()}
//           </p>
//         </div>
//       ))}
//     </div>
//   );
// };