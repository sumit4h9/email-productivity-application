# Routing Setup for Axnore Frontend

## Overview

This document explains the routing structure between the landing page, login, signup, and dashboard pages.

## Page Structure

### 1. Landing Page (`/`)

- **File**: `src/app/page.tsx`
- **Purpose**: Main marketing page with navigation to login/signup
- **Features**: Hero section, feature highlights, call-to-action buttons
- **Navigation**: Links to `/login` and `/signup`

### 2. Login Page (`/login`)

- **File**: `src/app/login/page.tsx`
- **Purpose**: User authentication
- **Features**: Email/password form, remember me checkbox, forgot password link
- **Navigation**: Back to home, link to signup
- **API**: Calls `/api/auth/login` endpoint
- **Redirect**: On success, redirects to `/dashboard`

### 3. Signup Page (`/signup`)

- **File**: `src/app/signup/page.tsx`
- **Purpose**: User registration
- **Features**: Full name, email, password, confirm password fields
- **Navigation**: Back to home, link to login
- **API**: Calls `/api/auth/signup` endpoint
- **Redirect**: On success, redirects to `/login` with success message

### 4. Dashboard Page (`/dashboard`)

- **File**: `src/app/dashboard/page.tsx`
- **Purpose**: Main application interface after login
- **Features**: Sidebar navigation, email management, AI assistant
- **Navigation**: Back to home, logout functionality

## API Routes

### 1. Login API (`/api/auth/login`)

- **File**: `src/app/api/auth/login/route.ts`
- **Purpose**: Proxy to backend authentication
- **Backend**: Forwards requests to `http://localhost:8000/login`

### 2. Signup API (`/api/auth/signup`)

- **File**: `src/app/api/auth/signup/route.ts`
- **Purpose**: Proxy to backend registration
- **Backend**: Forwards requests to `http://localhost:8000/signup`

## Environment Configuration

Create a `.env.local` file in the frontend/app directory:

```bash
BACKEND_URL=http://localhost:8000
```

## Navigation Flow

```
Landing Page (/)
    ├── Login (/login) → Dashboard (/dashboard)
    └── Signup (/signup) → Login (/login)
```

## Features

- **Responsive Design**: All pages work on mobile and desktop
- **Tailwind CSS**: Modern styling with CSS variables
- **Form Validation**: Client-side validation with error handling
- **Loading States**: Visual feedback during API calls
- **Error Handling**: User-friendly error messages
- **Token Storage**: JWT tokens stored in localStorage
- **Protected Routes**: Dashboard requires authentication

## Getting Started

1. Ensure the backend is running on `http://localhost:8000`
2. Set up the environment variables
3. Run the frontend development server:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

## Notes

- The backend currently has mock authentication (no real database)
- JWT tokens are stored in localStorage (consider more secure storage for production)
- All pages use the same design system and CSS variables
- Material Icons are replaced with emojis for simplicity
