import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ErrorDisplay } from "@/components/ui/error-display";
import { useForgotPassword } from "@/hooks/useAuthHooks";
import { useToast } from "@/hooks/use-toast";
import { sanitizeEmail } from "@/lib/security";
import { validateEmail } from "@/lib/validation";

const ForgotPassword = () => {
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState("");
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isDisabled, setIsDisabled] = useState(false);
  const [timeLeft, setTimeLeft] = useState(60);

  const forgotPasswordMutation = useForgotPassword();
  const { toast } = useToast();

  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (isDisabled && timeLeft > 0) {
      interval = setInterval(() => {
        setTimeLeft(prev => prev - 1);
      }, 1000);
    } else if (timeLeft === 0) {
      setIsDisabled(false);
      setTimeLeft(60);
    }

    return () => clearInterval(interval);
  }, [isDisabled, timeLeft]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setEmailError("");

    // Basic validation
    if (!email.trim()) {
      setEmailError("Email is required");
      return;
    }

    // Sanitize and validate email
    try {
      const sanitizedEmail = sanitizeEmail(email.trim());
      const { isValid, message } = validateEmail(sanitizedEmail);

      if (!isValid) {
        setEmailError(message);
        return;
      }

      // Submit to backend
      await forgotPasswordMutation.mutateAsync({ email: sanitizedEmail });

      setIsSubmitted(true);
      setIsDisabled(true);
    } catch (error) {
      // Error handling is done in the mutation hook
      console.error("Forgot password error:", error);
    }
  };

  return (
    <div className="flex min-h-screen">
      <div className="flex flex-1 flex-col justify-center py-8 px-4 sm:px-6 lg:flex-none lg:px-16 xl:px-20">
        <div className="mx-auto w-full max-w-sm lg:w-96">
          <div>
            <div className="flex items-center mb-6">
              <div className="w-10 h-10 bg-gray-900 rounded-full flex items-center justify-center mr-3">
                <span className="material-icons text-white text-2xl">
                  all_infinite
                </span>
              </div>
              <h1 className="text-2xl font-extrabold text-gray-900">Axnore</h1>
            </div>
            <h2 className="mt-4 text-3xl font-extrabold tracking-tighter text-gray-900">
              Reset Password
            </h2>
            <p className="mt-2 text-base text-gray-600">
              Enter your email address and we'll send you a link to reset your
              password.
            </p>
          </div>

          <div className="mt-6">
            <div className="mt-4">
              {isSubmitted && (
                <div className="rounded-lg bg-green-100 p-3 mb-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <span className="material-icons text-green-500">
                        check_circle
                      </span>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-bold text-green-800">
                        Reset Link Sent!
                      </h3>
                      <div className="mt-1 text-xs text-green-700">
                        <p>
                          A password reset link has been sent to your email
                          address. Please check your inbox (and spam folder) and
                          follow the instructions to reset your password.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <form className="space-y-4" onSubmit={handleSubmit}>
                <div>
                  <Label
                    htmlFor="email"
                    className="block text-sm font-semibold text-gray-900"
                  >
                    Email address
                  </Label>
                  <div className="mt-1">
                    <Input
                      id="email"
                      name="email"
                      type="email"
                      autoComplete="email"
                      placeholder="you@example.com"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      className={
                        emailError
                          ? "border-red-500 focus:border-red-500 focus:ring-red-500"
                          : ""
                      }
                      disabled={forgotPasswordMutation.isPending}
                    />
                    {emailError && <ErrorDisplay message={emailError} />}
                  </div>
                </div>

                <div>
                  <button
                    className={`flex w-full justify-center rounded-lg border border-transparent py-2.5 px-4 text-base font-semibold text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:ring-offset-2 ${
                      isDisabled || forgotPasswordMutation.isPending
                        ? "bg-gray-400 cursor-not-allowed"
                        : "bg-gray-900 hover:bg-gray-800"
                    }`}
                    disabled={isDisabled || forgotPasswordMutation.isPending}
                    type="submit"
                  >
                    {forgotPasswordMutation.isPending
                      ? "Sending..."
                      : isDisabled
                        ? "Link Sent"
                        : "Send Reset Link"}
                  </button>

                  {isDisabled && (
                    <div className="text-center mt-3 text-sm text-gray-600">
                      Request another link in{" "}
                      <span className="font-bold text-gray-900">
                        {timeLeft}
                      </span>
                      s
                    </div>
                  )}
                </div>
              </form>
            </div>
          </div>

          <p className="mt-6 text-center text-sm text-gray-600">
            Remember your password?{" "}
            <Link
              className="font-semibold text-indigo-600 hover:text-indigo-500"
              to="/login"
            >
              Return to log in
            </Link>
          </p>
        </div>
      </div>

      <div className="relative hidden w-0 flex-1 lg:block pattern-bg overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/30 via-slate-900/50 to-purple-900/30"></div>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-white text-center p-8 relative z-10">
            <h2 className="text-4xl font-black tracking-tighter mb-3 text-shadow">
              Secure Your Access
            </h2>
            <p className="text-lg text-slate-200 max-w-md mx-auto text-shadow">
              Regain access to your AI-powered dashboard quickly and securely.
              Your productivity is our priority.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;
