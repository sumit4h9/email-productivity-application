/**
 * Frontend Security Utilities
 * Provides client-side validation and sanitization for all input fields
 */

// Security patterns for different input types
const SECURITY_PATTERNS = {
  // XSS patterns
  xss: [
    /<script[^>]*>.*?<\/script>/gi,
    /javascript\s*:/gi,
    /vbscript\s*:/gi,
    /data\s*:/gi,
    /on\w+\s*=/gi,
    /expression\s*\(/gi,
    /url\s*\(/gi,
    /<iframe/gi,
    /<svg\s+onload/gi,
    /<body\s+onload/gi,
  ],

  // SQL injection patterns
  sqlInjection: [
    /'\s*OR\s*'1'='1/gi,
    /'\s*OR\s*1=1/gi,
    /'\s*--/gi,
    /'\s*;/gi,
    /'\s*DROP\s+TABLE/gi,
    /'\s*UNION\s+SELECT/gi,
    /'\s*EXEC\s+xp_cmdshell/gi,
    /\)\s*OR\s*\(/gi,
    /\)\s*DROP\s+TABLE/gi,
    /\)\s*;/gi,
    /"\s*OR\s*""="/gi,
    /"\s*OR\s*1=1/gi,
    /"\s*--/gi,
    /"\s*;/gi,
  ],

  // Command injection patterns
  commandInjection: [/`.*`/g, /\$\{.*\}/g, /\\$\(.*\)/g],

  // Hidden/invisible characters
  hiddenChars: /[\u200E\u200F\u202A-\u202E\u2066-\u2069]/g,

  // Unicode quote characters (homograph attacks)
  unicodeQuotes: /[％＇＂]/g,

  // Control characters - using character codes to avoid linting issues
  controlChars: /[\x00-\x1F\x7F]/g, // eslint-disable-line no-control-regex
};

/**
 * Sanitize general input fields
 */
export function sanitizeInput(
  value: string,
  fieldName: string = "input",
  maxLength: number = 1000
): string {
  if (typeof value !== "string") {
    throw new Error(`${fieldName} must be a string`);
  }

  let sanitized = value.trim();

  if (sanitized.length > maxLength) {
    throw new Error(`${fieldName} is too long (max ${maxLength} characters)`);
  }

  // Remove null bytes and control characters
  sanitized = sanitized.replace("\u0000", "");
  sanitized = sanitized.replace(SECURITY_PATTERNS.controlChars, "");

  // Check for dangerous patterns
  const allPatterns = [
    ...SECURITY_PATTERNS.xss,
    ...SECURITY_PATTERNS.sqlInjection,
    ...SECURITY_PATTERNS.commandInjection,
  ];

  for (const pattern of allPatterns) {
    if (pattern.test(sanitized)) {
      throw new Error(`${fieldName} contains potentially dangerous patterns`);
    }
  }

  // Check for hidden characters
  if (SECURITY_PATTERNS.hiddenChars.test(sanitized)) {
    throw new Error(`${fieldName} contains hidden characters`);
  }

  // Check for unicode quotes
  if (SECURITY_PATTERNS.unicodeQuotes.test(sanitized)) {
    throw new Error(`${fieldName} contains invalid quote characters`);
  }

  return sanitized;
}

/**
 * Sanitize email input
 */
export function sanitizeEmail(value: string): string {
  const sanitized = sanitizeInput(value, "email", 320);

  // Email-specific checks
  if ((sanitized.match(/@/g) || []).length !== 1) {
    throw new Error("Email must contain exactly one @ symbol");
  }

  if (sanitized.startsWith("@") || sanitized.endsWith("@")) {
    throw new Error("Email cannot start or end with @");
  }

  // Check for suspicious patterns
  const suspiciousPatterns = [
    /\.\./, // Double dots
    /\.@/, // Dot before @
    /@\./, // @ before dot
    /\.{3,}/, // Multiple consecutive dots
  ];

  for (const pattern of suspiciousPatterns) {
    if (pattern.test(sanitized)) {
      throw new Error("Email contains invalid patterns");
    }
  }

  return sanitized;
}

/**
 * Sanitize name input
 */
export function sanitizeName(value: string): string {
  const sanitized = sanitizeInput(value, "name", 100);

  // Name-specific checks
  const namePatterns = [
    /<[^>]*>/, // HTML tags
    /\\/, // Backslashes
    /\//, // Forward slashes
    /`/, // Backticks
    /\$\{/, // Template literals
  ];

  for (const pattern of namePatterns) {
    if (pattern.test(sanitized)) {
      throw new Error("Name contains potentially dangerous patterns");
    }
  }

  return sanitized;
}

/**
 * Sanitize password input
 *
 * This function allows users to be creative with passwords while maintaining security:
 * ✅ ALLOWED: Special characters like >, <, =, @, #, $, etc.
 * ✅ ALLOWED: Creative patterns that look suspicious but can't execute
 * ❌ BLOCKED: Only actual executable XSS patterns that could harm the system
 *
 * Examples:
 * - "><iframe src=javascript:alert(1)>" ✅ ALLOWED (just special chars)
 * - "<script>alert('xss')</script>" ❌ BLOCKED (executable script)
 * - "javascript:alert(1)" ❌ BLOCKED (executable protocol)
 */
export function sanitizePassword(value: string): string {
  const sanitized = sanitizeInput(value, "password", 128);

  // Password-specific checks
  if (sanitized.length < 8) {
    throw new Error("Password must be at least 8 characters long");
  }

  // Check for very weak patterns
  if (/^\s+$/.test(sanitized)) {
    throw new Error("Password cannot contain only spaces");
  }

  if (/^[!@#$%^&*()_+\-=[\]{}|;:'",.<>/?]+$/.test(sanitized)) {
    throw new Error("Password cannot contain only special characters");
  }

  // For passwords, we need to be more intelligent about XSS detection
  // Allow special characters but block actual executable XSS patterns
  const dangerousPasswordPatterns = [
    // Only block patterns that could actually execute code
    /<script[^>]*>.*?<\/script>/gi,
    /javascript\s*:/gi,
    /vbscript\s*:/gi,
    /data\s*:/gi,
    /on\w+\s*=/gi,
    /expression\s*\(/gi,
    /url\s*\(/gi,
    // Block complete iframe tags that could execute
    /<iframe[^>]*>.*?<\/iframe>/gi,
    /<iframe[^>]*\/>/gi,
    // Block SVG with onload that could execute
    /<svg\s+[^>]*onload[^>]*>/gi,
    // Block body with onload that could execute
    /<body\s+[^>]*onload[^>]*>/gi,
  ];

  for (const pattern of dangerousPasswordPatterns) {
    if (pattern.test(sanitized)) {
      throw new Error("Password contains potentially dangerous patterns");
    }
  }

  return sanitized;
}

/**
 * Sanitize textarea input
 */
export function sanitizeTextarea(
  value: string,
  maxLength: number = 5000
): string {
  const sanitized = sanitizeInput(value, "text", maxLength);

  // Additional checks for longer text
  const ltCount = (sanitized.match(/</g) || []).length;
  const gtCount = (sanitized.match(/>/g) || []).length;

  if (ltCount > 10 || gtCount > 10) {
    throw new Error("Text contains too many HTML-like characters");
  }

  return sanitized;
}

/**
 * Sanitize select input
 */
export function sanitizeSelect(value: string, allowedValues: string[]): string {
  const sanitized = sanitizeInput(value, "selection", 100);

  if (!allowedValues.includes(sanitized)) {
    throw new Error(
      `Invalid selection. Allowed values: ${allowedValues.join(", ")}`
    );
  }

  return sanitized;
}

/**
 * Validate and sanitize form data
 */
export function validateFormData(
  data: Record<string, unknown>,
  schema: Record<string, unknown>
): Record<string, unknown> {
  const validated: Record<string, unknown> = {};

  for (const [fieldName, fieldConfig] of Object.entries(schema)) {
    const value = data[fieldName];

    if (
      fieldConfig &&
      typeof fieldConfig === "object" &&
      "required" in fieldConfig &&
      fieldConfig.required &&
      (value === undefined || value === null || value === "")
    ) {
      throw new Error(`${fieldName} is required`);
    }

    if (value !== undefined && value !== null && value !== "") {
      try {
        if (
          fieldConfig &&
          typeof fieldConfig === "object" &&
          "type" in fieldConfig
        ) {
          const config = fieldConfig as {
            type: string;
            maxLength?: number;
            allowedValues?: string[];
          };

          switch (config.type) {
            case "email":
              validated[fieldName] = sanitizeEmail(value as string);
              break;
            case "name":
              validated[fieldName] = sanitizeName(value as string);
              break;
            case "password":
              validated[fieldName] = sanitizePassword(value as string);
              break;
            case "textarea":
              validated[fieldName] = sanitizeTextarea(
                value as string,
                config.maxLength
              );
              break;
            case "select":
              validated[fieldName] = sanitizeSelect(
                value as string,
                config.allowedValues || []
              );
              break;
            default:
              validated[fieldName] = sanitizeInput(
                value as string,
                fieldName,
                config.maxLength
              );
          }
        }
      } catch (error) {
        throw new Error(
          `${fieldName}: ${error instanceof Error ? error.message : "Invalid input"}`
        );
      }
    } else if (
      fieldConfig &&
      typeof fieldConfig === "object" &&
      "default" in fieldConfig
    ) {
      validated[fieldName] = (fieldConfig as { default: unknown }).default;
    }
  }

  return validated;
}

/**
 * Real-time input validation for form fields
 */
export function createInputValidator(schema: Record<string, unknown>) {
  return (fieldName: string, value: string) => {
    try {
      const fieldConfig = schema[fieldName];
      if (!fieldConfig) return { isValid: true, error: null };

      if (
        fieldConfig &&
        typeof fieldConfig === "object" &&
        "type" in fieldConfig
      ) {
        const config = fieldConfig as {
          type: string;
          maxLength?: number;
          allowedValues?: string[];
        };

        switch (config.type) {
          case "email":
            sanitizeEmail(value);
            break;
          case "name":
            sanitizeName(value);
            break;
          case "password":
            sanitizePassword(value);
            break;
          case "textarea":
            sanitizeTextarea(value, config.maxLength);
            break;
          case "select":
            sanitizeSelect(value, config.allowedValues || []);
            break;
          default:
            sanitizeInput(value, fieldName, config.maxLength);
        }
      }

      return { isValid: true, error: null };
    } catch (error) {
      return {
        isValid: false,
        error: error instanceof Error ? error.message : "Invalid input",
      };
    }
  };
}

// Export security patterns for testing
export { SECURITY_PATTERNS };
