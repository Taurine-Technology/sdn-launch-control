import { NextResponse } from "next/server";

export async function GET() {
  try {
    // Basic health check - you can add more sophisticated checks here
    // such as database connectivity, external service checks, etc.

    const healthData = {
      status: "healthy",
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      environment: process.env.NODE_ENV || "development",
      version: process.env.npm_package_version || "1.0.0",
    };

    return NextResponse.json(healthData, { status: 200 });
  } catch (error) {
    console.error("Health check failed:", error);

    return NextResponse.json(
      {
        status: "unhealthy",
        timestamp: new Date().toISOString(),
        error: "Health check failed",
      },
      { status: 503 }
    );
  }
}
