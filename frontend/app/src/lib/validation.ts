// List of explicitly allowed email domains
export const ALLOWED_EMAIL_DOMAINS = [
  // Google
  "gmail.com",

  // Apple Mail domains
  "icloud.com",
  "me.com",
  "mac.com",

  // Microsoft Mail domains
  "outlook.com",
  "hotmail.com",
  "live.com",
  "msn.com",
];

// List of restricted email domains
export const RESTRICTED_EMAIL_DOMAINS = [
  "yahoo.com",
  "protonmail.com",
  "zoho.com",
  "aol.com",
  "gmx.com",
  "yandex.com",
];

// List of valid top-level domains for business/education/government
export const VALID_TLD_PATTERNS = [
  // Generic TLDs
  /\.com$/,
  /\.org$/,
  /\.net$/,
  /\.edu$/,
  /\.gov$/,
  /\.mil$/,

  // Country code TLDs (examples)
  /\.uk$/,
  /\.us$/,
  /\.ca$/,
  /\.au$/,
  /\.in$/,
  /\.de$/,
  /\.fr$/,
  /\.jp$/,

  // Business specific
  /\.io$/,
  /\.co$/,
  /\.biz$/,
  /\.dev$/,
];

// Email validation
export const validateEmail = (
  email: string
): { isValid: boolean; message: string } => {
  // Convert to lowercase
  email = email.toLowerCase();

  // Check for common malicious patterns
  const maliciousPatterns = [
    /<script/i, // Script tags
    /javascript:/i, // JavaScript protocol
    /data:/i, // Data protocol
    /\\x[0-9a-f]{2}/i, // Hex encoded characters
    /\\u[0-9a-f]{4}/i, // Unicode encoded characters
    /\\n/, // Newline characters
    /\\r/, // Carriage returns
    /\\0/, // Null bytes
    /;/, // SQL injection basic pattern
    /--/, // SQL comment pattern
    /'/, // SQL string delimiter
    /\/\*/, // SQL comment start
    /\*\//, // SQL comment end
    /@@/, // SQL system variable prefix
    /\|\|/, // SQL concatenation
    /\$\{/, // Template injection
    /\{\{/, // Template injection
    /\}\}/, // Template injection
  ];

  // Check for malicious patterns
  for (const pattern of maliciousPatterns) {
    if (pattern.test(email)) {
      return {
        isValid: false,
        message: "Invalid email format",
      };
    }
  }

  // Basic email format validation
  const emailRegex =
    /^[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?@[a-z0-9.-]+\.[a-z]{2,}$/i;
  if (!emailRegex.test(email)) {
    return {
      isValid: false,
      message: "Invalid email format",
    };
  }

  // Extract domain
  const domain = email.split("@")[1].toLowerCase();

  // Check if domain is restricted
  if (RESTRICTED_EMAIL_DOMAINS.includes(domain)) {
    return {
      isValid: false,
      message:
        "Axnore only supports Gmail, Apple, Outlook, Microsoft, and business/education domains.",
    };
  }

  // Check if domain is explicitly allowed
  if (ALLOWED_EMAIL_DOMAINS.includes(domain)) {
    return { isValid: true, message: "" };
  }

  // Check if domain has a valid business/education TLD
  const hasSupportedTLD = VALID_TLD_PATTERNS.some(pattern =>
    pattern.test(domain)
  );
  if (!hasSupportedTLD) {
    return {
      isValid: false,
      message:
        "Axnore only supports Gmail, Apple, Outlook, Microsoft, and business/education domains.",
    };
  }

  return { isValid: true, message: "" };
};

// Username validation regex pattern
// - Only lowercase letters (a-z), numbers (0-9), dot (.), underscore (_), hyphen (-)
// - Cannot start or end with dot, underscore, or hyphen
// - No consecutive special characters
// - Length between 3 and 20 characters
export const USERNAME_PATTERN = /^[a-z0-9][a-z0-9._-]*[a-z0-9]$/;
export const USERNAME_MIN_LENGTH = 5;
export const USERNAME_MAX_LENGTH = 20;

export const validateUsername = (
  username: string
): { isValid: boolean; message: string } => {
  // Convert to lowercase
  username = username.toLowerCase();

  // Check length
  if (username.length < USERNAME_MIN_LENGTH) {
    return {
      isValid: false,
      message: `Username must be at least ${USERNAME_MIN_LENGTH} characters long`,
    };
  }
  if (username.length > USERNAME_MAX_LENGTH) {
    return {
      isValid: false,
      message: `Username cannot be longer than ${USERNAME_MAX_LENGTH} characters`,
    };
  }

  // Check for invalid characters
  if (/[^a-z0-9._-]/.test(username)) {
    return {
      isValid: false,
      message:
        "Username can only contain lowercase letters, numbers, dots, underscores, and hyphens",
    };
  }

  // Check for consecutive special characters
  if (/[._-]{2,}/.test(username)) {
    return {
      isValid: false,
      message:
        "Username cannot contain consecutive dots, underscores, or hyphens",
    };
  }

  // Check pattern (start/end with alphanumeric)
  if (!USERNAME_PATTERN.test(username)) {
    return {
      isValid: false,
      message: "Username must start and end with a letter or number",
    };
  }

  return { isValid: true, message: "" };
};

// Example test cases for email validation
export const EMAIL_TEST_CASES = {
  valid: [
    // Gmail
    "user@gmail.com",
    "yahoo123@gmail.com",
    "zoho.test@gmail.com",

    // Apple Mail
    "user@icloud.com",
    "test@me.com",
    "example@mac.com",

    // Microsoft Mail
    "user@outlook.com",
    "test@hotmail.com",
    "example@live.com",
    "user@msn.com",

    // Business/Education Domains
    "user@company.com",
    "admin@university.edu",
    "contact@nonprofit.org",
    "service@business.co.uk",
    "support@startup.io",
    "info@agency.gov",
    "user@tech.dev",
  ],
  invalid: [
    // Restricted Domains
    "user@yahoo.com",
    "test@protonmail.com",
    "example@zoho.com",
    "user@aol.com",
    "contact@gmx.com",
    "support@yandex.com",

    // Invalid TLDs
    "user@domain.invalid",
    "test@company.local",
    "example@service.internal",

    // Malformed Emails
    "user@domain",
    "@domain.com",
    "user@",
    "user.domain.com",
    "user@domain@com",
  ],
};

// Example valid usernames
export const VALID_USERNAME_EXAMPLES = [
  "john123",
  "jane.doe",
  "user_name",
  "dev-123",
  "alice25",
];

// Example invalid usernames
export const INVALID_USERNAME_EXAMPLES = [
  "user", // too short (now needs 5+ chars)
  "username#123", // invalid character #
  ".username", // starts with dot
  "username_", // ends with underscore
  "user..name", // consecutive dots
  "user@name", // invalid character @
  "USER NAME", // contains space
];

// Common weak passwords to block
const COMMON_PASSWORDS = [
  "password",
  "123456",
  "123456789",
  "qwerty",
  "abc123",
  "password123",
  "admin",
  "letmein",
  "welcome",
  "monkey",
  "1234567890",
  "password1",
  "qwerty123",
  "dragon",
  "master",
  "hello",
  "freedom",
  "whatever",
  "qazwsx",
  "trustno1",
  "654321",
  "jordan23",
  "harley",
  "password1",
  "1234",
  "robert",
  "matthew",
  "jordan",
  "asshole",
  "daniel",
  "andrew",
  "joshua",
  "michael",
  "charlie",
  "michelle",
  "jessica",
  "jennifer",
  "thomas",
  "anthony",
  "william",
  "david",
  "mark",
  "james",
  "christopher",
  "daniel",
  "paul",
  "steven",
  "kenneth",
  "joshua",
  "kevin",
  "brian",
  "george",
  "timothy",
  "ronald",
  "jason",
  "edward",
  "jeffrey",
  "ryan",
  "jacob",
  "gary",
  "nicholas",
  "eric",
  "jonathan",
  "stephen",
  "larry",
  "justin",
  "scott",
  "brandon",
  "benjamin",
  "samuel",
  "gregory",
  "frank",
  "raymond",
  "alexander",
  "patrick",
  "jack",
  "dennis",
  "jerry",
  "tyler",
  "aaron",
  "jose",
  "henry",
  "douglas",
  "adam",
  "peter",
  "nathan",
  "zachary",
  "walter",
  "kyle",
  "harold",
  "carl",
  "arthur",
  "gerald",
  "roger",
  "keith",
  "jeremy",
  "lawrence",
  "sean",
  "christian",
  "ethan",
  "austin",
  "joe",
  "albert",
  "jesse",
  "willie",
  "ralph",
  "mason",
  "roy",
  "eugene",
  "wayne",
  "louis",
  "philip",
  "bobby",
  "johnny",
  "billy",
  "noah",
  "alan",
  "howard",
  "juan",
  "arthur",
  "eugene",
  "ralph",
  "bobby",
  "johnny",
  "billy",
  "noah",
  "alan",
  "howard",
  "juan",
  "arthur",
  "eugene",
  "ralph",
  "bobby",
  "johnny",
];

// Password strength requirements
const PASSWORD_REQUIREMENTS = {
  minLength: 8,
  maxLength: 128,
  requireUppercase: true,
  requireLowercase: true,
  requireNumbers: true,
  requireSpecialChars: true,
  minSpecialChars: 1,
  maxConsecutiveChars: 3,
  maxRepeatingChars: 2,
};

// Calculate password strength score (0-100)
export const getPasswordStrength = (password: string): number => {
  let score = 0;

  // Length scoring
  if (password.length >= 8) score += 10;
  if (password.length >= 12) score += 10;
  if (password.length >= 16) score += 10;
  if (password.length >= 20) score += 10;

  // Character variety scoring
  if (/[a-z]/.test(password)) score += 10;
  if (/[A-Z]/.test(password)) score += 10;
  if (/[0-9]/.test(password)) score += 10;
  if (/[^A-Za-z0-9]/.test(password)) score += 10;

  // Complexity scoring
  const charTypes = [
    /[a-z]/.test(password),
    /[A-Z]/.test(password),
    /[0-9]/.test(password),
    /[^A-Za-z0-9]/.test(password),
  ];
  const typeCount = charTypes.filter(Boolean).length;
  score += typeCount * 5;

  // Penalty for common patterns
  if (/123/.test(password)) score -= 5;
  if (/abc/.test(password)) score -= 5;
  if (/qwe/.test(password)) score -= 5;
  if (/asd/.test(password)) score -= 5;

  // Penalty for repeated characters
  const repeatedChars = /(.)\1{2,}/.test(password);
  if (repeatedChars) score -= 10;

  // Penalty for keyboard patterns
  const keyboardPatterns = [/qwerty/i, /asdf/i, /zxcv/i, /123456/, /abcdef/i];
  if (keyboardPatterns.some(pattern => pattern.test(password))) {
    score -= 15;
  }

  return Math.max(0, Math.min(100, score));
};

// Get password strength category
export const getPasswordStrengthCategory = (score: number): string => {
  if (score < 30) return "Very Weak";
  if (score < 50) return "Weak";
  if (score < 70) return "Fair";
  if (score < 85) return "Good";
  return "Strong";
};

// Comprehensive password validation
export const validatePassword = (
  password: string
): {
  isValid: boolean;
  message: string;
  strength?: number;
  category?: string;
} => {
  // Basic checks
  if (!password || typeof password !== "string") {
    return {
      isValid: false,
      message: "Password is required",
    };
  }

  const trimmedPassword = password.trim();

  if (trimmedPassword.length < PASSWORD_REQUIREMENTS.minLength) {
    return {
      isValid: false,
      message: `Password must be at least ${PASSWORD_REQUIREMENTS.minLength} characters long`,
    };
  }

  if (trimmedPassword.length > PASSWORD_REQUIREMENTS.maxLength) {
    return {
      isValid: false,
      message: `Password cannot be longer than ${PASSWORD_REQUIREMENTS.maxLength} characters`,
    };
  }

  // Check for whitespace-only passwords
  if (/^\s+$/.test(trimmedPassword)) {
    return {
      isValid: false,
      message: "Password cannot contain only spaces",
    };
  }

  // Check for common passwords (case-insensitive)
  const lowerPassword = trimmedPassword.toLowerCase();
  if (COMMON_PASSWORDS.includes(lowerPassword)) {
    return {
      isValid: false,
      message:
        "This password is too common. Please choose a more unique password",
    };
  }

  // Check for very weak patterns
  if (/^[!@#$%^&*()_+\-=[\]{}|;:'",.<>/?]+$/.test(trimmedPassword)) {
    return {
      isValid: false,
      message: "Password cannot contain only special characters",
    };
  }

  if (/^[0-9]+$/.test(trimmedPassword)) {
    return {
      isValid: false,
      message: "Password cannot contain only numbers",
    };
  }

  if (/^[a-zA-Z]+$/.test(trimmedPassword)) {
    return {
      isValid: false,
      message: "Password must contain at least one number or special character",
    };
  }

  // Check for consecutive characters
  if (/(.)\1{3,}/.test(trimmedPassword)) {
    return {
      isValid: false,
      message:
        "Password cannot contain more than 3 consecutive identical characters",
    };
  }

  // Check for keyboard patterns
  const keyboardPatterns = [
    /qwerty/i,
    /asdf/i,
    /zxcv/i,
    /123456/,
    /abcdef/i,
    /qazwsx/i,
  ];
  if (keyboardPatterns.some(pattern => pattern.test(trimmedPassword))) {
    return {
      isValid: false,
      message: "Password cannot contain common keyboard patterns",
    };
  }

  // Check for sequential patterns
  if (
    /123|234|345|456|567|678|789|890|abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz/i.test(
      trimmedPassword
    )
  ) {
    return {
      isValid: false,
      message: "Password cannot contain sequential characters",
    };
  }

  // Calculate strength
  const strength = getPasswordStrength(trimmedPassword);
  const category = getPasswordStrengthCategory(strength);

  // Require minimum strength
  if (strength < 40) {
    return {
      isValid: false,
      message: `Password is too weak (${category}). Please use a combination of uppercase, lowercase, numbers, and special characters`,
      strength,
      category,
    };
  }

  return {
    isValid: true,
    message: "",
    strength,
    category,
  };
};
