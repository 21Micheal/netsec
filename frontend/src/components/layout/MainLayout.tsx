import React from "react";
import Sidebar from "./sidebar";
import Header from "./Header";

interface MainLayoutProps {
  title?: string;
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ title, children }) => {
  return (
    <div className="flex h-screen bg-gray-950 text-gray-100">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Header */}
        <Header title={title} />

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6 bg-gray-900 rounded-tl-2xl">
          {children}
        </main>
      </div>
    </div>
  );
};

export default MainLayout;
