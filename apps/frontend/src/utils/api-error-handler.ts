// src/utils/api-error-handler.ts
export interface ApiError {
  type: 'network' | 'authentication' | 'authorization' | 'not_found' | 'validation' | 'server' | 'rate_limit' | 'unknown'
  message: string
  userMessage: string
  timestamp: Date
  recoverable: boolean
  details: Record<string, unknown>
  code?: string
  status?: number
}

export function createApiError(
  errorMessage: string,
  status?: number,
  details?: Record<string, unknown>
): ApiError {
  // Handle rate limit errors specifically
  if (errorMessage === 'rate_limit_exceeded' || status === 429) {
    return {
      type: 'rate_limit',
      message: 'rate_limit_exceeded',
      userMessage: 'AI limit exceeded. Upgrade your plan to continue with AI-powered learning.',
      timestamp: new Date(),
      recoverable: false,
      details: details || {},
      code: '429',
      status: 429
    }
  }

  // Handle other error types
  let type: ApiError['type'] = 'unknown'
  let userMessage = 'An unexpected error occurred'

  if (status) {
    switch (status) {
      case 401:
        type = 'authentication'
        userMessage = 'Authentication required. Please login.'
        break
      case 403:
        type = 'authorization'
        userMessage = 'Access denied. Insufficient permissions.'
        break
      case 404:
        type = 'not_found'
        userMessage = 'Resource not found.'
        break
      case 400:
        type = 'validation'
        userMessage = 'Invalid request data.'
        break
      case 500:
        type = 'server'
        userMessage = 'Server error. Please try again later.'
        break
      default:
        if (status >= 500) {
          type = 'server'
          userMessage = 'Server error. Please try again later.'
        } else if (status >= 400) {
          type = 'validation'
          userMessage = 'Request error. Please check your input.'
        }
    }
  }

  // Check for network-related errors
  if (errorMessage.includes('Network') || errorMessage.includes('fetch')) {
    type = 'network'
    userMessage = 'Network connection failed. Please check your internet connection.'
  }

  return {
    type,
    message: errorMessage,
    userMessage,
    timestamp: new Date(),
    recoverable: type !== 'rate_limit' && type !== 'authorization',
    details: details || {},
    code: status?.toString(),
    status
  }
}

export function handleServiceError(
  error: string | object | null,
  status?: number
): ApiError | string {
  if (!error) {
    return 'Unknown error occurred'
  }

  if (typeof error === 'string') {
    return createApiError(error, status)
  }

  // If it's already a properly formatted error object, return as-is
  if (typeof error === 'object' && 'type' in error && 'message' in error) {
    return error as ApiError
  }

  return createApiError('Unknown error', status)
}