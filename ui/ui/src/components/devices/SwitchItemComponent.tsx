"use client";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { NetworkDeviceDetails } from "@/lib/types";
import { FC } from "react";
import { useLanguage } from "@/context/languageContext";
import { Settings2Icon, Trash2, Bomb } from "lucide-react";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";

interface SwitchItemComponentProps {
  device: NetworkDeviceDetails;
  onView?: (id: string) => void;
  onDelete?: (device: NetworkDeviceDetails) => void;
  onNuke?: (device: NetworkDeviceDetails) => void;
}

export const SwitchItemComponent: FC<SwitchItemComponentProps> = ({
  device,
  onView,
  onDelete,
  onNuke,
}) => {
  const { getT } = useLanguage();
  return (
    <Card className="w-full m-1 shadow-lg relative bg-gradient-to-r from-[#0f0f16] to-[#111218]">
      <CardContent className="flex flex-col gap-2 p-4 rounded-xl">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-taurine-light-purple">
              {device.name || device.id}
            </h3>

            {device.lan_ip_address && (
              <p className="text-sm text-muted-foreground">
                {getT("page.SwitchesPage.switch_ip_address", "IP Address")}:{" "}
                {device.lan_ip_address}
              </p>
            )}
            {device.device_type && (
              <p className="text-sm text-muted-foreground">
                {getT("page.SwitchesPage.switch_device_type", "Device Type")}:{" "}
                {device.device_type}
              </p>
            )}
            {device.operating_system && (
              <p className="text-sm text-muted-foreground">
                {getT(
                  "page.SwitchesPage.switch_operating_system",
                  "Operating System"
                )}
                : {device.operating_system}
              </p>
            )}
          </div>
          <div className="flex flex-col gap-2 items-end">
            <div className="flex gap-1">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => onView && onView(device.id)}
                    className="h-8 w-8"
                  >
                    <Settings2Icon className="w-4 h-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>View/Edit</TooltipContent>
              </Tooltip>

              {onDelete && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => onDelete(device)}
                      className="h-8 w-8 text-destructive hover:text-destructive"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Delete Switch</TooltipContent>
                </Tooltip>
              )}

              {onNuke && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => onNuke(device)}
                      className="h-8 w-8 text-destructive hover:text-destructive"
                    >
                      <Bomb className="w-4 h-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Force Delete (Nuke)</TooltipContent>
                </Tooltip>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default SwitchItemComponent;
