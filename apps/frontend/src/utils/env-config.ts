// src/utils/env-config.ts
// Centralized environment configuration utility

export const ENV_CONFIG = {
  // Mock data control
  USE_MOCK_DATA: process.env.NEXT_PUBLIC_USE_MOCK_DATA === 'true',
  
  // API Configuration
  API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000',
  
  // Development flags
  IS_DEVELOPMENT: process.env.NODE_ENV === 'development',
  IS_PRODUCTION: process.env.NODE_ENV === 'production',
} as const

// Helper functions for environment checks
export function shouldUseMockData(): boolean {
  const envValue = process.env.NEXT_PUBLIC_USE_MOCK_DATA
  console.log('🔧 Environment check - NEXT_PUBLIC_USE_MOCK_DATA:', envValue)
  console.log('🔧 Computed shouldUseMockData:', envValue === 'true')
  return envValue === 'true'
}

export function getApiBaseUrl(): string {
  return ENV_CONFIG.API_URL
}

export function logEnvironmentConfig(): void {
  if (ENV_CONFIG.IS_DEVELOPMENT) {
    console.log('🔧 Environment Configuration:')
    console.log('  - USE_MOCK_DATA:', ENV_CONFIG.USE_MOCK_DATA)
    console.log('  - API_URL:', ENV_CONFIG.API_URL)
    console.log('  - NODE_ENV:', process.env.NODE_ENV)
  }
}

// Error handling configuration
export const ERROR_CONFIG = {
  SHOW_DETAILED_ERRORS: ENV_CONFIG.IS_DEVELOPMENT,
  ENABLE_ERROR_REPORTING: ENV_CONFIG.IS_PRODUCTION,
  DEFAULT_ERROR_MESSAGE: 'An unexpected error occurred. Please try again.',
} as const