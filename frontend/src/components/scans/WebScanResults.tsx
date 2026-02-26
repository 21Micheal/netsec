import React, { useEffect, useState } from "react";
import axios from "axios";
import { API_BASE_URL } from "../../config/runtime";

type WebScan = {
  job_id: string;
  url?: string;
  http_status?: number;
  headers?: Record<string, string>;
  cookies?: Record<string, string>;
  issues?: any[];
  created_at?: string;
};

export default function WebScanResults({ jobId }: { jobId: string }) {
  const [data, setData] = useState<WebScan | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchResults = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/web-scans/results/${jobId}`);
      const rows = Array.isArray(res.data) ? res.data : [];
      setData(rows.length ? rows[0] : null);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();
    const interval = setInterval(fetchResults, 3000);
    return () => clearInterval(interval);
  }, [jobId]);

  if (loading) return <div>Loading...</div>;
  if (!data) return <div>No data</div>;

  return (
    <div className="space-y-4">
      <div className="card p-4 bg-base-200">
        <h3 className="font-bold">Web Scan: {data.url || "—"}</h3>
        <p>Job ID: {data.job_id}</p>
        <p>HTTP status: {data.http_status || "—"}</p>
        <p>Scanned at: {data.created_at || "—"}</p>
      </div>

      <div className="card p-4 bg-base-200">
        <h4 className="font-semibold mb-2">Security Headers</h4>
        <table className="table-auto w-full">
          <thead><tr><th>Header</th><th>Value</th></tr></thead>
          <tbody>
            {data.headers ? Object.entries(data.headers).map(([k,v]) => (
              <tr key={k}><td className="font-mono">{k}</td><td>{String(v)}</td></tr>
            )) : <tr><td colSpan={2}>No headers</td></tr>}
          </tbody>
        </table>
      </div>

      <div className="card p-4 bg-base-200">
        <h4 className="font-semibold mb-2">Cookies</h4>
        {data.cookies && Object.keys(data.cookies).length > 0 ? (
          <ul>
            {Object.entries(data.cookies).map(([key, value], idx) => (
              <li key={idx} className="mb-2">
                <div className="font-mono">{key} = {String(value)}</div>
              </li>
            ))}
          </ul>
        ) : <div>No cookies</div>}
      </div>

      <div className="card p-4 bg-base-200">
        <h4 className="font-semibold mb-2">Detected Issues</h4>
        {data.issues && data.issues.length > 0 ? (
          <ul className="list-disc pl-5">
            {data.issues.map((it, i) => (
              <li key={i}><strong>{it.type || "issue"}</strong> — {it.message || it.detail} ({it.severity || "info"})</li>
            ))}
          </ul>
        ) : <div>No issues found</div>}
      </div>
    </div>
  );
}
