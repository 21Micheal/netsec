import React, { useState } from "react";
import axios from "axios";

export default function WebScanForm({ onCreated }: { onCreated?: () => void }) {
  const [url, setUrl] = useState("");
  const [profile, setProfile] = useState("default");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post("http://localhost:5000/api/webscans", { url, profile });
      setUrl("");
      if (onCreated) onCreated();
    } catch (err) {
      console.error(err);
      alert("Failed to create web scan");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={submit} className="flex gap-2 items-center">
      <input
        className="px-3 py-2 rounded text-black flex-1"
        placeholder="https://example.com"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        required
      />
      <select value={profile} onChange={(e) => setProfile(e.target.value)} className="px-3 py-2 rounded text-black">
        <option value="default">Default</option>
        <option value="fast">Fast (header only)</option>
        <option value="full">Full (header + fuzzing) — later</option>
      </select>
      <button type="submit" disabled={loading} className="btn btn-primary">
        {loading ? "Scanning…" : "Run Web Scan"}
      </button>
    </form>
  );
}
