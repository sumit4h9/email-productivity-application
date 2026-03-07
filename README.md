# MY-APP

## Project Structure

- `frontend/` - Frontend application code
- `backend/` - Backend application code
- `ml/` - Machine learning models and scripts
- `scripts/` - Utility scripts
- `docker/` - Docker configurations
- `infra/` - Infrastructure as code
- `.github/workflows/` - GitHub Actions workflows

## Getting Started

Add your project description and setup instructions here.

## Features

### Automatic Token Refresh

The backend includes a robust automatic token refresh system that provides:

- **Silent token rotation**: Access tokens are automatically refreshed when they're near expiry
- **Middleware-based refresh**: Server-side middleware handles token refresh transparently
- **Client-side utilities**: Helper classes for managing tokens in client applications
- **Header-based communication**: New tokens are communicated via response headers

#### Quick Start

```python
from app.utils.token_utils import TokenManager

# Initialize token manager
token_manager = TokenManager(
    api_base_url="http://localhost:8000",
    access_token="your_access_token",
    refresh_token="your_refresh_token"
)

# Automatic refresh when needed
if token_manager.is_access_token_expiring_soon():
    token_manager.refresh_tokens()

# Use for API calls
headers = token_manager.get_auth_headers()
```

#### Automatic Refresh Loop

```python
from app.utils.token_utils import create_token_refresh_loop

# Create token manager with automatic refresh
token_manager = create_token_refresh_loop(
    api_base_url="http://localhost:8000",
    access_token="your_access_token",
    refresh_token="your_refresh_token",
    check_interval=30  # Check every 30 seconds
)
```

For detailed documentation, see [backend/AUTO_REFRESH_GUIDE.md](backend/AUTO_REFRESH_GUIDE.md).

## Development

a

### Code Formatting & Linting

This project uses ESLint and Prettier for JavaScript/TypeScript, and Black + isort + flake8 for Python.

#### Frontend (JavaScript/TypeScript)

```bash
cd frontend/app

# Format code
npm run format

# Check formatting
npm run format:check

# Lint code
npm run lint

# Fix linting issues
npm run lint:fix
```

#### Backend/ML (Python)

```bash
# Format backend
cd backend/app
black .
isort .

# Format ML service
cd ml
black .
isort .

# Check formatting
black --check .
isort --check-only .
flake8 .
```

#### Format All (PowerShell)

```powershell
# Format all code
.\scripts\format-all.ps1

# Check all formatting
.\scripts\format-check.ps1
```

### VS Code Setup

Install recommended extensions:

- Prettier - Code formatter
- ESLint
- Tailwind CSS IntelliSense

The project includes VS Code settings for automatic formatting on save.

### Docker Development

```bash
# Start with live reloading
docker compose -f infra/docker-compose.yml up --build

# Production build
docker compose -f docker/docker-compose.yaml up --build
```

### Testing

```bash
# Run backend tests
cd backend/app
pytest

# Run specific test file
pytest tests/test_auto_refresh.py
```

# download postgressql
