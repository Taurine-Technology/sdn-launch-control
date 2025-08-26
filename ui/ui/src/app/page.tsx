"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/authContext";
import { LoginForm } from "@/components/auth/LoginForm";
import Image from "next/image";
import { loginUser } from "@/lib/auth";
import { toast } from "sonner";
import { useLanguage } from "@/context/languageContext";

export default function Home() {
  const { isAuthenticated, loading, authenticate } = useAuth();
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const { getT } = useLanguage();

  const handleSubmit = async (
    username: string,
    password: string
  ): Promise<void> => {
    try {
      setSubmitting(true);
      const { token, username: returnedUsername } = await loginUser(
        username,
        password
      );
      authenticate(token, returnedUsername);
    } catch (error: unknown) {
      console.log("[LOGIN ERROR] Error logging in", error);

      // Type guard to check if error has response property
      const hasResponse =
        error && typeof error === "object" && "response" in error;
      const response = hasResponse
        ? (error as { response?: { status?: number } }).response
        : undefined;
      const status = response?.status;

      if (status === 404) {
        toast.error(getT("page.login.errors.notFound", "User not found"), {
          dismissible: true,
          richColors: true,
          action: {
            label: getT("page.login.closeButton", "Close"),
            onClick: () => {},
          },
        });
      } else if (status === 401) {
        toast.error(getT("page.login.errors.unauthorized", "Unauthorized"), {
          dismissible: true,
          richColors: true,
          action: {
            label: getT("page.login.closeButton", "Close"),
            onClick: () => {},
          },
        });
      } else if (
        (error &&
          typeof error === "object" &&
          "code" in error &&
          error.code === "ERR_NETWORK") ||
        status === 0
      ) {
        toast.error(getT("page.login.errors.api", "API Error"), {
          dismissible: true,
          richColors: true,
          action: {
            label: getT("page.login.closeButton", "Close"),
            onClick: () => {},
          },
        });
      } else {
        toast.error(getT("page.login.errors.generic", "Login failed"), {
          dismissible: true,
          richColors: true,
        });
      }
    } finally {
      setSubmitting(false);
    }
  };

  useEffect(() => {
    if (!loading && isAuthenticated) {
      return router.replace("/dashboard");
    }
  }, [isAuthenticated, loading, router]);

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-svh w-full items-center justify-center p-6 md:p-10">
        <div className="flex w-full max-w-sm flex-col gap-6">
          <div className="flex items-center justify-center">
            <Image
              src="/logo.png"
              alt="SDN Launch Control"
              width={200}
              height={200}
            />
          </div>

          <LoginForm
            handleSubmit={handleSubmit}
            submitting={submitting}
            title={getT("page.login.title", "Login")}
            description={getT(
              "page.login.description",
              "Enter your credentials"
            )}
          />
        </div>
      </div>
    );
  }

  return null;
}
