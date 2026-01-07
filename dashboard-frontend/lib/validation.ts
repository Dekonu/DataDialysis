/**
 * Input validation utilities for frontend security
 */

/**
 * Sanitize string input to prevent XSS
 */
export function sanitizeString(input: string): string {
  return input
    .replace(/[<>]/g, '') // Remove angle brackets
    .trim()
    .slice(0, 1000); // Limit length
}

/**
 * Validate time range parameter
 */
export function validateTimeRange(value: unknown): value is '1h' | '24h' | '7d' | '30d' {
  return value === '1h' || value === '24h' || value === '7d' || value === '30d';
}

/**
 * Validate numeric query parameter
 */
export function validateNumericParam(
  value: unknown,
  min: number = 0,
  max: number = Number.MAX_SAFE_INTEGER
): number | null {
  if (typeof value === 'string') {
    const num = parseInt(value, 10);
    if (!isNaN(num) && num >= min && num <= max) {
      return num;
    }
  }
  return null;
}

/**
 * Validate and sanitize search query
 */
export function validateSearchQuery(value: unknown): string {
  if (typeof value !== 'string') {
    return '';
  }
  return sanitizeString(value);
}

/**
 * Validate date string (ISO format)
 */
export function validateDateString(value: unknown): string | null {
  if (typeof value !== 'string') {
    return null;
  }
  const date = new Date(value);
  if (isNaN(date.getTime())) {
    return null;
  }
  return date.toISOString();
}

/**
 * Validate severity level
 */
export function validateSeverity(value: unknown): 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL' | null {
  if (typeof value !== 'string') {
    return null;
  }
  const upper = value.toUpperCase();
  if (['INFO', 'WARNING', 'ERROR', 'CRITICAL'].includes(upper)) {
    return upper as 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  }
  return null;
}

