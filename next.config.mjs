/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
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
  }
};

export default nextConfig;

