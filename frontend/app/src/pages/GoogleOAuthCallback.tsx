import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { AxiosError } from "axios";
import { oauthAPI } from "../lib/api";

const GoogleOAuthCallback = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading"
  );
  const [message, setMessage] = useState("");

  useEffect(() => {
    const handleOAuthCallback = async () => {
      try {
        // Extract the authorization code from URL query parameters
        const code = searchParams.get("code");

        if (!code) {
          setStatus("error");
          setMessage("No authorization code found in URL");
          return;
        }

        // Send the code to the backend to complete OAuth flow
        const response = await oauthAPI.googleCallback(code);

        setStatus("success");
        setMessage(response.message);

        // Redirect to dashboard after a short delay
        setTimeout(() => {
          navigate("/dashboard");
        }, 2000);
      } catch (error: unknown) {
        console.error("OAuth callback failed:", error);
        setStatus("error");
        if (error instanceof AxiosError) {
          setMessage(
            error.response?.data?.detail ||
              "Failed to connect Google account. Please try again."
          );
        } else {
          setMessage("Failed to connect Google account. Please try again.");
        }
      }
    };

    handleOAuthCallback();
  }, [searchParams, navigate]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow-lg">
        <div className="text-center">
          {status === "loading" && (
            <>
              <Loader2 className="mx-auto h-12 w-12 animate-spin text-blue-600" />
              <h2 className="mt-4 text-xl font-semibold text-gray-900">
                Connecting your Google account...
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                Please wait while we complete the connection.
              </p>
            </>
          )}

          {status === "success" && (
            <>
              <CheckCircle className="mx-auto h-12 w-12 text-green-600" />
              <h2 className="mt-4 text-xl font-semibold text-gray-900">
                Account Connected Successfully!
              </h2>
              <p className="mt-2 text-sm text-gray-600">{message}</p>
              <p className="mt-4 text-sm text-gray-500">
                Redirecting to dashboard...
              </p>
            </>
          )}

          {status === "error" && (
            <>
              <AlertCircle className="mx-auto h-12 w-12 text-red-600" />
              <h2 className="mt-4 text-xl font-semibold text-gray-900">
                Connection Failed
              </h2>
              <p className="mt-2 text-sm text-gray-600">{message}</p>
              <button
                onClick={() => navigate("/add-account")}
                className="mt-4 w-full rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Try Again
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default GoogleOAuthCallback;
