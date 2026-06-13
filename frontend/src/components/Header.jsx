import React from 'react';
import { Bell, User, Settings, Search } from "lucide-react";

const Header = ({ titulo, subtitulo }) => {
  return (
    <header className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between shadow-sm">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{titulo}</h1>
        {subtitulo && <p className="text-sm text-slate-500">{subtitulo}</p>}
      </div>

      <div className="flex items-center gap-4">
        <button className="p-2 text-slate-400 hover:text-slate-600 transition">
          <Search size={20} />
        </button>
        <button className="p-2 text-slate-400 hover:text-slate-600 transition">
          <Bell size={20} />
        </button>
        <div className="h-8 w-8 bg-indigo-600 rounded-full flex items-center justify-center text-white font-bold">
          AD
        </div>
      </div>
    </header>
  );
};

export default Header;