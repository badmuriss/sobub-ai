/**
 * Centralized Error Handler for SOBUB AI Frontend
 *
 * This module provides consistent error handling, logging, and user-friendly
 * error messages across the entire application.
 */

import { MESSAGES } from '../constants';

/**
 * Error severity levels
 */
export const ErrorSeverity = {
  INFO: 'info',
  WARNING: 'warning',
  ERROR: 'error',
  CRITICAL: 'critical',
};

/**
 * Error categories for better handling
 */
export const ErrorCategory = {
  NETWORK: 'network',
  VALIDATION: 'validation',
  PERMISSION: 'permission',
  FILE: 'file',
  AUDIO: 'audio',
  UNKNOWN: 'unknown',
};

/**
 * ErrorHandler class for centralized error management
 *
 * @typedef {Object} ErrorObject
 * @property {string} message - User-friendly error message
 * @property {Error|null} originalError - Original error object
 * @property {string} category - Error category from ErrorCategory enum
 * @property {string} severity - Error severity from ErrorSeverity enum
 * @property {string} context - Context where error occurred
 */
class ErrorHandler {
  constructor() {
    this.listeners = [];
    this.errorLog = [];
    this.maxLogSize = 100;
  }

  /**
   * Register an error listener to receive error notifications.
   *
   * IMPORTANT: You MUST call the returned cleanup function when the component unmounts
   * to prevent memory leaks!
   *
   * @param {function(ErrorObject): void} listener - Callback invoked when errors occur
   * @returns {function(): void} Cleanup function - MUST be called on component unmount
   *
   * @example
   * // In a React component
   * useEffect(() => {
   *   const cleanup = errorHandler.addListener((error) => {
   *     setError(error.message);
   *   });
   *
   *   return cleanup;  // ⚠️ CRITICAL: Clean up on unmount
   * }, []);
   */
  addListener(listener) {
    this.listeners.push(listener);

    // Return cleanup function
    return () => this.removeListener(listener);
  }

  /**
   * Remove an error listener (typically called automatically by cleanup function)
   *
   * @param {function(ErrorObject): void} listener - Callback to remove
   */
  removeListener(listener) {
    this.listeners = this.listeners.filter((l) => l !== listener);
  }

  /**
   * Notify all listeners of an error
   * @private
   */
  _notifyListeners(error) {
    this.listeners.forEach((listener) => {
      try {
        listener(error);
      } catch (e) {
        console.error('Error in error listener:', e);
      }
    });
  }

  /**
   * Log error to console and internal log
   * @private
   */
  _logError(error, context) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      message: error.message,
      category: error.category,
      severity: error.severity,
      context,
      stack: error.originalError?.stack,
    };

    // Log to console based on severity
    const consoleMethod = error.severity === ErrorSeverity.CRITICAL ? 'error' :
                         error.severity === ErrorSeverity.ERROR ? 'error' :
                         error.severity === ErrorSeverity.WARNING ? 'warn' : 'log';

    console[consoleMethod](`[${context}]:`, error.message, error.originalError || '');

    // Add to internal log
    this.errorLog.push(logEntry);
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog.shift();
    }
  }

  /**
   * Handle an error with context
   * @param {Error|string} error - Error object or message
   * @param {string} context - Where the error occurred
   * @param {ErrorCategory} category - Error category
   * @param {ErrorSeverity} severity - Error severity
   * @returns {string} - User-friendly error message
   */
  handle(error, context, category = ErrorCategory.UNKNOWN, severity = ErrorSeverity.ERROR) {
    const errorObj = {
      message: this.getUserMessage(error, category),
      originalError: error instanceof Error ? error : null,
      category,
      severity,
      context,
    };

    this._logError(errorObj, context);
    this._notifyListeners(errorObj);

    return errorObj.message;
  }

  /**
   * Get user-friendly error message
   * @private
   */
  getUserMessage(error, category) {
    // If error is a string, return it
    if (typeof error === 'string') {
      return error;
    }

    // Check for specific error messages
    const errorMessage = error.message || error.toString();

    // Network errors
    if (category === ErrorCategory.NETWORK || errorMessage.includes('fetch') || errorMessage.includes('network')) {
      if (errorMessage.includes('Failed to fetch')) {
        return MESSAGES.ERROR.CONNECTION_FAILED;
      }
      return `Network error: ${errorMessage}`;
    }

    // Permission errors
    if (category === ErrorCategory.PERMISSION || errorMessage.includes('permission') || errorMessage.includes('denied')) {
      if (errorMessage.toLowerCase().includes('microphone')) {
        return MESSAGES.ERROR.MICROPHONE_DENIED;
      }
      return `Permission denied: ${errorMessage}`;
    }

    // File errors
    if (category === ErrorCategory.FILE) {
      if (errorMessage.includes('size') || errorMessage.includes('large')) {
        return MESSAGES.ERROR.FILE_TOO_LARGE;
      }
      if (errorMessage.includes('type') || errorMessage.includes('format')) {
        return MESSAGES.ERROR.INVALID_FILE_TYPE;
      }
      return `File error: ${errorMessage}`;
    }

    // Audio errors
    if (category === ErrorCategory.AUDIO) {
      return MESSAGES.ERROR.MICROPHONE_ERROR;
    }

    // Validation errors
    if (category === ErrorCategory.VALIDATION) {
      return errorMessage; // Usually already user-friendly
    }

    // Default: return the error message
    return errorMessage || 'An unknown error occurred';
  }

  /**
   * Handle microphone access error
   */
  handleMicrophoneError(error, context = 'Microphone Access') {
    if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
      return this.handle(
        MESSAGES.ERROR.MICROPHONE_DENIED,
        context,
        ErrorCategory.PERMISSION,
        ErrorSeverity.WARNING
      );
    }

    if (error.name === 'NotFoundError') {
      return this.handle(
        'No microphone found. Please connect a microphone and try again.',
        context,
        ErrorCategory.AUDIO,
        ErrorSeverity.ERROR
      );
    }

    return this.handle(
      MESSAGES.ERROR.MICROPHONE_ERROR,
      context,
      ErrorCategory.AUDIO,
      ErrorSeverity.ERROR
    );
  }

  /**
   * Handle API error
   */
  handleApiError(error, operation, context = 'API') {
    const message = error.message || 'API request failed';
    const severity = error.status >= 500 ? ErrorSeverity.CRITICAL : ErrorSeverity.ERROR;

    return this.handle(
      `${operation} failed: ${message}`,
      context,
      ErrorCategory.NETWORK,
      severity
    );
  }

  /**
   * Handle file upload error
   */
  handleFileError(error, context = 'File Upload') {
    return this.handle(
      error,
      context,
      ErrorCategory.FILE,
      ErrorSeverity.ERROR
    );
  }

  /**
   * Handle validation error
   */
  handleValidationError(message, context = 'Validation') {
    return this.handle(
      message,
      context,
      ErrorCategory.VALIDATION,
      ErrorSeverity.WARNING
    );
  }

  /**
   * Get error log
   */
  getErrorLog() {
    return [...this.errorLog];
  }

  /**
   * Clear error log
   */
  clearErrorLog() {
    this.errorLog = [];
  }
}

// Export singleton instance
const errorHandler = new ErrorHandler();
export default errorHandler;

/**
 * Async error wrapper for handling errors in async functions
 * @param {Function} fn - Async function to wrap
 * @param {string} context - Context string for error logging
 * @param {ErrorCategory} category - Error category
 * @returns {Promise} - Wrapped promise
 */
export const asyncErrorHandler = async (fn, context, category = ErrorCategory.UNKNOWN) => {
  try {
    return await fn();
  } catch (error) {
    errorHandler.handle(error, context, category);
    throw error; // Re-throw so caller can handle it
  }
};

/**
 * React hook for error handling
 * @param {Function} callback - Callback to execute with error handling
 * @param {string} context - Context string
 * @param {ErrorCategory} category - Error category
 * @returns {Function} - Wrapped callback
 */
export const useErrorHandler = (callback, context, category = ErrorCategory.UNKNOWN) => {
  return async (...args) => {
    try {
      return await callback(...args);
    } catch (error) {
      errorHandler.handle(error, context, category);
      return null; // Return null instead of throwing
    }
  };
};
