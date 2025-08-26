"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Loader2, Info, Download, Trash2, CheckCircle } from "lucide-react";
import { Plugin, PluginInstallation, NetworkDeviceDetails } from "@/lib/types";
import { installPluginOnLC, uninstallPluginOnLC } from "@/lib/software";
import { useAuth } from "@/context/authContext";
import { SnifferInstallForm } from "./SnifferInstallForm";
import { toast } from "sonner";
import { useLanguage } from "@/context/languageContext";

interface PluginCardProps {
  plugin: Plugin;
  installation?: PluginInstallation;
  devices?: NetworkDeviceDetails[];
  installations?: PluginInstallation[];
  onInstallSuccess: () => void;
  onUninstallSuccess: () => void;
}

export function PluginCard({
  plugin,
  installation,
  devices = [],
  installations = [],
  onInstallSuccess,
  onUninstallSuccess,
}: PluginCardProps) {
  const { token } = useAuth();
  const { getT } = useLanguage();
  const [isLoading, setIsLoading] = useState(false);
  const [isInfoOpen, setIsInfoOpen] = useState(false);
  const [isInstallConfirmOpen, setIsInstallConfirmOpen] = useState(false);
  const [isUninstallConfirmOpen, setIsUninstallConfirmOpen] = useState(false);

  const isInstalled = !!installation;
  const isSnifferPlugin = plugin.name === "tau-traffic-classification-sniffer";
  const showGenericInstall = !isInstalled && !plugin.requires_target_device;
  const showGenericUninstall = isInstalled && !plugin.requires_target_device;

  const handleInstall = async () => {
    if (!token) return;

    setIsLoading(true);

    try {
      await installPluginOnLC(token, { plugin: plugin.id });
      toast.success(
        getT(
          "components.plugins.plugin_card.install_success",
          `${plugin.alias} installed successfully.`
        )
      );
      onInstallSuccess();
    } catch (error) {
      console.error("Installation failed:", error);
      const errorMessage =
        error instanceof Error
          ? error.message
          : getT("components.plugins.plugin_card.install_error");
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
      setIsInstallConfirmOpen(false);
    }
  };

  const handleUninstall = async () => {
    if (!token || !installation) return;

    setIsLoading(true);

    try {
      await uninstallPluginOnLC(token, installation.id);
      toast.success(
        getT(
          "components.plugins.plugin_card.uninstall_success",
          `${plugin.alias} uninstalled successfully.`
        )
      );
      onUninstallSuccess();
    } catch (error) {
      console.error("Uninstallation failed:", error);
      const errorMessage =
        error instanceof Error
          ? error.message
          : getT("components.plugins.plugin_card.uninstall_error");
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
      setIsUninstallConfirmOpen(false);
    }
  };

  const renderActionButtons = () => {
    if (isSnifferPlugin) {
      // Sniffer uses its dedicated form for install/update
      return (
        <SnifferInstallForm
          devices={devices.filter((d) => d.device_type === "switch")}
          installations={installations}
          onInstallSuccess={onInstallSuccess}
        />
      );
    } else {
      // Generic server-side plugins
      if (showGenericInstall) {
        return (
          <Dialog
            open={isInstallConfirmOpen}
            onOpenChange={setIsInstallConfirmOpen}
          >
            <DialogTrigger asChild>
              <Button size="sm" className="flex-1">
                <Download className="w-4 h-4 mr-2" />
                {getT("components.plugins.plugin_card.install")}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>
                  {getT(
                    "components.plugins.plugin_card.install_title",
                    `Install ${plugin.alias}?`
                  )}
                </DialogTitle>
                <DialogDescription>
                  {getT("components.plugins.plugin_card.install_description")}
                </DialogDescription>
              </DialogHeader>
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => setIsInstallConfirmOpen(false)}
                >
                  {getT("components.plugins.plugin_card.cancel")}
                </Button>
                <Button onClick={handleInstall} disabled={isLoading}>
                  {isLoading && (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  )}
                  {isLoading
                    ? getT("components.plugins.plugin_card.installing")
                    : getT("components.plugins.plugin_card.install")}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        );
      } else if (showGenericUninstall) {
        return (
          <>
            <Button variant="outline" size="sm" className="flex-1" disabled>
              <CheckCircle className="w-4 h-4 mr-2" />
              {getT("components.plugins.plugin_card.installed")}
            </Button>
            <Dialog
              open={isUninstallConfirmOpen}
              onOpenChange={setIsUninstallConfirmOpen}
            >
              <DialogTrigger asChild>
                <Button variant="destructive" size="sm">
                  <Trash2 className="w-4 h-4" />
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>
                    {getT(
                      "components.plugins.plugin_card.uninstall_title",
                      `Uninstall ${plugin.alias}?`
                    )}
                  </DialogTitle>
                  <DialogDescription>
                    {getT(
                      "components.plugins.plugin_card.uninstall_description"
                    )}
                  </DialogDescription>
                </DialogHeader>
                <div className="flex justify-end gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setIsUninstallConfirmOpen(false)}
                  >
                    {getT("components.plugins.plugin_card.cancel")}
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={handleUninstall}
                    disabled={isLoading}
                  >
                    {isLoading && (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    )}
                    {isLoading
                      ? getT("components.plugins.plugin_card.uninstalling")
                      : getT("components.plugins.plugin_card.uninstall")}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </>
        );
      } else if (isInstalled && plugin.requires_target_device) {
        // Installed on a device (like sniffer, but handled elsewhere)
        return (
          <Button variant="outline" size="sm" className="flex-1" disabled>
            <CheckCircle className="w-4 h-4 mr-2" />
            {getT("components.plugins.plugin_card.installed")}
          </Button>
        );
      } else {
        return null;
      }
    }
  };

  return (
    <Card className="w-full max-w-sm flex flex-col h-full">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            {/* Placeholder icon - you can replace with actual plugin icons */}
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
              {plugin.alias.charAt(0).toUpperCase()}
            </div>
            <div>
              <CardTitle className="text-md font-semibold">
                {plugin.alias}
              </CardTitle>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pb-4 flex-1">
        <CardDescription className="text-sm text-muted-foreground mb-3">
          {plugin.short_description}
        </CardDescription>

        <div className="space-y-2 text-xs text-muted-foreground">
          <div className="flex justify-between">
            <span>{getT("components.plugins.plugin_card.version")}:</span>
            <span className="font-medium">{plugin.version}</span>
          </div>
          <div className="flex justify-between">
            <span>{getT("components.plugins.plugin_card.author")}:</span>
            <span className="font-medium">{plugin.author}</span>
          </div>
        </div>
      </CardContent>

      <CardFooter className="pt-0 mt-auto">
        <div className="flex w-full gap-2">
          <Dialog open={isInfoOpen} onOpenChange={setIsInfoOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm" className="flex-1">
                <Info className="w-4 h-4 mr-2" />
                {getT("components.plugins.plugin_card.details")}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{plugin.alias}</DialogTitle>
                <DialogDescription>
                  {plugin.long_description ||
                    getT("components.plugins.plugin_card.no_description")}
                </DialogDescription>
              </DialogHeader>
            </DialogContent>
          </Dialog>

          {renderActionButtons()}
        </div>
      </CardFooter>
    </Card>
  );
}
