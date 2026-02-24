"use client";
import { useState, useEffect, useRef } from "react";
import { io } from "socket.io-client";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2, Shield, Globe, Bug, ScrollText } from "lucide-react";
import { motion } from "framer-motion";

export default function WebSecurityScan() {
  const [url, setUrl] = useState("");
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(false);
  const [socket, setSocket] = useState(null);
  const bottomRef = useRef(null);

  // Initialize socket connection
  useEffect(() => {
    const newSocket = io("http://localhost:5000");
    setSocket(newSocket);

    newSocket.on("scan_update", (data) => {
      console.log("Web scan update:", data);
      if (data.job_id) {
        setScans((prev) => {
          const existingIndex = prev.findIndex((s) => s.job_id === data.job_id);
          if (existingIndex >= 0) {
            // Update existing scan
            const updated = [...prev];
            updated[existingIndex] = { 
              ...updated[existingIndex], 
              ...data,
              // Ensure URL is preserved when updating
              url: updated[existingIndex].url || data.target || url
            };
            return updated;
          }
          // Add new scan if not found
          return [...prev, { 
            job_id: data.job_id, 
            url: data.target || url,
            status: data.status || "queued", 
            progress: data.progress || 0,
            created_at: data.created_at || new Date().toISOString()
          }];
        });
      }
    });

    newSocket.on("scan_log", (log) => {
      console.log("Web scan log:", log);
    });

    return () => newSocket.disconnect();
  }, []);

  // Auto-scroll to newest scan
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [scans]);

  const startScan = async () => {
    if (!url) return alert("Enter a valid URL first!");
    
    // Basic URL validation
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      return alert("Please enter a valid URL starting with http:// or https://");
    }

    setLoading(true);
    try {
      const res = await fetch("http://localhost:5000/api/web-scans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, profile: "web" }),
      });
      
      const data = await res.json();
      
      if (res.ok) {
        // Don't add to scans here - wait for socket update
        // The socket will add it when it receives the scan_update event
        setUrl(""); // Clear input after successful submission
      } else {
        alert(data.error || "Failed to start scan.");
      }
    } catch (err) {
      console.error("Scan start error:", err);
      alert("Failed to connect to server. Please check if the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const fetchResults = async (jobId) => {
    try {
      const res = await fetch(`http://localhost:5000/api/scans/scan-jobs/${jobId}/results`);
      const data = await res.json();
      
      if (res.ok) {
        setScans((prev) =>
          prev.map((scan) =>
            scan.job_id === jobId ? { ...scan, results: data } : scan
          )
        );
      } else {
        console.error("Failed to fetch results:", data.error);
      }
    } catch (err) {
      console.error("Error fetching results:", err);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "finished": return "text-green-400";
      case "running": return "text-yellow-400";
      case "failed": return "text-red-400";
      case "queued": return "text-blue-400";
      default: return "text-gray-400";
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "finished": return "✅";
      case "running": return "🔄";
      case "failed": return "❌";
      case "queued": return "⏳";
      default: return "❓";
    }
  };

  // Generate unique key for each scan
  const getScanKey = (scan) => {
    return `${scan.job_id}-${scan.created_at || scan.url}`;
  };

  return (
    <div className="p-6 space-y-6 overflow-auto max-h-screen">
      <div className="flex items-center space-x-3">
        <Globe className="text-sky-400" size={28} />
        <h1 className="text-2xl font-semibold">Web Application Security Scanner</h1>
      </div>

      <div className="flex items-center gap-3">
        <Input
          placeholder="Enter target URL (e.g. https://example.com)"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && startScan()}
          className="flex-1"
        />
        <Button onClick={startScan} disabled={loading || !url}>
          {loading ? (
            <>
              <Loader2 className="animate-spin mr-2" size={16} /> Scanning...
            </>
          ) : (
            <>
              <Shield className="mr-2" size={16} /> Start Scan
            </>
          )}
        </Button>
      </div>

      <div className="space-y-4 overflow-y-auto max-h-[70vh] p-2 border border-gray-700 rounded-md bg-gray-900/50">
        {scans.length === 0 ? (
          <p className="text-gray-400 text-center py-8">
            No scans yet. Start one above to see results here.
          </p>
        ) : (
          scans.map((scan, idx) => (
            <motion.div
              key={getScanKey(scan)} // Use unique key function
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <Card className="bg-zinc-900/50 border-zinc-700 hover:border-sky-500 transition-colors">
                <CardContent className="p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-lg">{getStatusIcon(scan.status)}</span>
                        <p className="text-sky-300 font-medium break-all">{scan.url}</p>
                      </div>
                      <div className="text-xs text-gray-400 space-y-1">
                        <p>
                          Status:{" "}
                          <span className={getStatusColor(scan.status)}>
                            {scan.status}
                          </span>
                        </p>
                        <p>Progress: {scan.progress ?? 0}%</p>
                        <p>Started: {new Date(scan.created_at).toLocaleString()}</p>
                        {scan.job_id && (
                          <p className="text-xs text-gray-500">ID: {scan.job_id.slice(0, 8)}...</p>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex flex-col gap-2">
                      {scan.status === "finished" && scan.results && scan.results.length > 0 && (
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => {
                            // Toggle results display
                            setScans(prev =>
                              prev.map(s =>
                                s.job_id === scan.job_id 
                                  ? { ...s, showResults: !s.showResults }
                                  : s
                              )
                            );
                          }}
                        >
                          <ScrollText className="mr-1" size={14} /> 
                          {scan.showResults ? "Hide" : "View"} Results
                        </Button>
                      )}
                      {scan.status === "finished" && (!scan.results || scan.results.length === 0) && (
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => fetchResults(scan.job_id)}
                        >
                          <ScrollText className="mr-1" size={14} /> Load Results
                        </Button>
                      )}
                    </div>
                  </div>

                  {/* Progress bar for running scans */}
                  {scan.status === "running" && (
                    <div className="w-full bg-gray-700 rounded-full h-2 mb-3">
                      <div 
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${scan.progress}%` }}
                      />
                    </div>
                  )}

                  {/* Results display */}
                  {scan.showResults && scan.results && scan.results.length > 0 && (
                    <div className="mt-3 p-3 bg-gray-800 rounded-md border border-gray-700">
                      <h4 className="font-semibold text-sky-400 mb-2 flex items-center gap-2">
                        <Bug size={16} />
                        Scan Results ({scan.results.length} found)
                      </h4>
                      
                      <div className="space-y-3 text-sm">
                        {scan.results.map((result, resultIdx) => (
                          <div key={`${scan.job_id}-result-${resultIdx}`} className="border-l-2 border-green-500 pl-3">
                            <div className="grid grid-cols-2 gap-2 text-xs">
                              <div><strong>Target:</strong> {result.target}</div>
                              <div><strong>Port:</strong> {result.port || 'N/A'}</div>
                              <div><strong>Service:</strong> {result.service || 'N/A'}</div>
                              <div><strong>Version:</strong> {result.version || 'N/A'}</div>
                              <div><strong>Protocol:</strong> {result.protocol || 'N/A'}</div>
                              <div><strong>Discovered:</strong> {new Date(result.discovered_at).toLocaleString()}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Web-specific results would go here when available */}
                  {scan.showResults && scan.web_results && (
                    <div className="mt-3 p-3 bg-gray-800 rounded-md border border-gray-700">
                      <h4 className="font-semibold text-sky-400 mb-2">Web Security Findings</h4>
                      {/* Web scan results display would be implemented here */}
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          ))
        )}
        <div ref={bottomRef}></div>
      </div>
    </div>
  );
}