import React from "react";
import WebSecurityScan from "@/components/WebSecurityScan";
import ScanAnalytics from "./ScanAnalytics";

const WebScanPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <WebSecurityScan />
      <ScanAnalytics />
    </div>
  );
};

export default WebScanPage;