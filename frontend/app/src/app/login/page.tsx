"use client";
import { useState, ChangeEvent, FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

interface LoginForm {
  email: string;
  password: string;
  rememberMe: boolean;
}

export default function LoginPage() {
  const [form, setForm] = useState<LoginForm>({
    email: "",
    password: "",
    rememberMe: false,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleChange = (
    e: ChangeEvent<HTMLInputElement | HTMLInputElement>
  ) => {
    const { name, type, value, checked } = e.target as HTMLInputElement;
    setForm({ ...form, [name]: type === "checkbox" ? checked : value });
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const backendUrl =
        import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
      const response = await fetch(`${backendUrl}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: form.email, password: form.password }),
      });

      if (response.ok) {
        const data = await response.json();
        // Store tokens in localStorage or secure storage
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);

        // Redirect to dashboard
        navigate("/dashboard");
      } else {
        const errorData = await response.json();
        setError(errorData.detail || "Login failed");
      }
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-[var(--bg-secondary)] text-[var(--text-primary)] min-h-screen flex">
      {/* Left Section */}
      <div className="flex flex-1 flex-col justify-center py-16 px-4 sm:px-6 lg:flex-none lg:px-20 xl:px-24">
        <div className="mx-auto w-full max-w-sm lg:w-96">
          {/* Back to Home Link */}
          <div className="mb-6">
            <Link
              to="/"
              className="inline-flex items-center text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              <span className="mr-2">←</span>
              Back to Home
            </Link>
          </div>

          <div className="flex items-center mb-8">
            <div className="w-12 h-12 bg-gray-900 rounded-full flex items-center justify-center mr-4">
              <span className="text-white text-3xl">∞</span>
            </div>
            <h1 className="text-3xl font-extrabold text-gray-900">Axnore</h1>
          </div>

          <h2 className="mt-6 text-5xl font-extrabold tracking-tighter text-gray-900">
            Sign in
          </h2>
          <p className="mt-4 text-lg text-[var(--text-secondary)]">
            Welcome back! Please enter your details.
          </p>

          {/* Form */}
          <form onSubmit={handleSubmit} className="mt-10 space-y-8">
            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            <div>
              <label className="block text-base font-bold text-gray-900">
                Email address
              </label>
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                placeholder="you@example.com"
                required
                className="mt-2 block w-full rounded-lg border border-gray-300 px-4 py-3 shadow-sm focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600 sm:text-base bg-[var(--bg-primary)]"
              />
            </div>

            <div>
              <label className="block text-base font-bold text-gray-900">
                Password
              </label>
              <input
                type="password"
                name="password"
                value={form.password}
                onChange={handleChange}
                placeholder="••••••••"
                required
                className="mt-2 block w-full rounded-lg border border-gray-300 px-4 py-3 shadow-sm focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600 sm:text-base bg-[var(--bg-primary)]"
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="rememberMe"
                  name="rememberMe"
                  type="checkbox"
                  checked={form.rememberMe}
                  onChange={handleChange}
                  className="h-4 w-4 rounded border-gray-300 text-[var(--accent-primary)] focus:ring-indigo-600"
                />
                <label
                  htmlFor="rememberMe"
                  className="ml-3 block text-base font-medium text-gray-800"
                >
                  Remember me
                </label>
              </div>
              <div className="text-base">
                <a
                  href="#"
                  className="font-semibold text-indigo-600 hover:text-indigo-500"
                >
                  Forgot your password?
                </a>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="flex w-full justify-center rounded-lg bg-gray-900 py-4 px-4 text-lg font-bold text-white shadow-sm hover:bg-gray-800 focus:ring-2 focus:ring-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <p className="mt-10 text-center text-base text-gray-600">
            Not a member?{" "}
            <Link
              className="font-semibold text-indigo-600 hover:text-indigo-500"
              to="/signup"
            >
              Start a 14 day free trial
            </Link>
          </p>
        </div>
      </div>

      {/* Right Section */}
      <div className="relative hidden w-0 flex-1 lg:block pattern-bg overflow-hidden">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-[800px] h-[800px] rounded-full bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 opacity-20 blur-[150px]"></div>
        </div>
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600 rounded-full mix-blend-multiply filter blur-2xl opacity-20 animate-blob"></div>
        <div className="absolute top-1/2 right-1/4 w-96 h-96 bg-purple-600 rounded-full mix-blend-multiply filter blur-2xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-1/4 left-1/2 w-96 h-96 bg-pink-600 rounded-full mix-blend-multiply filter blur-2xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>
    </div>
  );
}
