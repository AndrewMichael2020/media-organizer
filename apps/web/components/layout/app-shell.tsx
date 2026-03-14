import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[hsl(var(--background))]">
      <Sidebar />
      <main className="flex min-w-0 flex-1 flex-col overflow-auto">
        <Topbar />
        <div className="min-w-0 flex-1">
          {children}
        </div>
      </main>
    </div>
  );
}
