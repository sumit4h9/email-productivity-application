import { useState } from "react";
import { useNavigate } from "react-router-dom";

const AddAccount = () => {
  const navigate = useNavigate();
  const [switchAccountOpen, setSwitchAccountOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  // Theme color mappings
  const colors = {
    default: {
      bgPrimary: "#ffffff",
      bgSecondary: "#f8fafc",
      bgTertiary: "#f1f5f9",
      textPrimary: "#111827",
      textSecondary: "#4b5563",
      textTertiary: "#6b7280",
      borderPrimary: "#e5e7eb",
      accentPrimary: "#2563eb",
      accentPrimaryHover: "#1d4ed8",
      accentText: "#ffffff",
    },
  };

  const currentColors = colors.default;

  return (
    <div
      className="flex h-screen"
      style={{
        backgroundColor: currentColors.bgPrimary,
        color: currentColors.textPrimary,
        fontFamily: "Inter, sans-serif",
      }}
    >
      {/* Sidebar */}
      <aside
        className="w-64 flex flex-col"
        style={{ borderRight: `1px solid ${currentColors.borderPrimary}` }}
      >
        <div className="px-6 py-5 flex items-center">
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center mr-3"
            style={{ backgroundColor: currentColors.accentPrimary }}
          >
            <span
              className="material-icons"
              style={{ color: currentColors.accentText }}
            >
              all_inclusive
            </span>
          </div>
          <h1
            className="text-xl font-bold"
            style={{ color: currentColors.textPrimary }}
          >
            Axnore
          </h1>
        </div>

        <div className="px-4 py-2">
          <button
            onClick={() => setSwitchAccountOpen(!switchAccountOpen)}
            className="w-full flex items-center justify-between px-4 py-2 text-sm font-medium rounded-lg transition-colors"
            style={{
              color: currentColors.textSecondary,
              backgroundColor: currentColors.bgTertiary,
              border: `1px solid ${currentColors.borderPrimary}`,
            }}
            onMouseEnter={e =>
              (e.currentTarget.style.backgroundColor =
                currentColors.bgSecondary)
            }
            onMouseLeave={e =>
              (e.currentTarget.style.backgroundColor = currentColors.bgTertiary)
            }
          >
            <div className="flex items-center">
              <span className="material-icons mr-3">switch_account</span>
              <span>Switch Account</span>
            </div>
            <span
              className={`material-icons text-lg transition-transform ${switchAccountOpen ? "rotate-180" : ""}`}
              style={{ color: currentColors.textTertiary }}
            >
              unfold_more
            </span>
          </button>

          {switchAccountOpen && (
            <div className="mt-2 space-y-2">
              <button
                className="w-full flex items-center justify-center px-2 py-2 text-sm font-medium rounded-lg shadow-md transition-colors"
                style={{
                  color: currentColors.accentText,
                  backgroundColor: currentColors.accentPrimary,
                }}
                onMouseEnter={e =>
                  (e.currentTarget.style.backgroundColor =
                    currentColors.accentPrimaryHover)
                }
                onMouseLeave={e =>
                  (e.currentTarget.style.backgroundColor =
                    currentColors.accentPrimary)
                }
              >
                <span className="material-icons mr-2 text-base">add</span>
                <span>Add New Account</span>
              </button>
            </div>
          )}
        </div>

        <nav className="flex-1 px-4 py-2 space-y-2">
          <button
            className="w-full flex items-center justify-center px-4 py-3 text-sm font-medium rounded-lg shadow-lg transition-all duration-200 opacity-50 cursor-not-allowed"
            style={{
              color: currentColors.accentText,
              backgroundColor: currentColors.accentPrimary,
            }}
          >
            <span className="material-icons mr-2">edit</span>
            <span>Compose Email</span>
          </button>

          <p
            className="px-4 pt-4 text-xs font-semibold uppercase tracking-wider"
            style={{ color: currentColors.textTertiary }}
          >
            Inbox
          </p>

          <a
            className="flex items-center justify-between px-4 py-2 text-sm font-medium opacity-50 cursor-not-allowed"
            href="#"
            style={{ color: currentColors.textSecondary }}
          >
            <div className="flex items-center">
              <span className="material-icons mr-3">email</span>
              <span>Your Emails</span>
            </div>
          </a>

          <a
            className="flex items-center px-4 py-2 text-sm font-medium opacity-50 cursor-not-allowed"
            href="#"
            style={{ color: currentColors.textSecondary }}
          >
            <span className="material-icons mr-3">send</span>
            <span>Sent</span>
          </a>

          <a
            className="flex items-center px-4 py-2 text-sm font-medium opacity-50 cursor-not-allowed"
            href="#"
            style={{ color: currentColors.textSecondary }}
          >
            <span className="material-icons mr-3">archive</span>
            <span>Archive</span>
          </a>

          <a
            className="flex items-center px-4 py-2 text-sm font-medium opacity-50 cursor-not-allowed"
            href="#"
            style={{ color: currentColors.textSecondary }}
          >
            <span className="material-icons mr-3">delete</span>
            <span>Deleted</span>
          </a>

          <a
            className="flex items-center px-4 py-2 text-sm font-medium opacity-50 cursor-not-allowed"
            href="#"
            style={{ color: currentColors.textSecondary }}
          >
            <span className="material-icons mr-3">campaign</span>
            <span>Updates</span>
          </a>

          <p
            className="px-4 pt-6 text-xs font-semibold uppercase tracking-wider"
            style={{ color: currentColors.textTertiary }}
          >
            AI Insights
          </p>

          <a
            className="flex items-center px-4 py-2 text-sm font-medium opacity-50 cursor-not-allowed"
            href="#"
            style={{ color: currentColors.textSecondary }}
          >
            <span className="material-icons mr-3">smart_toy</span>
            <span>Smart Analysis</span>
          </a>

          <a
            className="flex items-center justify-between px-4 py-2 text-sm font-medium opacity-50 cursor-not-allowed"
            href="#"
            style={{ color: currentColors.textSecondary }}
          >
            <div className="flex items-center">
              <span className="material-icons mr-3">health_and_safety</span>
              <span>Email Health Score</span>
            </div>
          </a>

          <a
            className="flex items-center px-4 py-2 text-sm font-medium opacity-50 cursor-not-allowed"
            href="#"
            style={{ color: currentColors.textSecondary }}
          >
            <span className="material-icons mr-3">shield</span>
            <span>Threat Detection</span>
          </a>

          <a
            className="flex items-center px-4 py-2 text-sm font-medium opacity-50 cursor-not-allowed"
            href="#"
            style={{ color: currentColors.textSecondary }}
          >
            <span className="material-icons mr-3">gpp_bad</span>
            <span>Spam Filter</span>
          </a>
        </nav>

        <div className="px-4 py-4 mt-auto">
          <div
            style={{ borderTop: `1px solid ${currentColors.borderPrimary}` }}
          ></div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        <header
          className="flex items-center justify-between p-6"
          style={{
            borderBottom: `1px solid ${currentColors.borderPrimary}`,
            backgroundColor: currentColors.bgPrimary,
          }}
        >
          <div>
            <h2
              className="text-2xl font-bold"
              style={{ color: currentColors.textPrimary }}
            >
              Axnore Dashboard
            </h2>
            <p
              className="text-sm"
              style={{ color: currentColors.textTertiary }}
            >
              AI-powered email management and security
            </p>
          </div>

          <div className="flex items-center space-x-4">
            <button
              className="p-2 rounded-full transition-colors"
              style={{ backgroundColor: "transparent" }}
              onMouseEnter={e =>
                (e.currentTarget.style.backgroundColor =
                  currentColors.bgTertiary)
              }
              onMouseLeave={e =>
                (e.currentTarget.style.backgroundColor = "transparent")
              }
            >
              <span
                className="material-icons"
                style={{ color: currentColors.textSecondary }}
              >
                notifications
              </span>
            </button>

            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center space-x-2 focus:outline-none"
              >
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: currentColors.bgTertiary }}
                >
                  <span
                    className="material-icons"
                    style={{ color: currentColors.textSecondary }}
                  >
                    person
                  </span>
                </div>
              </button>

              {userMenuOpen && (
                <div
                  className="absolute right-0 mt-2 w-64 rounded-lg shadow-xl"
                  style={{ backgroundColor: currentColors.bgPrimary }}
                >
                  <div className="p-2">
                    <div className="px-2 py-3">
                      <p
                        className="text-sm font-semibold"
                        style={{ color: currentColors.textPrimary }}
                      >
                        Guest User
                      </p>
                    </div>
                    <div
                      style={{
                        borderTop: `1px solid ${currentColors.borderPrimary}`,
                        marginTop: "0.25rem",
                        marginBottom: "0.25rem",
                      }}
                    ></div>
                    <a
                      className="flex items-center px-2 py-2 text-sm rounded-md transition-colors"
                      href="#"
                      style={{ color: currentColors.textSecondary }}
                      onMouseEnter={e =>
                        (e.currentTarget.style.backgroundColor =
                          currentColors.bgTertiary)
                      }
                      onMouseLeave={e =>
                        (e.currentTarget.style.backgroundColor = "transparent")
                      }
                    >
                      <span className="material-icons mr-3">settings</span>{" "}
                      Settings
                    </a>
                    <div
                      style={{
                        borderTop: `1px solid ${currentColors.borderPrimary}`,
                        marginTop: "0.25rem",
                        marginBottom: "0.25rem",
                      }}
                    ></div>
                    <a
                      className="flex items-center px-2 py-2 text-sm rounded-md transition-colors"
                      href="#"
                      style={{ color: currentColors.textSecondary }}
                      onMouseEnter={e =>
                        (e.currentTarget.style.backgroundColor =
                          currentColors.bgTertiary)
                      }
                      onMouseLeave={e =>
                        (e.currentTarget.style.backgroundColor = "transparent")
                      }
                    >
                      <span className="material-icons mr-3">logout</span> Logout
                    </a>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        <div
          className="flex-1 flex flex-col items-center justify-center p-12 text-center"
          style={{ backgroundColor: currentColors.bgSecondary }}
        >
          <div
            className="w-16 h-16 rounded-full flex items-center justify-center mb-6"
            style={{ backgroundColor: `${currentColors.accentPrimary}1a` }}
          >
            <span
              className="material-icons text-4xl"
              style={{ color: currentColors.accentPrimary }}
            >
              email
            </span>
          </div>
          <h2
            className="text-2xl font-bold mb-2"
            style={{ color: currentColors.textPrimary }}
          >
            Connect your first email account
          </h2>
          <p
            className="text-lg mb-8"
            style={{ color: currentColors.textSecondary }}
          >
            Get started by adding an email account to manage your inbox with AI.
          </p>
          <button
            onClick={() => navigate("/auth-connect")}
            className="flex items-center justify-center px-6 py-3 text-lg font-medium rounded-lg shadow-lg transition-all duration-200"
            style={{
              color: currentColors.accentText,
              backgroundColor: currentColors.accentPrimary,
            }}
            onMouseEnter={e => {
              e.currentTarget.style.backgroundColor =
                currentColors.accentPrimaryHover;
              e.currentTarget.style.boxShadow =
                "0 25px 50px -12px rgba(0, 0, 0, 0.25)";
            }}
            onMouseLeave={e => {
              e.currentTarget.style.backgroundColor =
                currentColors.accentPrimary;
              e.currentTarget.style.boxShadow =
                "0 10px 15px -3px rgba(0, 0, 0, 0.1)";
            }}
          >
            <span className="material-icons mr-2">add_circle_outline</span>
            <span>Add Account</span>
          </button>
        </div>
      </main>
    </div>
  );
};

export default AddAccount;
