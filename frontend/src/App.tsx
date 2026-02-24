import React from "react";
import {  Routes, Route } from "react-router-dom";
import MainLayout from "./components/layout/MainLayout";
import Dashboard from "./pages/Dashboard";
import RiskDashboard from "./components/dashboard/RiskDashboard";
// import ScanInsights from "./components/dashboard/ScanInsights";
import VulnerabilityDashboard from "./components/vulnerability/VulnerabilityDashboard";
import Jobs from "./pages/Jobs";
import Alerts from "./pages/Alerts";
import Settings from "./pages/Settings";

const App: React.FC = () => {
  return (
    // <Router>
      <Routes>
        <Route
          path="/"
          element={
            <MainLayout title="Dashboard">
              <Dashboard />
            </MainLayout>
          }
        />
        <Route
          path="/risks"
          element={
            <MainLayout title="Risk Dashboard">
              <RiskDashboard assets={[]} vulnerabilities={[]} recentScans={[]} />
            </MainLayout>
          }
        />
        <Route
          path="/vulnerabilities"
          element={
            <MainLayout title="Vulnerability Assessment">
              <VulnerabilityDashboard />
            </MainLayout>
          }
        />
        <Route
          path="/alerts"
          element={
            <MainLayout title="Alerts">
              <Alerts />
            </MainLayout>
          }
        />
        <Route
          path="/settings"
          element={
            <MainLayout title="Settings">
              <Settings />
            </MainLayout>
          }
        />
      </Routes>
    // </Router>
  );
};

export default App;
