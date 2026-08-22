"use client";
import { useState, ChangeEvent, FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

interface FormData {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export default function SignUpPage() {
  const [form, setForm] = useState<FormData>({
    fullName: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match");
      setIsLoading(false);
      return;
    }

    try {
      const backendUrl =
        import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
      const response = await fetch(`${backendUrl}/auth/signup`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: form.email,
          password: form.password,
          name: form.fullName,
        }),
      });

      if (response.ok) {
        // Redirect to login page after successful signup
        navigate("/login?message=Account created successfully");
      } else {
        const errorData = await response.json();
        setError(errorData.detail || "Signup failed");
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
      <div className="flex flex-1 flex-col justify-center py-12 px-4 sm:px-6 lg:flex-none lg:px-20 xl:px-24">
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
            Create account
          </h2>
          <p className="mt-4 text-lg text-[var(--text-secondary)]">
            Start your journey with us today.
          </p>

          {/* Form */}
          <form onSubmit={handleSubmit} className="mt-6 space-y-6">
            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            <div>
              <label className="block text-base font-bold text-gray-900">
                Full name
              </label>
              <input
                type="text"
                name="fullName"
                value={form.fullName}
                onChange={handleChange}
                placeholder="John Doe"
                required
                className="mt-2 block w-full rounded-lg border border-gray-300 px-4 py-3 shadow-sm focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600 sm:text-base bg-[var(--bg-primary)]"
              />
            </div>

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

            <div>
              <label className="block text-base font-bold text-gray-900">
                Confirm password
              </label>
              <input
                type="password"
                name="confirmPassword"
                value={form.confirmPassword}
                onChange={handleChange}
                placeholder="••••••••"
                required
                className="mt-2 block w-full rounded-lg border border-gray-300 px-4 py-3 shadow-sm focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600 sm:text-base bg-[var(--bg-primary)]"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="flex w-full justify-center rounded-lg bg-gray-900 py-4 px-4 text-lg font-bold text-white shadow-sm hover:bg-gray-800 focus:ring-2 focus:ring-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? "Creating account..." : "Sign up"}
            </button>
          </form>

          <p className="mt-8 text-center text-base text-gray-600">
            Already have an account?{" "}
            <Link
              className="font-semibold text-indigo-600 hover:text-indigo-500"
              to="/login"
            >
              Log in
            </Link>
          </p>
        </div>
      </div>

      {/* Right Section */}
      <div className="relative hidden w-0 flex-1 lg:block pattern-bg overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/30 via-slate-900/50 to-purple-900/30"></div>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-white text-center p-8 relative z-10">
            <h2 className="text-5xl font-black tracking-tighter mb-4 text-shadow">
              Unlock the Future of Email
            </h2>
            <p className="text-xl text-slate-200 max-w-md mx-auto text-shadow">
              Harnessing AI to revolutionize your inbox. Experience unparalleled
              efficiency and intelligence.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
