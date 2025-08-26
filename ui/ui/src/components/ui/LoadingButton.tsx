import { Loader2Icon } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ButtonLoadingProps {
  disabled?: boolean;
  className?: string;
  label?: string;
}

const ButtonLoading = ({
  label = "Please wait",
  disabled = true,
  className = "",
}: ButtonLoadingProps) => (
  <Button size="sm" disabled={disabled} className={className}>
    <Loader2Icon className="animate-spin mr-2" />
    {label}
  </Button>
);

export default ButtonLoading;
