"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Lock } from "lucide-react";
import { useLanguage } from "@/context/languageContext";
import type { PasswordFormData } from "@/lib/types";

interface ChangePasswordComponentProps {
  passwordForm: PasswordFormData;
  isChangingPassword: boolean;
  isLoading: boolean;
  onPasswordFormChange: (field: keyof PasswordFormData, value: string) => void;
  onDialogToggle: (open: boolean) => void;
  onSave: () => void;
}

export function ChangePasswordComponent({
  passwordForm,
  isChangingPassword,
  isLoading,
  onPasswordFormChange,
  onDialogToggle,
  onSave,
}: ChangePasswordComponentProps) {
  const { getT } = useLanguage();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lock className="h-5 w-5" />
          {getT("page.account.password_section.title", "Password")}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">
          {getT(
            "page.account.password_section.description",
            "Change your account password"
          )}
        </p>

        <Dialog open={isChangingPassword} onOpenChange={onDialogToggle}>
          <DialogTrigger asChild>
            <Button>
              {getT(
                "page.account.password_section.change_password",
                "Change Password"
              )}
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {getT(
                  "page.account.password_section.change_password",
                  "Change Password"
                )}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="current_password">
                  {getT(
                    "page.account.password_section.current_password",
                    "Current Password"
                  )}
                </Label>
                <Input
                  id="current_password"
                  type="password"
                  value={passwordForm.old_password}
                  onChange={(e) =>
                    onPasswordFormChange("old_password", e.target.value)
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new_password">
                  {getT(
                    "page.account.password_section.new_password",
                    "New Password"
                  )}
                </Label>
                <Input
                  id="new_password"
                  type="password"
                  value={passwordForm.new_password}
                  onChange={(e) =>
                    onPasswordFormChange("new_password", e.target.value)
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirm_password">
                  {getT(
                    "page.account.password_section.confirm_password",
                    "Confirm New Password"
                  )}
                </Label>
                <Input
                  id="confirm_password"
                  type="password"
                  value={passwordForm.confirm_password}
                  onChange={(e) =>
                    onPasswordFormChange("confirm_password", e.target.value)
                  }
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => onDialogToggle(false)}>
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
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
}
