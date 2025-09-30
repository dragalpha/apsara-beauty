// Save as: apsara-beauty/frontend/next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    BACKEND_URL: process.env.BACKEND_URL || 'http://localhost:8000',
  },
  images: {
    domains: ['localhost', 'your-backend-domain.com'],
  },
}

module.exports = nextConfig