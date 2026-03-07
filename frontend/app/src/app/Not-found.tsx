import { useLocation } from "react-router-dom";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error(
      "404 Error: User attempted to access non-existent route:",
      location.pathname
    );
  }, [location.pathname]);

  return (
    <div className="flex h-screen w-full items-center justify-center bg-[hsl(var(--bg-secondary))] text-[hsl(var(--text-primary))]">
      <div className="text-center p-8 max-w-lg mx-auto relative">
        <div className="relative inline-block">
          <h1 className="text-9xl font-bold text-[hsl(var(--accent-primary))]">
            404
          </h1>
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center w-full">
            <span className="material-icons text-7xl text-[hsl(var(--accent-primary))] opacity-10">
              question_mark
            </span>
          </div>
        </div>

        <h2 className="mt-4 text-3xl font-extrabold tracking-tight text-[hsl(var(--text-primary))] sm:text-4xl">
          Page Not Found
        </h2>

        <p className="mt-4 text-base text-[hsl(var(--text-secondary))]">
          Oops! It seems you've ventured into uncharted territory. The page you
          are looking for does not exist or has been moved.
        </p>

        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button
            asChild
            className="flex items-center justify-center w-full sm:w-auto px-6 py-3 text-sm font-medium text-[hsl(var(--accent-text))] bg-[hsl(var(--accent-primary))] hover:bg-[hsl(var(--accent-primary-hover))] rounded-lg shadow-md transition-colors duration-200"
          >
            <a href="/">
              <span className="material-icons mr-2">home</span>
              Go to Homepage
            </a>
          </Button>

          <Button
            variant="outline"
            asChild
            className="flex items-center justify-center w-full sm:w-auto px-6 py-3 text-sm font-medium text-[hsl(var(--text-primary))] bg-[hsl(var(--bg-primary))] border border-[hsl(var(--border-primary))] hover:bg-[hsl(var(--bg-secondary))] rounded-lg shadow-sm transition-colors duration-200"
          >
            <a href="/dashboard">
              <span className="material-icons mr-2">dashboard</span>
              Back to Dashboard
            </a>
          </Button>
        </div>

        <div className="mt-12 text-sm text-[hsl(var(--text-secondary))] text-center">
          <p>
            If you believe this is an error, please{" "}
            <a
              href="#"
              className="font-medium text-[hsl(var(--accent-primary))] hover:underline"
            >
              contact support
            </a>
            .
          </p>
        </div>

        <div className="relative mt-8 flex items-center justify-center space-x-2">
          <div className="w-6 h-6 bg-[hsl(var(--accent-primary))] rounded-full flex items-center justify-center">
            <span className="material-icons text-base text-[hsl(var(--accent-text))]">
              all_inclusive
            </span>
          </div>
          <span className="text-sm font-semibold text-[hsl(var(--text-secondary))]">
            Axnore Mail
          </span>
        </div>
      </div>
    </div>
  );
};

export default NotFound;
