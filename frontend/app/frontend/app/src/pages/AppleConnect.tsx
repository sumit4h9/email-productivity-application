import { useState } from "react";
import { useNavigate } from "react-router-dom";

const AppleConnect = () => {
  const navigate = useNavigate();
  const [isConnecting, setIsConnecting] = useState(false);

  const handleConnect = async () => {
    setIsConnecting(true);
    try {
      // Apple authentication logic will go here
      console.log("Connecting to Apple...");
      // Simulating connection delay
      await new Promise(resolve => setTimeout(resolve, 2000));
      navigate("/dashboard");
    } catch (error) {
      console.error("Apple connection failed:", error);
    } finally {
      setIsConnecting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-6">
        <div className="text-center">
          <div className="flex justify-center mb-6">
            {/* Apple logo */}
            <div className="w-20 h-20 bg-black rounded-xl flex items-center justify-center">
              <svg
                className="w-12 h-12 text-white"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11" />
              </svg>
            </div>
          </div>
          <h2 className="text-3xl font-extrabold text-gray-900">
            Connect Apple Account
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Connect your Apple Mail account to use Axnore with your Apple email
            addresses
          </p>
        </div>

        <div className="mt-8">
          <button
            onClick={handleConnect}
            disabled={isConnecting}
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-sm text-sm font-medium text-white bg-black hover:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isConnecting ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Connecting to Apple...
              </>
            ) : (
              "Connect Apple Account"
            )}
          </button>
        </div>

        <div className="mt-6">
          <button
            onClick={() => navigate("/dashboard")}
            className="w-full flex justify-center py-3 px-4 border border-gray-300 rounded-xl shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black transition-colors"
          >
            Skip for now
          </button>
        </div>

        <div className="mt-6 text-center">
          <p className="text-xs text-gray-500">
            By connecting your account, you agree to our{" "}
            <a href="#" className="font-medium text-black hover:text-gray-900">
              Terms of Service
            </a>{" "}
            and{" "}
            <a href="#" className="font-medium text-black hover:text-gray-900">
              Privacy Policy
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default AppleConnect;
