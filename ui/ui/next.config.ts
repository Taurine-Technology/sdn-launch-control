import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: "standalone",
  // Allow cross-origin requests from development network (development only)
  // See: https://nextjs.org/docs/app/api-reference/config/next-config-js/allowedDevOrigins
  ...(process.env.NODE_ENV === "development" &&
    process.env.ALLOWED_DEV_ORIGINS && {
      allowedDevOrigins: process.env.ALLOWED_DEV_ORIGINS.split(",").map(
        (origin) => origin.trim()
      ),
    }),
};

export default nextConfig;
