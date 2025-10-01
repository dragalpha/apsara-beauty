// Save as: apsara-beauty/frontend/next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || 'http://localhost:8000',
    NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || process.env.BACKEND_URL || 'http://localhost:8000',
    BACKEND_URL: process.env.BACKEND_URL || 'http://localhost:8000',
  },
  images: {
    domains: ['localhost', 'your-backend-domain.com', 'm.media-amazon.com', 'images-na.ssl-images-amazon.com', 'amazon.com', 'www.amazon.com'],
  },
}

module.exports = nextConfig