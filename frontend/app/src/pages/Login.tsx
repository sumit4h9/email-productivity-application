import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ErrorDisplay } from "@/components/ui/error-display";
import { useToast } from "@/hooks/use-toast";
import { Eye, EyeOff } from "lucide-react";
import { sanitizeEmail, sanitizePassword } from "@/lib/security";
import { validateEmail, validateUsername } from "@/lib/validation";
import { authAPI, LoginInitRequest } from "@/lib/api";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [identifierError, setIdentifierError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");

  const { toast } = useToast();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Basic validation
    const isEmail = email.includes("@");

    // Envelope: prevent malicious strings early
    const input = email.trim();
    if (!input || !password) {
      toast({
        title: "Validation Error",
        description: "Please fill in all fields.",
        variant: "destructive",
      });
      return;
    }

    // Identifier validation (email domain allowlist or username rules)
    if (isEmail) {
      const { isValid, message } = validateEmail(input);
      if (!isValid) {
        setError(message);
        setIdentifierError(message);
        return;
      }
    } else {
      const { isValid, message } = validateUsername(input);
      if (!isValid) {
        setError(message || "Invalid username");
        setIdentifierError(message || "Invalid username");
        return;
      }
    }

    // Client-side security validation
    try {
      if (isEmail) sanitizeEmail(input);
      sanitizePassword(password);
    } catch (securityError) {
      const errorMessage =
        securityError instanceof Error
          ? securityError.message
          : "Security validation failed";
      setError(`Security validation failed: ${errorMessage}`);
      toast({
        title: "Security Validation Failed",
        description: errorMessage,
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);

    try {
      const payload: LoginInitRequest = {
        email_or_username: isEmail ? sanitizeEmail(input) : input.toLowerCase(),
        password: sanitizePassword(password),
      };

      const response = await authAPI.loginInit(payload);

      // Show success message
      toast({
        title: "Verification Code Sent!",
        description: response.message,
        variant: "default",
      });

      // Navigate to verification page with state
      navigate("/verify-login", {
        state: {
          email_or_username: isEmail
            ? sanitizeEmail(input)
            : input.toLowerCase(),
          contact: response.contact,
          message: response.message,
        },
      });
    } catch (error) {
      console.error("Login init error:", error);

      if (error && typeof error === "object" && "response" in error) {
        const response = (
          error as {
            response?: { status?: number; data?: { detail?: unknown } };
          }
        ).response;

        if (response?.status === 422) {
          const detail = response.data?.detail;
          if (Array.isArray(detail)) {
            const errorMessages = detail
              .map(
                (error: { loc?: string[]; msg?: string }) =>
                  `${error.loc?.join(".") || "unknown"}: ${error.msg || "Unknown error"}`
              )
              .join(", ");
            setError(`Validation error: ${errorMessages}`);
          } else if (typeof detail === "string") {
            setError(detail);
          } else {
            setError("Please check your input and try again.");
          }
        } else if (response?.status === 400) {
          setError(
            typeof response.data?.detail === "string"
              ? response.data.detail
              : "Invalid request data"
          );
        } else {
          setError(
            typeof response?.data?.detail === "string"
              ? response.data.detail
              : "Login failed. Please try again."
          );
        }
      } else {
        setError("Login failed. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Left Side Form */}
      <div className="flex flex-1 flex-col justify-center py-4 px-4 sm:px-6 lg:flex-none lg:px-12 xl:px-16">
        <div className="mx-auto w-full max-w-sm lg:w-96">
          {/* Branding */}
          <div>
            <div className="flex items-center mb-3">
              <div className="w-8 h-8 bg-gray-900 rounded-full flex items-center justify-center mr-2">
                <span className="material-icons text-white text-xl">
                  all_inclusive
                </span>
              </div>
              <h1 className="text-xl font-extrabold text-gray-900">Axnore</h1>
            </div>
            <h2 className="mt-2 text-2xl font-extrabold tracking-tighter text-gray-900">
              Sign in
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Welcome back! Please enter your details.
            </p>
          </div>

          {/* Login Form */}
          <form className="mt-4 space-y-4" onSubmit={handleSubmit}>
            <div>
              <Label
                htmlFor="email"
                className="block text-sm font-semibold text-foreground"
              >
                Email or Username
              </Label>
              <div className="mt-1">
                <Input
                  id="email"
                  name="email"
                  type="text"
                  autoComplete="username"
                  required
                  placeholder="Email or username"
                  value={email}
                  onChange={e => {
                    setEmail(e.target.value);
                    setIdentifierError("");
                  }}
                  className={`block w-full appearance-none rounded-lg border px-3 py-1.5 placeholder-muted-foreground shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary text-sm bg-background text-foreground ${identifierError ? "border-red-500 focus:ring-red-500" : "border-input"}`}
                  aria-describedby="login-identifier-error"
                />
              </div>
            </div>

            <div className="space-y-1">
              <Label
                htmlFor="password"
                className="block text-sm font-semibold text-foreground"
              >
                Password
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="block w-full appearance-none rounded-lg border border-input px-3 py-1.5 pr-10 placeholder-muted-foreground shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary text-sm bg-background text-foreground"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 flex items-center pr-3"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5 text-muted-foreground hover:text-foreground transition-colors" />
                  ) : (
                    <Eye className="h-5 w-5 text-muted-foreground hover:text-foreground transition-colors" />
                  )}
                </button>
              </div>
            </div>

            {identifierError && (
              <p
                id="login-identifier-error"
                className="text-xs text-red-500 -mt-3"
              >
                {identifierError}
              </p>
            )}

            {/* Error Display */}
            <ErrorDisplay error={error} />

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  checked={rememberMe}
                  onChange={e => setRememberMe(e.target.checked)}
                  className="h-4 w-4 rounded border-border text-primary focus:ring-primary focus:ring-offset-2"
                />
                <Label
                  htmlFor="remember-me"
                  className="ml-2 block text-sm font-medium text-foreground"
                >
                  Remember me
                </Label>
              </div>
              <div className="text-sm">
                <Link
                  to="/forgot-password"
                  className="font-semibold text-primary hover:text-primary/80 transition-colors"
                >
                  Forgot your password?
                </Link>
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="flex w-full justify-center rounded-lg border border-transparent bg-gray-900 py-2 px-4 text-sm font-semibold text-white shadow-sm hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
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
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Signing in...
                  </>
                ) : (
                  "Sign in"
                )}
              </button>
            </div>
          </form>

          <p className="mt-2 text-center text-sm text-muted-foreground">
            Not a member?{" "}
            <Link
              to="/signup"
              className="font-semibold text-primary hover:text-primary/80 transition-colors"
            >
              Start a 14 day free trial
            </Link>
          </p>
        </div>
      </div>

      {/* Right Side Background */}
      <div className="relative hidden w-0 flex-1 lg:block pattern-bg overflow-hidden">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-[800px] h-[800px] rounded-full bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 opacity-20 blur-[150px]"></div>
        </div>
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600 rounded-full mix-blend-multiply filter blur-2xl opacity-20 animate-blob"></div>
        <div className="absolute top-1/2 right-1/4 w-96 h-96 bg-purple-600 rounded-full mix-blend-multiply filter blur-2xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-1/4 left-1/2 w-96 h-96 bg-pink-600 rounded-full mix-blend-multiply filter blur-2xl opacity-20 animate-blob animation-delay-4000"></div>

        {/* Hero Content */}
        <div className="absolute inset-0 flex items-center justify-center z-10">
          <div className="text-center p-8 max-w-md">
            <div className="mb-8">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-white/10 backdrop-blur-sm rounded-2xl mb-6 border border-white/20">
                <svg
                  className="w-10 h-10 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
              </div>
            </div>
            <h2 className="text-4xl font-bold text-white mb-4 text-shadow-lg">
              Welcome Back
            </h2>
            <p className="text-xl text-white/90 mb-8 text-shadow">
              Experience the future of email management with AI-powered
              intelligence
            </p>

            {/* Feature List */}
            <div className="space-y-4 text-left">
              <div className="flex items-center text-white/90">
                <div className="w-2 h-2 bg-white rounded-full mr-3"></div>
                <span className="text-sm">Smart email categorization</span>
              </div>
              <div className="flex items-center text-white/90">
                <div className="w-2 h-2 bg-white rounded-full mr-3"></div>
                <span className="text-sm">AI-powered responses</span>
              </div>
              <div className="flex items-center text-white/90">
                <div className="w-2 h-2 bg-white rounded-full mr-3"></div>
                <span className="text-sm">Unified inbox management</span>
              </div>
              <div className="flex items-center text-white/90">
                <div className="w-2 h-2 bg-white rounded-full mr-3"></div>
                <span className="text-sm">Advanced security features</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
