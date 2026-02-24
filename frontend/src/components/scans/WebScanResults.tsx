import React, { useEffect, useState } from "react";
import axios from "axios";

type WebScan = {
  job: { id: string; status: string };
  url?: string;
  http_status?: number;
  headers?: Record<string, string>;
  cookies?: any[];
  issues?: any[];
  created_at?: string;
};

export default function WebScanResults({ jobId }: { jobId: string }) {
  const [data, setData] = useState<WebScan | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchResults = async () => {
    try {
      const res = await axios.get(`http://localhost:5000/api/webscans/${jobId}/results`);
      setData(res.data);
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
        <p>Status: {data.job?.status}</p>
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
        {data.cookies && data.cookies.length > 0 ? (
          <ul>
            {data.cookies.map((c, idx) => (
              <li key={idx} className="mb-2">
                <div className="font-mono">{c.name} = {c.value}</div>
                <div className="text-sm text-gray-400">attrs: {JSON.stringify(c.attributes)}</div>
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
              <li key={i}><strong>{it.id}</strong> — {it.detail} ({it.severity})</li>
            ))}
          </ul>
        ) : <div>No issues found</div>}
      </div>
    </div>
  );
}
