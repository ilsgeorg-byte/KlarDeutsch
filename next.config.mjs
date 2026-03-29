import bundleAnalyzer from '@next/bundle-analyzer'

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // === DOCKER/PRODUCTION OPTIMIZATIONS ===
  output: 'standalone',
  
  // SWC минификация (быстрее Terser)
  swcMinify: true,
  
  // Compiler оптимизации
  compiler: {
    // Удаляем console.log в production
    removeConsole: process.env.NODE_ENV === 'production',
  },
  
  // === IMAGE OPTIMIZATION ===
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920],
    imageSizes: [16, 32, 48, 64, 96, 128, 256],
    minimumCacheTTL: 60,
  },
  
  // === WEBPACK OPTIMIZATIONS ===
  webpack: (config, { isServer, dev }) => {
    if (!isServer && !dev) {
      // Code splitting для vendor chunks
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            // Выносим зависимости в отдельные чанки
            vendors: {
              test: /[\\/]node_modules[\\/]/,
              priority: -10,
              name: 'vendors',
              // Большие библиотеки в отдельный чанк
              reuseExistingChunk: true,
            },
            // React и ReactDOM в отдельный чанк (редко меняются)
            react: {
              test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
              priority: -20,
              name: 'react',
              reuseExistingChunk: true,
            },
            // Next.js и общие утилиты
            common: {
              minChunks: 2,
              priority: -30,
              reuseExistingChunk: true,
            },
          },
        },
      };
    }
    return config;
  },
  
  // === SECURITY HEADERS ===
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload',
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
        ],
      },
    ];
  },
  
  // === API REWRITES ===
  async rewrites() {
    return {
      beforeFiles: [
        // Для разработки: проксируем API запросы на Flask
        {
          source: '/api/:path*',
          destination: process.env.NODE_ENV === 'development'
            ? 'http://127.0.0.1:5000/api/:path*'
            : '/api/:path*'
        },
        // Для сервирования заложенных файлов (audio)
        {
          source: '/files/:path*',
          destination: process.env.NODE_ENV === 'development'
            ? 'http://127.0.0.1:5000/files/:path*'
            : '/files/:path*'
        }
      ]
    };
  },
};

// Bundle Analyzer (только при сборке с флагом)
const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
  openAnalyzer: true,
});

export default withBundleAnalyzer(nextConfig);

