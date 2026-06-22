import { Link, Outlet } from "@tanstack/react-router";
import { FileSpreadsheet, FileText, LayoutDashboard, ListChecks, Settings, Table2, Upload } from "lucide-react";
import { SessionSwitcher } from "@/components/SessionSwitcher";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/upload", label: "Upload", icon: Upload },
  { to: "/jobs", label: "Jobs", icon: ListChecks },
  { to: "/results", label: "Results", icon: Table2 },
  { to: "/document", label: "Document", icon: FileSpreadsheet },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Layout() {
  return (
    <div className="min-h-screen bg-surface">
      {/* Sticky header (Coral Stay nav, 80px, Level 1 shadow) */}
      <header className="sticky top-0 z-10 flex h-20 items-center border-b border-border bg-white px-6 shadow-lvl1">
        <Link to="/" className="flex items-center gap-2">
          <FileText className="text-primary" size={24} />
          <span className="font-display text-[22px] font-extrabold text-text-primary">DocOCR</span>
        </Link>
        <nav className="ml-10 flex gap-1">
          {nav.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className="flex items-center gap-2 rounded px-3 py-2 font-body text-sm font-medium text-text-secondary transition-colors hover:bg-surface [&.active]:bg-surface [&.active]:text-text-primary"
              activeOptions={{ exact: to === "/" }}
            >
              <Icon size={16} />
              {label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto">
          <SessionSwitcher />
        </div>
      </header>
      <main className="mx-auto max-w-container px-6 py-8 md:px-10">
        <Outlet />
      </main>
    </div>
  );
}
