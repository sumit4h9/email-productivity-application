import { useState, useEffect, useRef, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useQueries } from "@tanstack/react-query";
import EmailList from "@/components/EmailList";
import { EmailData } from "@/components/EmailCard";
import Logo from "@/components/ui/Logo";
import {
  useConnectedAccounts,
  useDisconnectAccount,
} from "@/hooks/useOAuthAccounts";
import { oauthAPI, AccountStatusResponse } from "@/lib/api";
import {
  Mail,
  Send,
  Archive,
  Trash2,
  Search,
  RefreshCw,
  Bell,
  Plus,
  Edit,
  LogOut,
  ChevronDown,
  Bold,
  Italic,
  Underline,
  Paperclip,
  Mic,
  X,
  Minus,
  Maximize,
  User,
  Users,
  Settings,
  Palette,
  Shield,
  Phone,
  Sparkles,
  Megaphone,
  Gauge,
  Trash,
  Flag,
  CheckCheck,
  Infinity as InfinityIcon,
} from "lucide-react";
import { useLogout, useCurrentUser } from "@/hooks/useAuthHooks";

type Theme = "default" | "dark" | "sunset" | "oceanic";
type Folder = "inbox" | "sent" | "archive" | "deleted" | "chat";

const Dashboard = () => {
  const navigate = useNavigate();
  const { data: user } = useCurrentUser();
  const [theme, setTheme] = useState<Theme>("default");
  const [composeOpen, setComposeOpen] = useState(false);
  const [composeMinimized, setComposeMinimized] = useState(false);
  const [showCcBcc, setShowCcBcc] = useState(false);
  const [composeData, setComposeData] = useState({
    to: "",
    cc: "",
    bcc: "",
    subject: "",
    body: "",
  });
  const [attachments, setAttachments] = useState<File[]>([]);
  const bodyRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeFolder, setActiveFolder] = useState<Folder>("inbox");
  const [accountDropdownOpen, setAccountDropdownOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const [settingsDropdownOpen, setSettingsDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [tagFilter, setTagFilter] = useState<string | null>(null);
  const userMenuRef = useRef<HTMLDivElement | null>(null);
  const logoutMutation = useLogout();

  // Use connected accounts hook
  const {
    data: accountsData,
    isLoading: accountsLoading,
    error: accountsError,
  } = useConnectedAccounts();
  const disconnectMutation = useDisconnectAccount();

  // Function to disconnect an account by ID
  const disconnectAccount = (accountId: string) => {
    if (disconnectMutation.isPending) return; // Prevent multiple clicks
    disconnectMutation.mutate(accountId, {
      onSuccess: () => {
        console.log(`Successfully disconnected account ${accountId}`);
      },
      onError: error => {
        console.error(`Failed to disconnect account ${accountId}:`, error);
        // You could add a toast notification here
        alert(`Failed to disconnect account. Please try again.`);
      },
    });
  };

  // Apply theme to document
  useEffect(() => {
    document.documentElement.className = theme === "default" ? "" : theme;
  }, [theme]);

  // Close profile dropdown on outside click
  useEffect(() => {
    if (!userDropdownOpen) return;
    const onClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      if (userMenuRef.current && !userMenuRef.current.contains(target)) {
        setUserDropdownOpen(false);
        setSettingsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [userDropdownOpen]);

  // Handle placeholder for contentEditable div
  useEffect(() => {
    const handlePlaceholder = () => {
      if (bodyRef.current) {
        const div = bodyRef.current;
        if (div.innerHTML.trim() === "") {
          div.innerHTML =
            '<span class="placeholder-text">Compose your email...</span>';
        } else {
          const placeholder = div.querySelector(".placeholder-text");
          if (
            placeholder &&
            div.innerHTML.trim() ===
              '<span class="placeholder-text">Compose your email...</span>'
          ) {
            div.innerHTML = "";
          }
        }
      }
    };

    if (bodyRef.current) {
      const currentDiv = bodyRef.current;
      const onFocus = () => {
        if (
          currentDiv.innerHTML.trim() ===
          '<span class="placeholder-text">Compose your email...</span>'
        ) {
          currentDiv.innerHTML = "";
        }
      };

      currentDiv.addEventListener("focus", onFocus);
      currentDiv.addEventListener("blur", handlePlaceholder);
      currentDiv.addEventListener("input", handlePlaceholder);

      return () => {
        currentDiv.removeEventListener("focus", onFocus);
        currentDiv.removeEventListener("blur", handlePlaceholder);
        currentDiv.removeEventListener("input", handlePlaceholder);
      };
    }
  }, []);

  // Use useQueries to fetch account statuses for all accounts
  const accountQueries = useQueries({
    queries:
      accountsData?.accounts?.map(account => ({
        queryKey: ["accountStatus", account.id],
        queryFn: () => oauthAPI.getAccountStatus(account.id),
        enabled: !!account.id,
        staleTime: 2 * 60 * 1000, // 2 minutes
      })) || [],
  });

  // Derive accountStatuses from the queries
  const accountStatuses = useMemo(() => {
    const statuses: Record<string, AccountStatusResponse> = {};
    accountQueries.forEach((query, index) => {
      const account = accountsData?.accounts?.[index];
      if (account && query.data) {
        statuses[account.id] = query.data;
      }
    });
    return statuses;
  }, [accountQueries, accountsData]);

  // Apply theme to document
  useEffect(() => {
    document.documentElement.className = theme === "default" ? "" : theme;
  }, [theme]);

  // Close profile dropdown on outside click
  useEffect(() => {
    if (!userDropdownOpen) return;
    const onClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      if (userMenuRef.current && !userMenuRef.current.contains(target)) {
        setUserDropdownOpen(false);
        setSettingsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [userDropdownOpen]);

  // Handle placeholder for contentEditable div
  useEffect(() => {
    const handlePlaceholder = () => {
      if (bodyRef.current) {
        const div = bodyRef.current;
        if (div.innerHTML.trim() === "") {
          div.innerHTML =
            '<span class="placeholder-text">Compose your email...</span>';
        } else {
          const placeholder = div.querySelector(".placeholder-text");
          if (
            placeholder &&
            div.innerHTML.trim() ===
              '<span class="placeholder-text">Compose your email...</span>'
          ) {
            div.innerHTML = "";
          }
        }
      }
    };

    if (bodyRef.current) {
      const currentDiv = bodyRef.current;
      const onFocus = () => {
        if (
          currentDiv.innerHTML.trim() ===
          '<span class="placeholder-text">Compose your email...</span>'
        ) {
          currentDiv.innerHTML = "";
        }
      };

      currentDiv.addEventListener("focus", onFocus);
      currentDiv.addEventListener("blur", handlePlaceholder);
      currentDiv.addEventListener("input", handlePlaceholder);

      return () => {
        currentDiv.removeEventListener("focus", onFocus);
        currentDiv.removeEventListener("blur", handlePlaceholder);
        currentDiv.removeEventListener("input", handlePlaceholder);
      };
    }
  }, []);

  // Callback functions for email actions
  const handleReply = (email: EmailData) => {
    setComposeData({
      to: email.sender,
      cc: "",
      bcc: "",
      subject: `Re: ${email.subject}`,
      body: "",
    });
    setComposeOpen(true);
    setComposeMinimized(false);
  };

  const handleForward = (email: EmailData) => {
    setComposeData({
      to: "",
      cc: "",
      bcc: "",
      subject: `Fwd: ${email.subject}`,
      body: email.content || "",
    });
    setComposeOpen(true);
    setComposeMinimized(false);
  };

  const handleAutoWrite = (email: EmailData) => {
    setComposeData({
      to: email.sender,
      cc: "",
      bcc: "",
      subject: `Re: ${email.subject}`,
      body: "",
    });
    setComposeOpen(true);
    setComposeMinimized(false);
  };

  return (
    <>
      <style>
        {`
          .placeholder-text {
            color: #9ca3af;
            font-style: italic;
            pointer-events: none;
          }
        `}
      </style>
      <div className="flex h-screen bg-bg-primary text-text-primary font-lexend antialiased">
        {/* Sidebar */}
        <aside className="w-64 flex flex-col border-r border-border-primary bg-bg-primary">
          {/* Logo */}
          <div className="px-6 py-6 flex items-center">
            <div className="w-8 h-8 flex items-center justify-center mr-3">
              <Logo className="w-7 h-7" />
            </div>
            <h1 className="text-xl font-semibold text-text-primary">Axnore</h1>
          </div>

          {/* Account Switcher */}
          <div className="px-4 py-2 relative">
            <button
              onClick={() => setAccountDropdownOpen(!accountDropdownOpen)}
              className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-text-secondary bg-bg-tertiary rounded-xl hover:bg-opacity-80 border border-border-primary transition-all duration-200"
            >
              <div className="flex items-center">
                <Users className="mr-3 w-4 h-4" />
                <span>Switch Account</span>
              </div>
              <ChevronDown
                className={`w-4 h-4 text-text-tertiary transition-transform ${accountDropdownOpen ? "rotate-180" : ""}`}
              />
            </button>

            {accountDropdownOpen && (
              <div className="mt-3 space-y-2 animate-in slide-in-from-top-2 duration-200">
                {accountsData?.accounts?.map(account => (
                  <div
                    key={account.id}
                    className={`group flex items-center justify-between p-3 rounded-xl transition-colors duration-200 cursor-pointer ${
                      account.is_active
                        ? "bg-bg-tertiary border border-border-primary"
                        : "hover:bg-account-item-hover border border-transparent hover:border-border-secondary"
                    }`}
                  >
                    <div className="flex items-center">
                      <div className="w-8 h-8 rounded-full ring-2 ring-border-primary bg-accent-primary flex items-center justify-center">
                        <span className="text-xs font-semibold text-accent-text">
                          {account.provider.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="ml-3">
                        <p className="text-xs font-semibold text-text-primary">
                          {account.account_email}
                        </p>
                        {account.is_active && (
                          <span className="text-xs text-success-text font-medium">
                            Active
                          </span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => disconnectAccount(account.id)}
                      className="p-2 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200 hover:bg-danger-bg"
                    >
                      <LogOut className="w-3 h-3 text-text-tertiary group-hover:text-danger-text" />
                    </button>
                  </div>
                ))}

                <button
                  onClick={() => {
                    navigate("/auth-connect");
                    setAccountDropdownOpen(false);
                  }}
                  className="w-full flex items-center justify-center px-3 py-3 text-sm font-medium text-accent-text bg-accent-primary rounded-xl hover:bg-accent-primary-hover shadow-sm transition-all duration-200"
                >
                  <Plus className="mr-2 w-4 h-4" />
                  <span>Add Account</span>
                </button>
              </div>
            )}
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-2 space-y-2">
            <button
              onClick={() => {
                setComposeOpen(true);
                setComposeMinimized(false);
              }}
              className="w-full flex items-center justify-center px-4 py-3 text-sm font-medium text-accent-text bg-gradient-to-r from-accent-primary to-purple-500 rounded-xl hover:shadow-lg shadow-accent-primary/20 transition-all duration-200"
            >
              <Edit className="mr-2 w-4 h-4" />
              <span>Compose Email</span>
            </button>

            <p className="px-4 pt-6 text-xs font-semibold text-text-tertiary uppercase tracking-wider">
              Inbox
            </p>

            <a
              href="#"
              onClick={e => {
                e.preventDefault();
                setActiveFolder("inbox");
              }}
              className={`flex items-center justify-between px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                activeFolder === "inbox"
                  ? "bg-accent-primary text-accent-text shadow-sm"
                  : "text-text-secondary hover:bg-bg-tertiary"
              }`}
            >
              <div className="flex items-center">
                <Mail className="mr-3 w-4 h-4" />
                <span>Your Emails</span>
              </div>
              <span
                className={`text-xs font-bold rounded-full px-2 py-1 ${
                  activeFolder === "inbox"
                    ? "bg-accent-primary-hover text-accent-text"
                    : "bg-bg-tertiary text-text-secondary"
                }`}
              >
                47
              </span>
            </a>

            <a
              href="#"
              onClick={e => {
                e.preventDefault();
                setActiveFolder("chat");
              }}
              className={`flex items-center justify-between px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                activeFolder === "chat"
                  ? "bg-accent-primary text-accent-text shadow-sm"
                  : "text-text-secondary hover:bg-bg-tertiary"
              }`}
            >
              <div className="flex items-center">
                <Mail className="mr-3 w-4 h-4" />
                <span>Chat</span>
              </div>
            </a>

            <a
              href="#"
              onClick={e => {
                e.preventDefault();
                setActiveFolder("sent");
              }}
              className={`flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                activeFolder === "sent"
                  ? "bg-accent-primary text-accent-text shadow-sm"
                  : "text-text-secondary hover:bg-bg-tertiary"
              }`}
            >
              <Send className="mr-3 w-4 h-4" />
              <span>Sent</span>
            </a>

            <a
              href="#"
              onClick={e => {
                e.preventDefault();
                setActiveFolder("archive");
              }}
              className={`flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                activeFolder === "archive"
                  ? "bg-accent-primary text-accent-text shadow-sm"
                  : "text-text-secondary hover:bg-bg-tertiary"
              }`}
            >
              <Archive className="mr-3 w-4 h-4" />
              <span>Archive</span>
            </a>

            <a
              href="#"
              onClick={e => {
                e.preventDefault();
                setActiveFolder("deleted");
              }}
              className={`flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                activeFolder === "deleted"
                  ? "bg-accent-primary text-accent-text shadow-sm"
                  : "text-text-secondary hover:bg-bg-tertiary"
              }`}
            >
              <Trash2 className="mr-3 w-4 h-4" />
              <span>Deleted</span>
            </a>

            <p className="px-4 pt-6 text-xs font-semibold text-text-tertiary uppercase tracking-wider">
              AI Insights
            </p>

            <a
              href="#"
              className="flex items-center justify-between px-4 py-3 text-sm font-medium text-text-secondary hover:bg-bg-tertiary rounded-xl transition-all duration-200"
            >
              <div className="flex items-center">
                <Gauge className="mr-3 w-4 h-4" />
                <span>Email Health Score</span>
              </div>
              <span className="text-xs font-bold text-success-text bg-success-bg rounded-full px-2 py-1">
                84
              </span>
            </a>

            <a
              href="#"
              className="flex items-center px-4 py-3 text-sm font-medium text-text-secondary hover:bg-bg-tertiary rounded-xl transition-all duration-200"
            >
              <Megaphone className="mr-3 w-4 h-4" />
              <span>Updates</span>
            </a>
          </nav>

          <div className="px-4 py-4 mt-auto">
            <div className="border-t border-border-primary"></div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col relative">
          {/* Header */}
          <header className="flex items-center justify-between p-3 border-b border-border-primary bg-bg-primary">
            <div>
              <h2 className="text-xl font-semibold text-text-primary">
                Axnore Dashboard
              </h2>
              <p className="text-xs text-text-tertiary font-light">
                AI-powered email management and security
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <span className="text-xs text-text-tertiary font-light">
                Last synced: 2 min ago
              </span>
              <button className="p-2 rounded-xl hover:bg-bg-tertiary transition-colors">
                <Bell className="text-text-secondary w-5 h-5" />
              </button>

              {/* User Dropdown */}
              <div className="relative" ref={userMenuRef}>
                <button
                  onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                  className="flex items-center space-x-2 focus:outline-none"
                >
                  <img
                    alt="User avatar"
                    className="w-10 h-10 rounded-full ring-2 ring-border-primary"
                    src="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop&crop=face"
                  />
                </button>

                {userDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-64 bg-bg-primary rounded-xl shadow-xl border border-border-primary z-50 animate-in slide-in-from-top-2 duration-200">
                    <div className="p-3">
                      <div className="px-3 py-3">
                        <p className="text-sm font-semibold text-text-primary">
                          {user?.username || user?.email || "User"}
                        </p>
                        <p className="text-xs text-text-tertiary font-light">
                          {user?.email || "demo@axnore.com"}
                        </p>
                      </div>
                      <div className="border-t border-border-primary my-2"></div>
                      <a
                        href="#"
                        className="flex items-center px-3 py-3 text-sm text-text-secondary hover:bg-bg-tertiary rounded-lg transition-colors"
                      >
                        <User className="mr-3 w-4 h-4" />
                        Profile
                      </a>
                      {/* Settings Submenu */}
                      <div className="relative">
                        <button
                          onClick={() =>
                            setSettingsDropdownOpen(!settingsDropdownOpen)
                          }
                          className="w-full flex items-center justify-between px-3 py-3 text-sm text-text-secondary hover:bg-bg-tertiary rounded-lg transition-colors"
                        >
                          <div className="flex items-center">
                            <Settings className="mr-3 w-4 h-4" />
                            <span>Settings</span>
                          </div>
                          <ChevronDown
                            className={`w-4 h-4 transition-transform ${settingsDropdownOpen ? "rotate-180" : ""}`}
                          />
                        </button>

                        {settingsDropdownOpen && (
                          <div className="pl-6 space-y-1">
                            <button
                              onClick={() => {
                                const themes: Theme[] = [
                                  "default",
                                  "dark",
                                  "sunset",
                                  "oceanic",
                                ];
                                const currentIndex = themes.indexOf(theme);
                                const nextTheme =
                                  themes[(currentIndex + 1) % themes.length];
                                setTheme(nextTheme);
                              }}
                              className="flex items-center px-3 py-2 text-sm text-text-secondary hover:bg-bg-tertiary rounded-lg w-full transition-colors"
                            >
                              <Palette className="mr-3 w-4 h-4" />
                              Theme ({theme})
                            </button>
                            <a
                              href="#"
                              className="flex items-center px-3 py-2 text-sm text-text-secondary hover:bg-bg-tertiary rounded-lg transition-colors"
                            >
                              <Shield className="mr-3 w-4 h-4" />
                              Privacy
                            </a>
                            <a
                              href="#"
                              className="flex items-center px-3 py-2 text-sm text-text-secondary hover:bg-bg-tertiary rounded-lg transition-colors"
                            >
                              <Bell className="mr-3 w-4 h-4" />
                              Notifications
                            </a>
                          </div>
                        )}
                      </div>

                      <div className="border-t border-border-primary my-2"></div>
                      <button
                        onClick={() => logoutMutation.mutate()}
                        className="flex items-center w-full text-left px-3 py-3 text-sm text-text-secondary hover:bg-bg-tertiary rounded-lg transition-colors"
                      >
                        <LogOut className="mr-3 w-4 h-4" />
                        Logout
                      </button>
                      <button
                        onClick={() => logoutMutation.mutate()}
                        className="flex items-center w-full text-left px-3 py-3 text-sm text-danger-text hover:bg-danger-bg rounded-lg transition-colors"
                      >
                        <Phone className="mr-3 w-4 h-4" />
                        Logout from All Devices
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </header>

          {/* Content Area */}
          <div className="flex-1 flex overflow-hidden">
            {/* Email List */}
            <div className="flex-1 p-6 overflow-y-auto bg-bg-secondary">
              {/* Search and Quick Actions */}
              <div className="mb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 flex-1">
                    <div className="relative w-64">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary w-4 h-4" />
                      <input
                        className="w-full pl-10 pr-4 py-2 border border-border-secondary rounded-xl focus:outline-none focus:ring-2 focus:ring-accent-primary bg-bg-primary text-text-primary placeholder-text-tertiary font-light transition-all duration-200"
                        placeholder="Search emails..."
                        type="text"
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                      />
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-text-secondary whitespace-nowrap">
                        Quick Actions:
                      </span>
                      <button className="flex items-center px-3 py-1 text-xs font-medium text-text-secondary bg-bg-primary border border-border-secondary rounded-full hover:bg-bg-tertiary transition-all duration-200">
                        <Trash className="w-3 h-3 mr-1" />
                        Clean Promotions
                      </button>
                      <button className="flex items-center px-3 py-1 text-xs font-medium text-danger-text bg-danger-bg border border-danger-border rounded-full hover:bg-danger-hover transition-all duration-200">
                        <Flag className="w-3 h-3 mr-1" />
                        Review Flagged
                      </button>
                      <button className="flex items-center px-3 py-1 text-xs font-medium text-success-text bg-success-bg border border-success-border rounded-full hover:bg-success-hover transition-all duration-200">
                        <CheckCheck className="w-3 h-3 mr-1" />
                        Mark All Read
                      </button>
                    </div>
                  </div>
                </div>
                <h2 className="mt-4 mb-2 text-lg font-semibold text-text-primary">
                  Your Emails (3 unread)
                </h2>
                {/* Header */}
                {/* Tag filter buttons */}
                <div className="flex items-center justify-between mt-2">
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setTagFilter(null)}
                      className={`px-3 py-1 rounded-full text-xs font-medium ${
                        tagFilter === null
                          ? "bg-accent-primary text-accent-text"
                          : "bg-bg-primary text-text-secondary border border-border-secondary hover:bg-bg-tertiary"
                      }`}
                    >
                      All
                    </button>
                    {["payment", "work", "spam", "promotion", "custom"].map(
                      tag => (
                        <button
                          key={tag}
                          onClick={() => setTagFilter(tag)}
                          className={`px-3 py-1 rounded-full text-xs font-medium ${
                            tagFilter === tag
                              ? "bg-accent-primary text-accent-text"
                              : "bg-bg-primary text-text-secondary border border-border-secondary hover:bg-bg-tertiary"
                          }`}
                        >
                          {tag.charAt(0).toUpperCase() + tag.slice(1)}
                        </button>
                      )
                    )}
                  </div>
                  <button
                    onClick={() => {
                      // Implement refresh logic here, perhaps refetch emails
                      console.log("Refresh clicked");
                    }}
                    className="p-2 text-text-tertiary rounded-lg hover:bg-bg-tertiary transition-colors flex items-center"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    <span className="text-sm font-medium">Refresh</span>
                  </button>
                </div>
              </div>

              {/* Email List Component */}
              {activeFolder === "chat" ? (
                <div className="flex items-center justify-center h-full text-2xl font-semibold text-text-secondary">
                  Coming soon
                </div>
              ) : (
                <EmailList
                  folder={activeFolder}
                  searchQuery={searchQuery}
                  tagFilter={tagFilter}
                  onReply={handleReply}
                  onForward={handleForward}
                  onAutoWrite={handleAutoWrite}
                />
              )}

              {/* Footer */}
              <div className="pt-8 mt-auto border-t border-border-primary">
                <div className="flex space-x-6 text-sm text-text-tertiary">
                  <a
                    className="hover:text-text-primary transition-colors font-light"
                    href="#"
                  >
                    Resources
                  </a>
                  <a
                    className="hover:text-text-primary transition-colors font-light"
                    href="#"
                  >
                    Legal
                  </a>
                  <a
                    className="hover:text-text-primary transition-colors font-light"
                    href="#"
                  >
                    Contact Us
                  </a>
                </div>
              </div>
              <p className="text-xs text-text-tertiary text-center pt-6 font-light">
                All Rights Reserved by Axnore
              </p>
            </div>

            {/* AI Assistant Sidebar */}
            <aside className="w-[380px] bg-bg-secondary border-l border-border-primary p-6 flex flex-col space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-text-primary">
                  AI Assistant
                </h3>
                <button className="p-2 text-text-tertiary rounded-xl hover:bg-bg-tertiary transition-colors">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="flex-1 bg-bg-primary border border-border-primary rounded-2xl flex flex-col">
                <div className="p-4 border-b border-border-primary">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-9 h-9 bg-gradient-to-br from-accent-primary to-purple-500 rounded-xl flex items-center justify-center shrink-0 shadow-sm">
                        <Sparkles className="text-accent-text w-4 h-4" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-text-primary">
                          AI Co-pilot
                        </p>
                        <p className="text-xs text-text-tertiary font-light">
                          Powered by GPT-4 Turbo
                        </p>
                      </div>
                    </div>
                    <button className="flex items-center px-3 py-2 text-xs font-medium text-text-secondary bg-bg-primary border border-border-secondary rounded-xl hover:bg-bg-tertiary transition-colors">
                      <Settings className="w-3 h-3 mr-2" />
                      Configure
                    </button>
                  </div>
                </div>

                <div
                  className="flex-1 p-4 space-y-4 overflow-y-auto"
                  style={{ maxHeight: "calc(100vh - 350px)" }}
                >
                  <div className="flex items-start space-x-3">
                    <img
                      alt="User avatar"
                      className="w-8 h-8 rounded-full ring-2 ring-border-primary"
                      src="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop&crop=face"
                    />
                    <div className="bg-bg-tertiary rounded-2xl p-3 max-w-xs">
                      <p className="text-sm text-text-primary font-light">
                        Summarize this email and draft a polite decline.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3 justify-end">
                    <div className="bg-accent-primary rounded-2xl p-3 max-w-xs">
                      <p className="text-sm text-accent-text font-light">
                        The email is from Sarah Chen about the Q4 Marketing
                        Strategy. She needs input by EOD Friday. Here is a draft
                        to decline:
                      </p>
                      <div className="mt-3 bg-accent-primary-hover/30 p-3 rounded-xl text-accent-text text-xs font-light">
                        <p>Hi Sarah,</p>
                        <p>
                          Thanks for the heads-up. Unfortunately, I won't have
                          the bandwidth to provide meaningful feedback by
                          Friday. Apologies for not being able to contribute
                          this time.
                        </p>
                        <p>Best,</p>
                        <p>[Your Name]</p>
                      </div>
                    </div>
                    <div className="w-8 h-8 bg-accent-primary rounded-full flex items-center justify-center shrink-0">
                      <Sparkles className="text-accent-text w-4 h-4" />
                    </div>
                  </div>
                </div>

                <div className="p-4 border-t border-border-primary mt-auto">
                  <div className="relative">
                    <textarea
                      className="w-full p-3 pr-28 border border-border-secondary rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-accent-primary text-sm bg-bg-primary text-text-primary placeholder-text-tertiary font-light transition-all duration-200"
                      placeholder="Chat with AI or type '/' for commands..."
                      rows={2}
                    />
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center space-x-2">
                      <button className="p-2 rounded-xl hover:bg-bg-tertiary text-text-tertiary hover:text-text-primary transition-colors">
                        <Mic className="w-4 h-4" />
                      </button>
                      <button className="px-4 py-2 text-sm font-medium text-accent-text bg-accent-primary rounded-xl hover:bg-accent-primary-hover flex items-center transition-colors">
                        Send
                        <Send className="w-4 h-4 ml-2" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </aside>
          </div>

          {/* Compose Email Modal */}
          {composeOpen && (
            <div
              className={`fixed bottom-0 right-24 w-[560px] bg-bg-primary rounded-t-2xl shadow-2xl border border-border-primary flex flex-col z-50 transition-all duration-300 ${
                composeMinimized ? "h-12" : "h-[520px]"
              }`}
            >
              <div
                onClick={() => setComposeMinimized(!composeMinimized)}
                className="flex items-center justify-between px-4 py-3 bg-bg-tertiary rounded-t-2xl cursor-pointer"
              >
                <h4 className="text-sm font-semibold text-text-primary">
                  New Message
                </h4>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={e => {
                      e.stopPropagation();
                      setComposeMinimized(!composeMinimized);
                    }}
                    className="p-1 rounded-lg hover:bg-bg-secondary transition-colors"
                  >
                    {composeMinimized ? (
                      <Maximize className="w-4 h-4 text-text-tertiary" />
                    ) : (
                      <Minus className="w-4 h-4 text-text-tertiary" />
                    )}
                  </button>
                  <button
                    onClick={e => {
                      e.stopPropagation();
                      setComposeOpen(false);
                    }}
                    className="p-1 rounded-lg hover:bg-bg-secondary transition-colors"
                  >
                    <X className="w-4 h-4 text-text-tertiary" />
                  </button>
                </div>
              </div>

              {!composeMinimized && (
                <div className="flex-1 flex flex-col p-4 space-y-4">
                  <div className="flex items-center">
                    <input
                      className="flex-1 px-3 py-3 text-sm border-b border-border-primary focus:outline-none focus:border-accent-primary bg-transparent text-text-primary placeholder-text-tertiary font-light transition-colors"
                      placeholder="Recipients"
                      type="text"
                    />
                    <button
                      onClick={() => setShowCcBcc(!showCcBcc)}
                      className="ml-3 text-sm text-text-tertiary hover:text-text-primary font-light transition-colors"
                    >
                      Cc/Bcc
                    </button>
                  </div>

                  {showCcBcc && (
                    <div className="space-y-3 animate-in slide-in-from-top-2 duration-200">
                      <input
                        className="w-full px-3 py-3 text-sm border-b border-border-primary focus:outline-none focus:border-accent-primary bg-transparent text-text-primary placeholder-text-tertiary font-light transition-colors"
                        placeholder="Cc"
                        type="text"
                      />
                      <input
                        className="w-full px-3 py-3 text-sm border-b border-border-primary focus:outline-none focus:border-accent-primary bg-transparent text-text-primary placeholder-text-tertiary font-light transition-colors"
                        placeholder="Bcc"
                        type="text"
                      />
                    </div>
                  )}

                  <input
                    className="w-full px-3 py-3 text-sm border-b border-border-primary focus:outline-none focus:border-accent-primary bg-transparent text-text-primary placeholder-text-tertiary font-light transition-colors"
                    placeholder="Subject"
                    type="text"
                  />

                  <div className="flex-1 relative">
                    <div
                      ref={bodyRef}
                      contentEditable={!composeMinimized}
                      suppressContentEditableWarning={true}
                      className="w-full h-full p-3 text-sm border-none focus:outline-none resize-none bg-transparent text-text-primary placeholder-text-tertiary font-light overflow-auto"
                      data-placeholder="Compose your email..."
                      onInput={e => {
                        const html = (e.target as HTMLDivElement).innerHTML;
                        setComposeData(prev => ({ ...prev, body: html }));
                      }}
                    />
                    <div className="absolute bottom-2 left-3">
                      <button className="flex items-center px-3 py-2 text-xs font-medium text-accent-text bg-accent-primary rounded-full hover:bg-accent-primary-hover shadow-sm transition-all duration-200">
                        <Sparkles className="w-3 h-3 mr-2" />
                        <span>Auto-Writer</span>
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center justify-between border-t border-border-primary pt-3">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => document.execCommand("bold")}
                        className="p-2 rounded-xl hover:bg-bg-tertiary text-text-secondary transition-colors"
                        type="button"
                      >
                        <Bold className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => document.execCommand("italic")}
                        className="p-2 rounded-xl hover:bg-bg-tertiary text-text-secondary transition-colors"
                        type="button"
                      >
                        <Italic className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => document.execCommand("underline")}
                        className="p-2 rounded-xl hover:bg-bg-tertiary text-text-secondary transition-colors"
                        type="button"
                      >
                        <Underline className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        className="p-2 rounded-xl hover:bg-bg-tertiary text-text-secondary transition-colors"
                        type="button"
                      >
                        <Paperclip className="w-4 h-4" />
                      </button>
                    </div>
                    <button
                      className="flex items-center px-5 py-2 text-sm font-medium text-accent-text bg-accent-primary rounded-xl hover:bg-accent-primary-hover transition-colors"
                      type="button"
                      onClick={() => {
                        // Implement send email logic here
                        console.log("Send email:", composeData, attachments);
                      }}
                    >
                      <span>Send</span>
                      <Send className="w-4 h-4 ml-2" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Hidden file input for attachments */}
          <input
            type="file"
            multiple
            ref={fileInputRef}
            className="hidden"
            onChange={e => {
              if (e.target.files) {
                setAttachments(prev => [
                  ...prev,
                  ...Array.from(e.target.files),
                ]);
                e.target.value = "";
              }
            }}
          />

          {/* Display attachments */}
          {attachments.length > 0 && (
            <div className="fixed bottom-[540px] right-24 w-[560px] bg-bg-secondary rounded-t-2xl shadow-lg border border-border-primary p-4 z-50 max-h-40 overflow-y-auto">
              <h4 className="text-sm font-semibold text-text-primary mb-2">
                Attachments
              </h4>
              <ul className="space-y-1">
                {attachments.map((file, index) => (
                  <li
                    key={index}
                    className="flex items-center justify-between bg-bg-primary rounded-md px-3 py-2"
                  >
                    <span className="text-xs text-text-primary truncate max-w-[400px]">
                      {file.name}
                    </span>
                    <button
                      onClick={() =>
                        setAttachments(prev =>
                          prev.filter((_, i) => i !== index)
                        )
                      }
                      className="text-danger-text hover:text-danger-hover"
                      type="button"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </main>
      </div>
    </>
  );
};

export default Dashboard;
