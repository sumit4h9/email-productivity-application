"use client";
import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import Logo from "../../components/ui/Logo";

export default function DashboardPage() {
  const [theme, setTheme] = useState<"default" | "dark" | "sunset" | "oceanic">(
    "default"
  );
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  useEffect(() => {
    console.log("Adding event listener");
    console.log("profileRef.current", profileRef.current);
    const handleClickOutside = (event: MouseEvent) => {
      console.log("Click outside handler called", event.target);
      console.log("profileRef.current", profileRef.current);
      if (profileRef.current) {
        console.log(
          "Contains check",
          profileRef.current.contains(event.target as Node)
        );
        if (!profileRef.current.contains(event.target as Node)) {
          console.log("Setting profileOpen to false");
          setProfileOpen(false);
        }
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <div
      data-theme={theme}
      className="flex h-screen bg-[var(--bg-primary)] text-[var(--text-primary)]"
    >
      {/* Sidebar */}
      <aside className="w-64 flex flex-col border-r border-[var(--border-primary)]">
        <div className="px-6 py-5 flex items-center gap-2">
          <div className="w-7 h-7 flex items-center bg-transparent">
            <Logo className="w-full h-full" />
          </div>
          <h1 className="text-xl font-bold leading-none">Axnore</h1>
        </div>
        <nav className="flex-1 px-4 py-4 space-y-2 overflow-y-auto">
          <button className="w-full flex items-center justify-center px-4 py-3 text-sm font-medium text-[var(--accent-text)] bg-[var(--accent-primary)] rounded-lg hover:bg-[var(--accent-primary-hover)] shadow-lg transition-all duration-75">
            <span className="mr-2">✏️</span>
            Compose Email
          </button>
          <p className="px-4 pt-4 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">
            Inbox
          </p>
          <a
            className="flex items-center justify-between px-4 py-2 text-sm font-medium bg-[var(--accent-primary)] text-white rounded-lg"
            href="#"
          >
            <div className="flex items-center">
              <span className="mr-3">📧</span>
              <span>Your Emails</span>
            </div>
            <span className="text-xs font-bold bg-[var(--accent-primary-hover)] rounded-full px-2 py-0.5">
              47
            </span>
          </a>
          <a
            className="flex items-center justify-between px-4 py-2 text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors duration-75"
            href="#"
          >
            <div className="flex items-center">
              <span className="mr-3">📤</span>
              <span>Sent</span>
            </div>
            <span></span>
          </a>
          <a
            className="flex items-center justify-between px-4 py-2 text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors duration-75"
            href="#"
          >
            <div className="flex items-center">
              <span className="mr-3">📁</span>
              <span>Archive</span>
            </div>
            <span></span>
          </a>
          <a
            className="flex items-center justify-between px-4 py-2 text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors duration-75"
            href="#"
          >
            <div className="flex items-center">
              <span className="mr-3">🗑️</span>
              <span>Deleted</span>
            </div>
            <span></span>
          </a>
          <p className="px-4 pt-6 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">
            AI Insights
          </p>
          <a
            className="flex items-center justify-between px-4 py-2 text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors duration-75"
            href="#"
          >
            <div className="flex items-center">
              <span className="mr-3">🏥</span>
              <span>Email Health Score</span>
            </div>
            <span className="text-xs font-bold text-[var(--success-text)] bg-[var(--success-bg)] rounded-full px-2 py-0.5">
              84
            </span>
          </a>
          <a
            className="flex items-center justify-between px-4 py-2 text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors duration-75"
            href="#"
          >
            <div className="flex items-center">
              <span className="mr-3">📢</span>
              <span>Updates</span>
            </div>
            <span></span>
          </a>
        </nav>
        <div className="px-4 py-4 mt-auto border-t border-[var(--border-primary)]">
          <Link
            to="/"
            className="flex items-center px-4 py-2 text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors duration-75"
          >
            <span className="mr-3">🏠</span>
            Back to Home
          </Link>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="flex items-center justify-between p-6 border-b border-[var(--border-primary)] bg-[var(--bg-primary)]">
          <div>
            <h2 className="text-2xl font-bold">Axnore Dashboard</h2>
            <p className="text-sm text-[var(--text-tertiary)]">
              AI-powered email management and security
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <select
              value={theme}
              onChange={e =>
                setTheme(
                  e.target.value as "default" | "dark" | "sunset" | "oceanic"
                )
              }
              className="px-3 py-2 text-sm border border-[var(--border-secondary)] rounded-lg bg-[var(--bg-primary)] text-[var(--text-primary)]"
            >
              <option value="default">Default</option>
              <option value="dark">Dark</option>
              <option value="sunset">Sunset</option>
              <option value="oceanic">Oceanic</option>
            </select>
            <button className="flex items-center px-4 py-2 text-sm font-medium text-[var(--text-secondary)] border border-[var(--border-secondary)] rounded-lg hover:bg-[var(--bg-tertiary)] transition-colors duration-75">
              <span className="mr-2">🔄</span>
              Refresh
            </button>
            <span className="text-sm text-[var(--text-tertiary)]">
              Last synced: 2 min ago
            </span>
            <button className="p-2 rounded-full hover:bg-[var(--bg-tertiary)] transition-colors duration-75">
              <span className="text-[var(--text-secondary)]">🔔</span>
            </button>

            {/* Profile dropdown */}
            <div className="relative" ref={profileRef}>
              <button
                onClick={e => {
                  e.stopPropagation();
                  setProfileOpen(!profileOpen);
                }}
                className="flex items-center space-x-2"
              >
                <div className="w-10 h-10 bg-[var(--accent-primary)] rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-bold">JM</span>
                </div>
              </button>
              {profileOpen && (
                <div
                  className="absolute right-0 mt-2 w-64 bg-[var(--bg-primary)] rounded-lg shadow-xl p-2 border border-[var(--border-primary)]"
                  onClick={e => e.stopPropagation()}
                >
                  <div className="px-2 py-3">
                    <p className="text-sm font-semibold">Jessica Miller</p>
                    <p className="text-xs text-[var(--text-tertiary)]">
                      jessica.miller@axnore.com
                    </p>
                  </div>
                  <div className="border-t border-[var(--border-primary)] my-1"></div>
                  <a
                    href="#"
                    className="flex items-center px-2 py-2 text-sm hover:bg-[var(--bg-tertiary)] rounded-md transition-colors duration-75"
                  >
                    <span className="mr-3">👤</span> Profile
                  </a>
                  <Link
                    to="/"
                    className="flex items-center px-2 py-2 text-sm hover:bg-[var(--bg-tertiary)] rounded-md transition-colors duration-75"
                  >
                    <span className="mr-3">🚪</span> Logout
                  </Link>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Emails Section */}
          <div className="flex-1 p-4 overflow-y-auto bg-[var(--bg-secondary)]">
            {/* Search and Quick Actions */}
            <div className="mb-8">
              <div className="relative flex-1">
                <input
                  type="text"
                  placeholder="Search emails..."
                  className="w-full pl-10 pr-4 py-2 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-[var(--accent-primary)]"
                />
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg
                    className="h-5 w-5 text-[var(--text-tertiary)]"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                </div>
              </div>
              <div className="flex items-center mt-3 space-x-3 text-sm">
                <span className="text-[var(--text-secondary)]">
                  Quick Actions:
                </span>
                <button className="text-[var(--text-primary)] hover:text-[var(--accent-primary)] transition-colors">
                  <span className="mr-1">🧹</span>Clean Promotions
                </button>
                <button className="text-[var(--text-secondary)] bg-[var(--warning-bg)] text-[var(--warning-text)] px-2 py-1 rounded-md hover:bg-[var(--warning-bg-hover)] transition-colors">
                  <span className="mr-1">⚠️</span>Review Flagged
                </button>
                <button className="text-[var(--text-secondary)] bg-[var(--success-bg)] text-[var(--success-text)] px-2 py-1 rounded-md hover:bg-[var(--success-bg-hover)] transition-colors">
                  <span className="mr-1">✓</span>Mark All Read
                </button>
              </div>
            </div>

            <div className="mt-6"></div>
            {/* Example Email */}
            <div className="p-3 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg shadow-sm mb-2 hover:shadow-md transition duration-75">
              <p className="font-medium text-sm mb-1">
                Q4 Marketing Strategy Review
              </p>
              <p className="text-xs text-[var(--text-secondary)]">
                Hi team, I need your input on the Q4 strategy by Friday.
              </p>
            </div>
            <div className="p-3 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg shadow-sm mb-2 hover:shadow-md transition duration-75">
              <p className="font-medium text-sm mb-1">
                Critical Security Alert
              </p>
              <p className="text-xs text-[var(--text-secondary)]">
                Immediate action required: vulnerability detected.
              </p>
            </div>
          </div>

          {/* AI Assistant */}
          <aside className="w-[320px] bg-[var(--bg-secondary)] border-l border-[var(--border-primary)] p-4 flex flex-col space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold">AI Assistant</h3>
              <button className="p-1.5 rounded-full hover:bg-[var(--bg-tertiary)] transition-colors duration-75">
                <span>✕</span>
              </button>
            </div>
            <div className="flex-1 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg flex flex-col">
              <div className="p-3 border-b border-[var(--border-primary)] flex items-center justify-between">
                <p className="font-medium text-sm">AI Co-pilot</p>
                <button className="px-2 py-1 text-xs border rounded-md">
                  Configure
                </button>
              </div>
              <div className="flex-1 p-3 space-y-3 overflow-y-auto">
                <div className="bg-[var(--bg-tertiary)] rounded-md p-2.5 text-xs">
                  Summarize this email and draft a polite decline.
                </div>
                <div className="bg-[var(--accent-primary)] text-white rounded-md p-2.5 text-xs">
                  Draft prepared: "Hi Sarah, thanks for the heads-up..."
                </div>
              </div>
              <div className="p-3 border-t border-[var(--border-primary)]">
                <textarea
                  className="w-full p-2.5 border rounded-md resize-none text-xs"
                  placeholder="Chat with AI..."
                />
                <button className="mt-2 w-full bg-[var(--accent-primary)] text-white rounded-md py-1.5 text-xs">
                  Send
                </button>
              </div>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
