import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import MainLayout from "./components/layout/MainLayout";
import Dashboard from "./pages/Dashboard";
import RiskDashboard from "./components/dashboard/RiskDashboard";
import VulnerabilityDashboard from "./components/vulnerability/VulnerabilityDashboard";
import Settings from "./pages/Settings";
import Login from "./pages/Login";
import ProtectedRoute from "./components/auth/ProtectedRoute";

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <MainLayout title="Dashboard">
              <Dashboard />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/risks"
        element={
          <ProtectedRoute>
            <MainLayout title="Risk Dashboard">
              <RiskDashboard assets={[]} vulnerabilities={[]} recentScans={[]} />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/vulnerabilities"
        element={
          <ProtectedRoute>
            <MainLayout title="Vulnerability Assessment">
              <VulnerabilityDashboard />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <MainLayout title="Settings">
              <Settings />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
};

export default App;
