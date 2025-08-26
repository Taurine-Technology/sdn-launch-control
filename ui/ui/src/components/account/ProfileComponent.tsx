"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { User } from "lucide-react";
import { useLanguage } from "@/context/languageContext";
import type { ProfileFormData } from "@/lib/types";

interface ProfileComponentProps {
  profileForm: ProfileFormData;
  isEditing: boolean;
  isLoading: boolean;
  onProfileFormChange: (field: keyof ProfileFormData, value: string) => void;
  onEditToggle: () => void;
  onSave: () => void;
  onCancel: () => void;
}

export function ProfileComponent({
  profileForm,
  isEditing,
  isLoading,
  onProfileFormChange,
  onEditToggle,
  onSave,
  onCancel,
}: ProfileComponentProps) {
  const { getT } = useLanguage();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <User className="h-5 w-5" />
          {getT("page.account.profile_section.title", "Profile")}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Profile Form */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="username">
              {getT("page.account.profile_section.first_name", "First Name")}
            </Label>
            <Input
              id="username"
              value={profileForm.username}
              onChange={(e) => onProfileFormChange("username", e.target.value)}
              disabled={!isEditing}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">
              {getT("page.account.profile_section.email", "Email Address")}
            </Label>
            <Input
              id="email"
              type="email"
              value={profileForm.email}
              onChange={(e) => onProfileFormChange("email", e.target.value)}
              disabled={!isEditing}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="telegram_username">
            {getT(
              "page.account.telegram_section.telegram_username",
              "Telegram Username"
            )}
          </Label>
          <Input
            id="telegram_username"
            value={profileForm.telegram_username}
            onChange={(e) =>
              onProfileFormChange("telegram_username", e.target.value)
            }
            disabled={!isEditing}
            placeholder="@username"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="phone_number">
            {getT("page.account.telegram_section.phone_number", "Phone Number")}
          </Label>
          <Input
            id="phone_number"
            value={profileForm.phone_number}
            onChange={(e) =>
              onProfileFormChange("phone_number", e.target.value)
            }
            disabled={!isEditing}
            placeholder="+1234567890"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-2">
          {isEditing ? (
            <>
              <Button variant="outline" onClick={onCancel}>
                {getT("page.account.profile_section.cancel", "Cancel")}
              </Button>
              <Button onClick={onSave} disabled={isLoading}>
                {isLoading
                  ? getT("page.account.profile_section.saving", "Saving...")
                  : getT(
                      "page.account.profile_section.save_changes",
                      "Save Changes"
                    )}
              </Button>
            </>
          ) : (
            <Button onClick={onEditToggle}>
              {getT("page.account.profile_section.edit", "Edit")}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
