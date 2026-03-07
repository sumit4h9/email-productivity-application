# Secure Authentication Backend

A comprehensive FastAPI authentication backend with enterprise-grade security features and edge case handling.

## 🛡️ Security Features

### Authentication & Authorization

- **JWT Token Management** with enhanced security claims
- **Token Rotation** - refresh tokens are invalidated after use
- **Token Blacklisting** with Redis for immediate revocation
- **Clock Skew Tolerance** to handle time synchronization issues
- **Constant-Time Authentication** to prevent timing attacks

### Input Validation & Sanitization

- **Pydantic Models** for request validation
- **Email Validation** using `email-validator` library (RFC compliant)
- **Password Strength Validation** using `zxcvbn` (Dropbox's password strength estimator)
- **Input Sanitization** to prevent XSS and injection attacks
- **Request Size Limits** to prevent DoS attacks

### Rate Limiting & Protection

- **Multi-Factor Rate Limiting** (IP + User Agent + Language)
- **Graceful Redis Degradation** - falls back to memory when Redis is unavailable
- **Endpoint-Specific Limits** (login: 5/5min, signup: 3/hour, refresh: 10/min)
- **Rate Limit Headers** with retry-after information

### Database Security

- **Database Transactions** with proper rollback handling
- **Race Condition Protection** for concurrent user registration
- **Connection Pool Management** with health checks
- **Database-Level Constraints** and indexes

### Monitoring & Logging

- **Sanitized Logging** - sensitive data is redacted
- **Audit Trail** - all requests and responses are logged
- **Health Checks** - comprehensive system status monitoring
- **Performance Metrics** - response times and error rates

## 🏗️ Architecture

```
backend/app/
├── api/
│   └── auth.py              # Enhanced authentication endpoints
├── core/
│   └── jwt.py               # JWT with Redis integration & graceful degradation
├── db/
│   ├── base.py              # SQLAlchemy base class
│   └── session.py           # Database session with transaction handling
├── middleware/
│   ├── audit.py             # Request/response logging
│   ├── auth.py              # Authentication middleware
│   ├── rate_limit.py        # Multi-factor rate limiting
│   └── security.py          # Security headers
├── models/
│   ├── session.py           # Session model
│   └── user.py              # User model with constraints
├── utils/
│   └── validation.py        # Input validation utilities
├── tests/
│   └── test_health.py      # Health check tests
├── main.py                  # FastAPI application with monitoring
└── requirements.txt         # Dependencies
```

## 🚀 Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**

   ```bash
   export DATABASE_URL="sqlite:///./test.db"
   export REDIS_URL="redis://localhost:6379/0"
   export JWT_SECRET_KEY="your-secure-secret-key"
   export CLOCK_SKEW_TOLERANCE="30"
   export CORS_ALLOWED_ORIGINS="http://localhost:3000"
   export ENVIRONMENT="development"
   ```

3. **Run the application:**

   ```bash
   uvicorn app.main:app --reload
   ```

## 📡 API Endpoints

### Authentication

- `POST /auth/signup` - User registration with validation
- `POST /auth/login` - User login with constant-time response
- `POST /auth/refresh` - Token refresh with rotation
- `GET /auth/me` - Get current user information
- `POST /auth/logout` - Logout with token revocation
- `POST /auth/logout-all` - Logout from all devices

### Monitoring

- `GET /health` - Enhanced health check with service status
- `GET /status` - Detailed system status for monitoring
- `POST /admin/cleanup` - Trigger cleanup operations

## 🔒 Edge Cases Handled

### Security Vulnerabilities

- ✅ **Timing Attacks** - Constant-time authentication responses
- ✅ **User Enumeration** - Same response time for valid/invalid users
- ✅ **Token Reuse** - Refresh tokens are invalidated after use
- ✅ **Race Conditions** - Database-level constraints and transaction handling
- ✅ **Redis Failures** - Graceful degradation to memory storage
- ✅ **Clock Skew** - Configurable tolerance for time differences
- ✅ **Input Validation** - Comprehensive request validation with Pydantic
- ✅ **Rate Limit Bypass** - Multi-factor rate limiting
- ✅ **Logging Security** - Sensitive data redaction
- ✅ **Database Failures** - Connection pooling and health checks

### Performance & Reliability

- ✅ **Connection Pooling** - Efficient database connection management
- ✅ **Memory Management** - Rate limit storage with size limits
- ✅ **Error Handling** - Comprehensive exception handling
- ✅ **Monitoring** - Health checks and performance metrics
- ✅ **Graceful Degradation** - System continues working when Redis is down

## 🧪 Testing

Run the test suite:

```bash
pytest tests/
```

## 📊 Monitoring

The application provides comprehensive monitoring endpoints:

- **Health Check**: `/health` - Overall system health
- **Status**: `/status` - Detailed service status
- **Metrics**: Rate limiting, database, and Redis metrics

## 🔧 Configuration

### Environment Variables

- `DATABASE_URL` - Database connection string
- `REDIS_URL` - Redis connection string
- `JWT_SECRET_KEY` - Secret key for JWT signing
- `CLOCK_SKEW_TOLERANCE` - JWT clock skew tolerance (seconds)
- `CORS_ALLOWED_ORIGINS` - Comma-separated list of allowed origins
- `ENVIRONMENT` - Environment (development/production)

### Rate Limiting Configuration

- Login: 5 attempts per 5 minutes
- Signup: 3 attempts per hour
- Refresh: 10 attempts per minute
- General: 100 requests per minute

### Password Strength Requirements

The application uses **zxcvbn** (Dropbox's password strength estimator) which:

- **Rejects passwords below "Good" strength** (score < 3)
- **Analyzes common patterns** like keyboard layouts, common words, and sequences
- **Provides detailed feedback** with specific suggestions for improvement
- **Considers real-world password analysis** from data breaches

**Password Strength Levels:**

- **0: Very Weak** - Rejected
- **1: Weak** - Rejected
- **2: Fair** - Rejected
- **3: Good** - Accepted ✅
- **4: Very Strong** - Accepted ✅

## 🚨 Production Considerations

1. **Use strong JWT secret keys**
2. **Enable HTTPS in production**
3. **Configure proper CORS origins**
4. **Set up Redis clustering for high availability**
5. **Use PostgreSQL for production database**
6. **Configure proper logging levels**
7. **Set up monitoring and alerting**
8. **Regular security audits and updates**
