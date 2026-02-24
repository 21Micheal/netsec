import React, { useEffect, useState, useCallback } from "react";
import { useSocket } from "../hooks/useSocket";

interface ScanJob {
  id: string;
  target: string;
  profile: string;
  status: string;
  progress: number;
  createdAt: string;
  finishedAt?: string;
}

const ScanPage: React.FC = () => {
  const [scans, setScans] = useState<ScanJob[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch initial scans
  const fetchScans = useCallback(async () => {
    try {
      const res = await fetch("http://localhost:5000/api/scans/scans");
      const data = await res.json();
      setScans(data);
    } catch (err) {
      console.error("Failed to fetch scans:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchScans();
  }, [fetchScans]);

  // Socket listener
  useSocket((update) => {
    setScans((prev) => {
      const existing = prev.find((s) => s.id === update.job_id);
      if (existing) {
        // Update existing scan
        return prev.map((s) =>
          s.id === update.job_id
            ? { ...s, ...update, id: update.job_id, createdAt: s.createdAt || new Date().toISOString() }
            : s
        );
      } else {
        // Add new scan
        return [
          { ...update, id: update.job_id, createdAt: new Date().toISOString() },
          ...prev,
        ];
      }
    });
  });

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-2xl font-bold mb-4">🧠 Active & Recent Scans</h1>

      {loading ? (
        <p>Loading scans...</p>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {scans.map((scan) => (
            <div
              key={scan.id}
              className="bg-gray-800 text-white p-4 rounded-lg shadow-md border border-gray-700"
            >
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="font-semibold">{scan.target}</h2>
                  <p className="text-sm text-gray-400">
                    Profile: {scan.profile} | Status:{" "}
                    <span
                      className={`${
                        scan.status === "running"
                          ? "text-yellow-400"
                          : scan.status === "finished"
                          ? "text-green-400"
                          : scan.status === "failed"
                          ? "text-red-400"
                          : "text-gray-400"
                      }`}
                    >
                      {scan.status}
                    </span>
                  </p>
                </div>
                <p className="text-sm">{scan.progress}%</p>
              </div>

              <div className="w-full bg-gray-700 h-2 mt-2 rounded-full">
                <div
                  className="bg-green-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${scan.progress || 0}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ScanPage;





// import React, { useState, useEffect } from "react";
// import ScanResults from "../components/ScanResults";
// // 💡 Import the Socket.IO client library
// import { io, Socket } from "socket.io-client";

// // 💡 Define the Socket.IO connection URL
// const SOCKET_IO_URL = "http://127.0.0.1:5000";

// // 💡 Initialize the Socket.IO connection outside of the component or useEffect
// // to ensure it's a stable connection across renders.
// // We'll manage connection/disconnection inside useEffect based on 'jobId'.
// let socket: Socket | null = null;

// const ScanPage: React.FC = () => {
//   // Replace this with the job ID returned from backend after starting a scan
//   const [jobId, setJobId] = useState<string>("150edb27-134d-4d4e-bbb8-c4e2e214d7e7");
//   const [status, setStatus] = useState<string>("waiting");
//   const [progress, setProgress] = useState<number>(0);
//   const [result, setResult] = useState<any>(null);
//   const [error, setError] = useState<string | null>(null);

//   useEffect(() => {
//     if (!jobId) return;

//     // 1. Establish the connection if it doesn't exist or is disconnected
//     if (!socket || !socket.connected) {
//         socket = io(SOCKET_IO_URL);

//         // Optional: Add connection status listeners for better UX/debugging
//         socket.on("connect", () => {
//             console.log(`Connected to Socket.IO: ${SOCKET_IO_URL}`);
//             setStatus("connected");
//             setError(null);
//             // After connecting, subscribe to the job updates
//             socket?.emit("subscribe", { job_id: jobId });
//         });

//         socket.on("disconnect", () => {
//             console.warn("Socket.IO connection closed");
//             setStatus("disconnected");
//         });

//         socket.on("connect_error", (err) => {
//             console.error("Socket.IO connection error:", err);
//             setError(`Socket.IO connection error: ${err.message}`);
//             setStatus("error");
//         });

//     } else {
//         // If already connected, just resubscribe in case jobId changed
//         socket.emit("subscribe", { job_id: jobId });
//     }

//     // 2. Set up the event listener for job updates
//     const handleJobUpdate = (data: any) => {
//       console.log("Received job_update:", data);
//       // Data is typically already parsed JSON in Socket.IO
//       if (data.status) setStatus(data.status);
//       if (data.progress !== undefined) setProgress(data.progress);
//       if (data.result) setResult(data.result);
//       if (data.error) setError(data.error); // Handle server-side errors
//     };

//     socket.on("job_update", handleJobUpdate);

//     // 3. Cleanup function: unsubscribe and disconnect
//     return () => {
//       if (socket) {
//         // Stop listening for updates
//         socket.off("job_update", handleJobUpdate);
        
//         // Optional: Send an 'unsubscribe' event to the server if needed
//         // socket.emit("unsubscribe", { job_id: jobId }); 

//         // Disconnect only if this is the last reference or component unmounts fully
//         // For simplicity and to match the original cleanup logic, we disconnect here.
//         socket.disconnect();
//         socket = null; // Clear the reference
//         console.log("Cleaned up Socket.IO listeners and disconnected.");
//       }
//     };
//   }, [jobId]); // Re-run effect when jobId changes

//   return (
//     <div className="container mx-auto py-8 px-4">
//       <h2 className="text-2xl font-semibold mb-4 text-indigo-400">Web Scan Progress</h2>

//       <div className="bg-gray-900 rounded-xl p-6 shadow-lg border border-gray-800">
//         <p className="mb-2 text-gray-400">
//           <span className="font-semibold text-gray-300">Job ID:</span> {jobId}
//         </p>
//         <p className="mb-2 text-gray-400">
//           <span className="font-semibold text-gray-300">Status:</span>{" "}
//           <span className="text-indigo-300">{status}</span>
//         </p>
//         <p className="mb-2 text-gray-400">
//           <span className="font-semibold text-gray-300">Progress:</span> {progress}%
//         </p>

//         {error && <p className="text-red-500 mt-3">⚠️ {error}</p>}

//         {result ? (
//           <ScanResults data={result} />
//         ) : (
//           <div className="mt-4 text-gray-500 italic">Waiting for scan results...</div>
//         )}
//       </div>
//     </div>
//   );
// };

// export default ScanPage;