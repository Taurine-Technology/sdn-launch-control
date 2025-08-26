"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { MessageCircle } from "lucide-react";
import { useLanguage } from "@/context/languageContext";
import type { TelegramLinkData } from "@/lib/types";

import { QRCodeSVG } from "qrcode.react";

interface TelegramIntegrationComponentProps {
  telegramLinked: boolean;
  showTelegramDialog: boolean;
  countdown: number;
  telegramLinkData: TelegramLinkData;
  isLinkingTelegram: boolean;
  onLinkTelegram: () => void;
  onDialogToggle: (open: boolean) => void;
}

export function TelegramIntegrationComponent({
  telegramLinked,
  showTelegramDialog,
  countdown,
  telegramLinkData,
  isLinkingTelegram,
  onLinkTelegram,
  onDialogToggle,
}: TelegramIntegrationComponentProps) {
  const { getT } = useLanguage();

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="h-5 w-5" />
            {getT(
              "page.account.telegram_section.title",
              "Telegram Integration"
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            {getT(
              "page.account.telegram_section.description",
              "Link your Telegram account for notifications"
            )}
          </p>

          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="flex items-center gap-3">
              <MessageCircle className="h-5 w-5 text-blue-500" />
              <div>
                <p className="font-medium">Telegram</p>
                <p className="text-sm text-muted-foreground">
                  {telegramLinked
                    ? getT(
                        "page.account.telegram_section.linked",
                        "Telegram account linked"
                      )
                    : getT(
                        "page.account.telegram_section.not_linked",
                        "Telegram account not linked"
                      )}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {telegramLinked ? (
                <Badge
                  variant="secondary"
                  className="bg-green-100 text-green-800"
                >
                  {getT("page.account.telegram_section.linked", "Linked")}
                </Badge>
              ) : (
                <Button onClick={onLinkTelegram} disabled={isLinkingTelegram}>
                  {getT(
                    "page.account.telegram_section.link_telegram",
                    "Link Telegram"
                  )}
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Telegram Linking Dialog */}
      <Dialog open={showTelegramDialog} onOpenChange={onDialogToggle}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Link Telegram Account</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Scan the QR code or click the link below to link your Telegram
              account.
            </p>
            <div className="text-center">
              <p className="text-sm font-medium">
                Time remaining: {countdown} seconds
              </p>
            </div>
            <div className="flex justify-center">
              <div className="p-4 rounded-lg">
                <QRCodeSVG
                  value={`https://t.me/LaunchControlBot?start=${telegramLinkData.unique_token}`}
                  size={192}
                  level="M"
                  bgColor="#FFFFFF"
                  fgColor="#000000"
                  marginSize={4}
                />
              </div>
            </div>
            <div className="text-center">
              <Button asChild>
                <a
                  href={`https://t.me/LaunchControlBot?start=${telegramLinkData.unique_token}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Open Telegram
                </a>
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
