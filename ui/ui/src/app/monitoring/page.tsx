"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function MonitoringPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to the classifications page where the monitoring graphs are located
    router.push("/monitoring/classifications");
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-4">
          Redirecting to Monitoring...
        </h1>
        <p className="text-muted-foreground">
          Please wait while we redirect you to the monitoring dashboard.
        </p>
      </div>
    </div>
  );
}

