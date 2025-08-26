import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import ButtonLoading from "../ui/LoadingButton";
import { useLanguage } from "@/context/languageContext";

export function LoginForm({
  className,
  handleSubmit,
  submitting,
  title,
  description,
  ...props
}: React.ComponentProps<"div"> & {
  handleSubmit: (username: string, password: string) => Promise<void>;
  submitting: boolean;
  title: string;
  description: string;
}) {
  const { getT } = useLanguage();
  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              const form = e.currentTarget;
              const username = (
                form.elements.namedItem("username") as HTMLInputElement
              )?.value;
              const password = (
                form.elements.namedItem("password") as HTMLInputElement
              )?.value;
              await handleSubmit(username, password);
            }}
          >
            <div className="flex flex-col gap-6">
              <div className="grid gap-3">
                <Label htmlFor="username">
                  {getT("page.login.username", "Username")}
                </Label>
                <Input
                  id="username"
                  type="text"
                  placeholder={getT("page.login.usernamePlaceholder", "admin")}
                  required
                />
              </div>
              <div className="grid gap-3">
                <div className="flex items-center">
                  <Label htmlFor="password">
                    {getT("page.login.password", "Password")}
                  </Label>
                </div>
                <Input id="password" type="password" required />
              </div>
              <div className="flex flex-col gap-3">
                {submitting ? (
                  <ButtonLoading
                    label={getT("page.login.loggingIn", "Logging in...")}
                  />
                ) : (
                  <Button
                    type="submit"
                    className="w-full"
                    disabled={submitting}
                  >
                    {getT("page.login.loginButton", "Login")}
                  </Button>
                )}
              </div>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
