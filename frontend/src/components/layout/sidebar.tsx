import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  FileSearch,
  Settings,
  AlertTriangle,
} from "lucide-react";

const Sidebar: React.FC = () => {
  const navItems = [
    { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { path: "/risks", label: "Risk Dashboard", icon: AlertTriangle },
    { path: "/vulnerabilities", label: "Vulnerabilities", icon: FileSearch },
    { path: "/settings", label: "Settings", icon: Settings },
  ];

  return (
    <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
      <div className="flex items-center justify-center h-16 border-b border-gray-800">
        <span className="text-xl font-semibold text-blue-400">
          ⚡ NetSec
        </span>
      </div>

      <nav className="flex-1 overflow-y-auto p-4">
        <ul className="space-y-2">
          {navItems.map(({ path, label, icon: Icon }) => (
            <li key={path}>
              <NavLink
                to={path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? "bg-blue-600 text-white"
                      : "text-gray-300 hover:bg-gray-800 hover:text-white"
                  }`
                }
              >
                <Icon className="w-5 h-5" />
                <span>{label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
};

export default Sidebar;
