"use client";

import { useState, useEffect } from "react";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/sidebar/app-sidebar";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import { useLanguage } from "@/context/languageContext";
import { toast } from "sonner";
import {
  getUserData,
  updateUserProfile,
  updateUserPassword,
  linkTelegram,
} from "@/lib/user";
import type {
  UserData,
  ProfileFormData,
  PasswordFormData,
  TelegramLinkData,
  AccountSettingsState,
} from "@/lib/types";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Info } from "lucide-react";
import { v4 as uuidv4 } from "uuid";
import { ProfileComponent } from "@/components/account/ProfileComponent";
import { ChangePasswordComponent } from "@/components/account/ChangePasswordComponent";
import { TelegramIntegrationComponent } from "@/components/account/TelegramIntegrationComponent";
import { LanguageComponent } from "@/components/account/LanguageComponent";

export default function Account() {
  const { getT, language, setLanguage } = useLanguage();

  const [state, setState] = useState<AccountSettingsState>({
    user: { username: "", email: "" },
    profile: {
      telegram_username: "",
      phone_number: "",
      telegram_linked: false,
    },
    isLoading: true,
    isEditing: false,
    isChangingPassword: false,
    isLinkingTelegram: false,
    error: null,
  });

  const [profileForm, setProfileForm] = useState<ProfileFormData>({
    username: "",
    email: "",
    telegram_username: "",
    phone_number: "",
  });

  const [passwordForm, setPasswordForm] = useState<PasswordFormData>({
    old_password: "",
    new_password: "",
    confirm_password: "",
  });

  const [telegramLinkData, setTelegramLinkData] = useState<TelegramLinkData>({
    unique_token: "",
    telegram_username: "",
    phone_number: "",
  });

  const [countdown, setCountdown] = useState(45);
  const [showTelegramDialog, setShowTelegramDialog] = useState(false);

  // Fetch user data on component mount
  useEffect(() => {
    const token = localStorage.getItem("taurineToken");
    if (token) {
      fetchUserData();
    }
  }, []);

  const fetchUserData = async () => {
    const token = localStorage.getItem("taurineToken");
    if (!token) return;

    try {
      setState((prev) => ({ ...prev, isLoading: true }));
      const userData: UserData = await getUserData(token);

      setState((prev) => ({
        ...prev,
        user: userData.user,
        profile: userData.profile,
        isLoading: false,
      }));

      setProfileForm({
        username: userData.user.username || "",
        email: userData.user.email || "",
        telegram_username: userData.profile.telegram_username || "",
        phone_number: userData.profile.phone_number || "",
      });
    } catch (error) {
      console.error("Error fetching user data:", error);
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: "Failed to fetch user data",
      }));
      toast.error("Failed to fetch user data");
    }
  };

  const handleProfileUpdate = async () => {
    const token = localStorage.getItem("taurineToken");
    if (!token) return;

    try {
      setState((prev) => ({ ...prev, isLoading: true }));

      await updateUserProfile(
        token,
        {
          username: profileForm.username,
          email: profileForm.email,
        },
        {
          telegram_username: profileForm.telegram_username,
          phone_number: profileForm.phone_number,
        }
      );

      setState((prev) => ({
        ...prev,
        user: { username: profileForm.username, email: profileForm.email },
        profile: {
          ...prev.profile,
          telegram_username: profileForm.telegram_username,
          phone_number: profileForm.phone_number,
        },
        isEditing: false,
        isLoading: false,
      }));

      toast.success(
        getT(
          "page.account.profile_section.update_success",
          "Profile updated successfully!"
        )
      );
    } catch (error) {
      console.error("Error updating profile:", error);
      setState((prev) => ({ ...prev, isLoading: false }));
      toast.error(
        getT(
          "page.account.profile_section.update_error",
          "Failed to update profile"
        )
      );
    }
  };

  const handlePasswordChange = async () => {
    const token = localStorage.getItem("taurineToken");
    if (!token) return;

    if (passwordForm.new_password !== passwordForm.confirm_password) {
      toast.error(
        getT(
          "page.account.password_section.password_mismatch",
          "Passwords do not match"
        )
      );
      return;
    }

    try {
      setState((prev) => ({ ...prev, isLoading: true }));

      await updateUserPassword(
        token,
        passwordForm.old_password,
        passwordForm.new_password
      );

      setPasswordForm({
        old_password: "",
        new_password: "",
        confirm_password: "",
      });

      setState((prev) => ({
        ...prev,
        isChangingPassword: false,
        isLoading: false,
      }));

      toast.success(
        getT(
          "page.account.password_section.update_success",
          "Password updated successfully!"
        )
      );
    } catch (error: unknown) {
      console.error("Error updating password:", error);
      setState((prev) => ({ ...prev, isLoading: false }));

      const errorResponse = error as {
        response?: { data?: { old_password?: string } };
      };
      if (errorResponse?.response?.data?.old_password) {
        toast.error(
          getT(
            "page.account.password_section.old_password_error",
            "Current password is incorrect"
          )
        );
      } else {
        toast.error(
          getT(
            "page.account.password_section.update_error",
            "Failed to update password"
          )
        );
      }
    }
  };

  const handleTelegramLink = async () => {
    const token = localStorage.getItem("taurineToken");
    if (!token) return;

    const uniqueToken = uuidv4();
    setTelegramLinkData((prev) => ({ ...prev, unique_token: uniqueToken }));
    setShowTelegramDialog(true);
    setCountdown(45);

    try {
      await linkTelegram(token, { unique_token: uniqueToken });

      // Start countdown and check for successful linking
      const interval = setInterval(async () => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            handleTelegramDialogClose();
            return 45;
          }
          return prev - 1;
        });
      }, 1010);
    } catch (error) {
      console.error("Error linking Telegram:", error);
      toast.error(
        getT(
          "page.account.telegram_section.link_error",
          "Failed to link Telegram account"
        )
      );
      setShowTelegramDialog(false);
    }
  };

  const handleTelegramDialogClose = async () => {
    setShowTelegramDialog(false);

    // Recheck Telegram link status
    const token = localStorage.getItem("taurineToken");
    if (!token) return;

    try {
      const userData: UserData = await getUserData(token);
      const wasLinked = state.profile.telegram_linked;
      const isNowLinked = userData.profile.telegram_linked;

      // Update state with new data
      setState((prev) => ({
        ...prev,
        user: userData.user,
        profile: userData.profile,
      }));

      // Show appropriate toast based on status change
      if (!wasLinked && isNowLinked) {
        toast.success(
          getT(
            "page.account.telegram_section.link_success",
            "Telegram account linked successfully!"
          )
        );
      } else if (wasLinked && !isNowLinked) {
        toast.error(
          getT(
            "page.account.telegram_section.unlink_success",
            "Telegram account unlinked"
          )
        );
      } else if (!wasLinked && !isNowLinked) {
        toast.error(
          getT(
            "page.account.telegram_section.link_unsuccessful",
            "Telegram linking was unsuccessful. Please try again."
          )
        );
      }
    } catch (error) {
      console.error("Error checking Telegram status:", error);
      toast.error(
        getT(
          "page.account.telegram_section.status_check_error",
          "Failed to check Telegram link status"
        )
      );
    }
  };

  const handleLanguageChange = (newLanguage: "en" | "es") => {
    setLanguage(newLanguage);
    toast.success(
      getT(
        "page.account.language_section.language_changed",
        "Language changed successfully!"
      )
    );
  };

  if (state.isLoading) {
    return (
      <SidebarProvider
        style={
          {
            "--sidebar-width": "calc(var(--spacing) * 72)",
            "--header-height": "calc(var(--spacing) * 12)",
          } as React.CSSProperties
        }
      >
        <AppSidebar />
        <SidebarInset>
          <header className="flex h-16 shrink-0 items-center gap-2">
            <div className="flex items-center gap-2 px-4">
              <SidebarTrigger className="-ml-1" />
              <Separator
                orientation="vertical"
                className="mr-2 data-[orientation=vertical]:h-4"
              />
              <Breadcrumb>
                <BreadcrumbList>
                  <BreadcrumbItem className="hidden md:block">
                    <BreadcrumbLink href="/account">
                      {getT("navigation.account", "Account")}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>
          </header>
          <div className="@container/main w-full max-w-7.5xl flex flex-col gap-6 px-4 lg:px-8 py-8 mx-auto">
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          </div>
        </SidebarInset>
      </SidebarProvider>
    );
  }

  return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "calc(var(--spacing) * 72)",
          "--header-height": "calc(var(--spacing) * 12)",
        } as React.CSSProperties
      }
    >
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2">
          <div className="flex items-center gap-2 px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator
              orientation="vertical"
              className="mr-2 data-[orientation=vertical]:h-4"
            />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem className="hidden md:block">
                  <BreadcrumbLink href="/account">
                    {getT("navigation.account", "Account")}
                  </BreadcrumbLink>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          </div>
        </header>

        <div className="@container/main w-full max-w-7.5xl flex flex-col gap-6 px-4 lg:px-8 py-8 mx-auto">
          <div className="space-y-2">
            <h1 className="text-2xl font-bold">
              {getT("page.account.title", "Account Settings")}
            </h1>
            <p className="text-muted-foreground">
              {getT(
                "page.account.description",
                "Manage your account settings and preferences"
              )}
            </p>
          </div>

          {/* Information Banner */}
          <div className="flex items-center gap-2 p-4 bg-muted rounded-lg">
            <Info className="h-4 w-4 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              {getT(
                "page.account.profile_section.description",
                "Changes to your profile will apply to all of your workspaces."
              )}
            </p>
          </div>

          <Tabs defaultValue="profile" className="space-y-6">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="profile" className="flex items-center gap-2">
                Profile
              </TabsTrigger>
              <TabsTrigger value="password" className="flex items-center gap-2">
                Password
              </TabsTrigger>
              <TabsTrigger value="telegram" className="flex items-center gap-2">
                Telegram
              </TabsTrigger>
              <TabsTrigger
                value="preferences"
                className="flex items-center gap-2"
              >
                Preferences
              </TabsTrigger>
            </TabsList>

            {/* Profile Tab */}
            <TabsContent value="profile" className="space-y-6">
              <ProfileComponent
                profileForm={profileForm}
                isEditing={state.isEditing}
                isLoading={state.isLoading}
                onProfileFormChange={(field, value) =>
                  setProfileForm((prev) => ({ ...prev, [field]: value }))
                }
                onEditToggle={() =>
                  setState((prev) => ({ ...prev, isEditing: true }))
                }
                onSave={handleProfileUpdate}
                onCancel={() => {
                  setState((prev) => ({ ...prev, isEditing: false }));
                  setProfileForm({
                    username: state.user.username || "",
                    email: state.user.email || "",
                    telegram_username: state.profile.telegram_username || "",
                    phone_number: state.profile.phone_number || "",
                  });
                }}
              />
            </TabsContent>

            {/* Password Tab */}
            <TabsContent value="password" className="space-y-6">
              <ChangePasswordComponent
                passwordForm={passwordForm}
                isChangingPassword={state.isChangingPassword}
                isLoading={state.isLoading}
                onPasswordFormChange={(field, value) =>
                  setPasswordForm((prev) => ({ ...prev, [field]: value }))
                }
                onDialogToggle={(open) =>
                  setState((prev) => ({ ...prev, isChangingPassword: open }))
                }
                onSave={handlePasswordChange}
              />
            </TabsContent>

            {/* Telegram Tab */}
            <TabsContent value="telegram" className="space-y-6">
              <TelegramIntegrationComponent
                telegramLinked={state.profile.telegram_linked}
                showTelegramDialog={showTelegramDialog}
                countdown={countdown}
                telegramLinkData={telegramLinkData}
                isLinkingTelegram={state.isLinkingTelegram}
                onLinkTelegram={handleTelegramLink}
                onDialogToggle={(open) => {
                  if (!open) {
                    handleTelegramDialogClose();
                  } else {
                    setShowTelegramDialog(true);
                  }
                }}
              />
            </TabsContent>

            {/* Preferences Tab */}
            <TabsContent value="preferences" className="space-y-6">
              <LanguageComponent
                language={language}
                onLanguageChange={handleLanguageChange}
              />
            </TabsContent>
          </Tabs>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
