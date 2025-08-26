import { Controller } from "@/lib/types";
import { Card, CardContent } from "../ui/card";
import { useLanguage } from "@/context/languageContext";
import { Settings2Icon, Trash2 } from "lucide-react";
import { Button } from "../ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "../ui/tooltip";

export default function ControllerItemComponent({
  controller,
  onEdit,
  onDelete,
}: {
  controller: Controller;
  onEdit?: (controller: Controller) => void;
  onDelete?: (controller: Controller) => void;
}) {
  const { getT } = useLanguage();
  return (
    <Card className="w-full m-1 shadow-lg relative bg-gradient-to-r from-[#0f0f16] to-[#111218]">
      <CardContent className="flex flex-col gap-2 p-4 rounded-xl">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-taurine-light-purple">
              {controller.name || controller.type}
            </h3>

            {controller.lan_ip_address && (
              <p className="text-sm text-muted-foreground">
                {getT("page.ControllersPage.controller_ip_address")}:{" "}
                {controller.lan_ip_address}
              </p>
            )}

            {controller.type && (
              <p className="text-sm text-muted-foreground">
                {getT("page.ControllersPage.controller_device_type")}:{" "}
                {controller.type === "onos"
                  ? "ONOS"
                  : controller.type === "odl"
                  ? "OpenDaylight"
                  : controller.type === "faucet"
                  ? "Faucet"
                  : "Other"}
              </p>
            )}
          </div>
          <div className="flex flex-col gap-2 items-end">
            <div className="flex gap-1">
              {onEdit && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => onEdit(controller)}
                      className="h-8 w-8 p-0"
                    >
                      <Settings2Icon className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    {getT("components.devices.controller_item.view_edit")}
                  </TooltipContent>
                </Tooltip>
              )}
              {onDelete && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => onDelete(controller)}
                      className="h-8 w-8 p-0 text-destructive hover:text-destructive hover:bg-destructive/10"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    {getT(
                      "components.devices.controller_item.delete_controller"
                    )}
                  </TooltipContent>
                </Tooltip>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
