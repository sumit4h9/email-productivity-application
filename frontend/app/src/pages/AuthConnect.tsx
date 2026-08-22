import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CheckCircle, ArrowRight } from "lucide-react";
import { oauthAPI } from "../lib/api";

type Provider = "google" | "apple" | "outlook";

const AuthConnect = () => {
  const navigate = useNavigate();
  const [connectedAccounts, setConnectedAccounts] = useState({
    google: false,
    apple: false,
    outlook: false,
  });
  const [loading, setLoading] = useState(false);

  const handleConnect = async (provider: Provider) => {
    if (provider === "google") {
      try {
        setLoading(true);
        const { authorization_url } = await oauthAPI.getGoogleUrl();
        window.location.href = authorization_url;
      } catch (error) {
        console.error("Failed to get Google OAuth URL", error);
        alert("Failed to initiate Google OAuth. Please try again.");
      } finally {
        setLoading(false);
      }
      return;
    }

    // For Apple and Outlook, update connectedAccounts state accordingly
    setConnectedAccounts(prev => ({
      ...prev,
      [provider]: true,
    }));
  };

  const handleContinue = () => {
    if (connectedAccounts.apple) {
      navigate("/apple-connect");
    } else if (connectedAccounts.google) {
      // Google flow handled by redirect, no immediate navigation here
      return;
    } else if (connectedAccounts.outlook) {
      // Add Outlook auth logic here
      navigate("/dashboard");
    } else {
      navigate("/dashboard");
    }
  };

  const allConnected = Object.values(connectedAccounts).every(Boolean);
  const someConnected = Object.values(connectedAccounts).some(Boolean);

  return (
    <div className="flex min-h-screen">
      <div className="flex flex-1 flex-col justify-center py-6 px-4 sm:px-6 lg:flex-none lg:px-16 xl:px-20">
        <div className="mx-auto w-full max-w-md lg:w-96">
          <div className="text-center">
            <div className="flex items-center justify-center mb-6">
              <div className="w-12 h-12 bg-gray-900 rounded-full flex items-center justify-center">
                <span className="material-icons text-white text-2xl">
                  all_infinite
                </span>
              </div>
            </div>
            <h1 className="text-3xl font-extrabold tracking-tighter text-gray-900">
              Connect Your Accounts
            </h1>
            <p className="mt-2 text-base text-muted-foreground max-w-sm mx-auto">
              Connect your email accounts to get started with Axnore. You can
              always add more later.
            </p>
          </div>

          <div className="mt-8 space-y-4">
            {/* Google */}
            <div className="relative">
              <button
                onClick={() => handleConnect("google")}
                disabled={connectedAccounts.google || loading}
                className={`w-full flex items-center justify-between p-4 border rounded-lg transition-colors ${
                  connectedAccounts.google
                    ? "border-green-200 bg-green-50 cursor-default"
                    : "border-border bg-background hover:bg-accent cursor-pointer"
                }`}
              >
                <div className="flex items-center">
                  <svg
                    className="h-6 w-6 mr-3"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      fill="#4285F4"
                    ></path>
                    <path
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      fill="#34A853"
                    ></path>
                    <path
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"
                      fill="#FBBC05"
                    ></path>
                    <path
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      fill="#EA4335"
                    ></path>
                    <path d="M1 1h22v22H1z" fill="none"></path>
                  </svg>
                  <div className="text-left">
                    <p className="font-semibold text-foreground">Gmail</p>
                    <p className="text-sm text-muted-foreground">
                      Connect your Google account
                    </p>
                  </div>
                </div>
                {connectedAccounts.google ? (
                  <CheckCircle className="h-6 w-6 text-green-600" />
                ) : (
                  <ArrowRight className="h-5 w-5 text-muted-foreground" />
                )}
              </button>
            </div>

            {/* Apple */}
            <div className="relative">
              <button
                onClick={() => handleConnect("apple")}
                disabled={connectedAccounts.apple || loading}
                className={`w-full flex items-center justify-between p-4 border rounded-lg transition-colors ${
                  connectedAccounts.apple
                    ? "border-green-200 bg-green-50 cursor-default"
                    : "border-border bg-background hover:bg-accent cursor-pointer"
                }`}
              >
                <div className="flex items-center">
                  <svg
                    className="h-6 w-6 mr-3"
                    fill="currentColor"
                    viewBox="0 0 16 16"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path d="M8.813.012a8.43 8.43 0 0 0-4.437 1.348c-1.637 1.139-2.6 2.995-2.825 5.011a8.4 8.4 0 0 0 .584 4.546c.553.86 1.314 1.52 2.21 1.956.88.43 1.833.642 2.784.642.12 0 .239-.005.358-.014a5.1 5.1 0 0 0 .34-.035c.875-.15 1.705-.53 2.45-1.105.797-.613 1.4-1.42 1.768-2.33.12-.3.22-.613.313-.938a.04.04 0 0 1 .046-.035c.124.01.248.014.372.014a4.4 4.4 0 0 0 3.32-1.48C16.883 6.9 16.32 3.1 14.2.983c-1.39-1.408-3.488-1.074-4.575-.971Zm-1.854 2.152a2.3 2.3 0 0 1 1.732-.82c.42.023.832.162 1.196.425.36.26.65.592.833.975.186.386.27.813.25 1.23-.023.42-.163.832-.425 1.196-.26.36-.593.65-.975.833-.386.186-.813.27-1.23.25-.42-.023-.832-.163-1.196-.425a2.29 2.29 0 0 1-.833-.975 2.29 2.29 0 0 1-.25-1.23c.023-.419.163-.832.425-1.196.253-.356.58-.642.949-.82Z"></path>
                  </svg>
                  <div className="text-left">
                    <p className="font-semibold text-foreground">Apple ID</p>
                    <p className="text-sm text-muted-foreground">
                      Connect your Apple account
                    </p>
                  </div>
                </div>
                {connectedAccounts.apple ? (
                  <CheckCircle className="h-6 w-6 text-green-600" />
                ) : (
                  <ArrowRight className="h-5 w-5 text-muted-foreground" />
                )}
              </button>
            </div>

            {/* Outlook */}
            <div className="relative">
              <button
                onClick={() => handleConnect("outlook")}
                disabled={connectedAccounts.outlook || loading}
                className={`w-full flex items-center justify-between p-4 border rounded-lg transition-colors ${
                  connectedAccounts.outlook
                    ? "border-green-200 bg-green-50 cursor-default"
                    : "border-border bg-background hover:bg-accent cursor-pointer"
                }`}
              >
                <div className="flex items-center">
                  <svg
                    className="h-6 w-6 mr-3"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      d="M11.4 24H0V12.6h11.4V24zM24 24H12.6V12.6H24V24zM11.4 11.4H0V0h11.4v11.4zm12.6 0H12.6V0H24v11.4z"
                      fill="#00A4EF"
                    />
                  </svg>
                  <div className="text-left">
                    <p className="font-semibold text-foreground">Outlook</p>
                    <p className="text-sm text-muted-foreground">
                      Connect your Microsoft account
                    </p>
                  </div>
                </div>
                {connectedAccounts.outlook ? (
                  <CheckCircle className="h-6 w-6 text-green-600" />
                ) : (
                  <ArrowRight className="h-5 w-5 text-muted-foreground" />
                )}
              </button>
            </div>
          </div>

          <div className="mt-8">
            {allConnected && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-800 font-medium">
                  🎉 All accounts connected! You're ready to go.
                </p>
              </div>
            )}

            <button
              onClick={handleContinue}
              disabled={!someConnected}
              className={`w-full flex justify-center items-center py-3 px-4 text-sm font-semibold rounded-lg transition-colors ${
                someConnected
                  ? "bg-gray-900 text-white hover:bg-gray-800"
                  : "bg-gray-100 text-gray-500 cursor-not-allowed"
              }`}
            >
              {someConnected ? "Continue" : "Select an account to continue"}
            </button>
          </div>

          <p className="mt-4 text-center text-sm text-muted-foreground">
            You can always connect more accounts later in{" "}
            <Link
              to="/"
              className="font-semibold text-primary hover:text-primary/80 transition-colors"
            >
              Settings
            </Link>
          </p>
        </div>
      </div>

      <div className="relative hidden w-0 flex-1 lg:block overflow-hidden bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-indigo-500/10 to-purple-500/10"></div>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center p-8 relative z-10">
            <div className="mb-6">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-white/20 backdrop-blur-sm rounded-full mb-4">
                <svg
                  className="w-8 h-8 text-indigo-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                  />
                </svg>
              </div>
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-3">
              Connect & Sync
            </h2>
            <p className="text-lg text-gray-600 max-w-md mx-auto">
              Seamlessly integrate all your email accounts in one unified inbox
              powered by AI.
            </p>
          </div>
        </div>
        <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-blue-400 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-pulse"></div>
        <div className="absolute top-1/2 right-1/4 w-72 h-72 bg-indigo-400 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-pulse animation-delay-2000"></div>
        <div className="absolute bottom-1/4 left-1/2 w-72 h-72 bg-purple-400 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-pulse animation-delay-4000"></div>
      </div>
    </div>
  );
};

export default AuthConnect;
