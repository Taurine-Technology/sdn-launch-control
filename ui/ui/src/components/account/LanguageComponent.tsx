"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Globe } from "lucide-react";
import { useLanguage } from "@/context/languageContext";

interface LanguageComponentProps {
  language: string;
  onLanguageChange: (language: "en" | "es") => void;
}

export function LanguageComponent({
  language,
  onLanguageChange,
}: LanguageComponentProps) {
  const { getT } = useLanguage();

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            {getT("page.account.language_section.title", "Language")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            {getT(
              "page.account.language_section.description",
              "Choose your preferred language"
            )}
          </p>

          <div className="space-y-2">
            <Label>Language</Label>
            <Select value={language} onValueChange={onLanguageChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en">
                  {getT("page.account.language_section.english", "English")}
                </SelectItem>
                <SelectItem value="es">
                  {getT("page.account.language_section.spanish", "Spanish")}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
    </>
  );
}
