import React from "react";
import { Bell } from "lucide-react";

interface HeaderProps {
  title?: string;
}

const Header: React.FC<HeaderProps> = ({ title }) => {
  return (
    <header className="flex items-center justify-between h-16 px-6 border-b border-gray-800 bg-gray-950">
      <h1 className="text-lg font-semibold text-gray-200">
        {title || "Dashboard"}
      </h1>
      <div className="flex items-center gap-4">
        <button className="relative text-gray-300 hover:text-blue-400">
          <Bell className="w-5 h-5" />
          <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>
        <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center text-sm font-semibold">
          MJ
        </div>
      </div>
    </header>
  );
};

export default Header;
