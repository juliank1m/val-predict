import type { NextConfig } from "next";

const securityHeaders = [
  // Allow the profile site to embed the app in an iframe; still blocks all
  // other origins (clickjacking protection). frame-ancestors replaces
  // X-Frame-Options, which can only DENY or allow same-origin.
  {
    key: "Content-Security-Policy",
    value: "frame-ancestors 'self' https://juliankim.dev https://*.juliankim.dev http://localhost:5173",
  },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
];

const nextConfig: NextConfig = {
  output: "standalone",
  async headers() {
    return [{ source: "/(.*)", headers: securityHeaders }];
  },
};

export default nextConfig;
