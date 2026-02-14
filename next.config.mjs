/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination:
          process.env.NODE_ENV === "development"
            ? "http://127.0.0.1:5000/:path*" // Локально: /api/x -> Flask /x
            : "/api/:path*", // Продакшн (Vercel): /api/x -> Flask /api/x
      },
      {
        source: "/api/files/:path*",
        destination: "http://127.0.0.1:5000/files/:path*" 
      }

    ];
  },
};




export default nextConfig;
