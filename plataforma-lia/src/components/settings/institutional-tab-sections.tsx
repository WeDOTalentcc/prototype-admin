"use client"

import { useTranslations } from "next-intl"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Building, Globe, Upload
} from "lucide-react"

export { SocialMediaSection, SegmentSection, BranchesSection } from "./institutional-tab-market-sections"

interface SectionProps {
  onSettingsChange: (changed: boolean) => void
}

export function BasicDataSection({ onSettingsChange }: SectionProps) {
  const t = useTranslations("settings.institutionalSections")
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <Building className="w-4 h-4" />
            {t("basicInfo")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("legalName")}
              </label>
              <input
                key={t("legalNameDefault")}
                type="text"
                defaultValue={t("legalNameDefault")}
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("tradeName")}
              </label>
              <input
                key={t("tradeNameDefault")}
                type="text"
                defaultValue={t("tradeNameDefault")}
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("cnpj")}
              </label>
              <input
                type="text"
                defaultValue="12.345.678/0001-90"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("stateRegistration")}
              </label>
              <input
                type="text"
                defaultValue="123.456.789.012"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("foundingDate")}
              </label>
              <input
                type="date"
                defaultValue="1966-03-15"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("employeeCount")}
              </label>
              <select
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              >
                <option>{t("employees1_10")}</option>
                <option>{t("employees11_50")}</option>
                <option>{t("employees51_200")}</option>
                <option>{t("employees201_1000")}</option>
                <option>{t("employees1001_5000")}</option>
                <option>{t("employees5000plus")}</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("institutionalWebsite")}
              </label>
              <input
                type="url"
                defaultValue="https://sodexo.com.br"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("mainEmail")}
              </label>
              <input
                type="email"
                defaultValue="contato@sodexo.com.br"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("mainPhone")}
              </label>
              <input
                type="tel"
                defaultValue="(11) 3049-6300"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("corporateWhatsApp")}
              </label>
              <input
                type="tel"
                placeholder="(11) 99999-9999"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-lia-text-primary mb-3 block">
              {t("companyDescription")}
            </label>
            <textarea
              key={t("companyDescriptionDefault")}
              rows={4}
              defaultValue={t("companyDescriptionDefault")}
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("companyLogo")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-xl p-6 text-center bg-lia-bg-secondary dark:bg-lia-bg-secondary">
            <Upload className="w-8 h-8 mx-auto mb-2 text-lia-text-primary" />
            <p className="text-sm text-lia-text-primary mb-2">
              {t("uploadLogo")}
            </p>
            <p className="text-xs text-lia-text-primary">{t("logoFormat")}</p>
            <Button variant="outline" className="mt-3" size="sm">
              {t("chooseFile")}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export function AddressSection({ onSettingsChange }: SectionProps) {
  const t = useTranslations("settings.institutionalSections")
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <Globe className="w-4 h-4" />
            {t("headquartersAddress")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("zipCode")}
              </label>
              <input
                type="text"
                defaultValue="04571-020"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
                placeholder="00000-000"
              />
            </div>
            <div className="md:col-span-2">
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("street")}
              </label>
              <input
                key={t("streetDefault")}
                type="text"
                defaultValue={t("streetDefault")}
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("number")}
              </label>
              <input
                type="text"
                defaultValue="375"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div className="md:col-span-2">
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("complement")}
              </label>
              <input
                type="text"
                placeholder={t("complementPlaceholder")}
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("neighborhood")}
              </label>
              <input
                key={t("neighborhoodDefault")}
                type="text"
                defaultValue={t("neighborhoodDefault")}
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("city")}
              </label>
              <input
                key={t("cityDefault")}
                type="text"
                defaultValue={t("cityDefault")}
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("state")}
              </label>
              <select
                defaultValue="SP"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              >
                <option value="">{t("selectState")}</option>
                <option value="AC">{t("stateAC")}</option>
                <option value="AL">{t("stateAL")}</option>
                <option value="AP">{t("stateAP")}</option>
                <option value="AM">{t("stateAM")}</option>
                <option value="BA">{t("stateBA")}</option>
                <option value="CE">{t("stateCE")}</option>
                <option value="DF">{t("stateDF")}</option>
                <option value="ES">{t("stateES")}</option>
                <option value="GO">{t("stateGO")}</option>
                <option value="MA">{t("stateMA")}</option>
                <option value="MT">{t("stateMT")}</option>
                <option value="MS">{t("stateMS")}</option>
                <option value="MG">{t("stateMG")}</option>
                <option value="PA">{t("statePA")}</option>
                <option value="PB">{t("statePB")}</option>
                <option value="PR">{t("statePR")}</option>
                <option value="PE">{t("statePE")}</option>
                <option value="PI">{t("statePI")}</option>
                <option value="RJ">{t("stateRJ")}</option>
                <option value="RN">{t("stateRN")}</option>
                <option value="RS">{t("stateRS")}</option>
                <option value="RO">{t("stateRO")}</option>
                <option value="RR">{t("stateRR")}</option>
                <option value="SC">{t("stateSC")}</option>
                <option value="SP">{t("stateSP")}</option>
                <option value="SE">{t("stateSE")}</option>
                <option value="TO">{t("stateTO")}</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-lia-text-primary mb-3 block">
              {t("country")}
            </label>
            <select
              defaultValue="BR"
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
            >
              <option value="BR">{t("countryBR")}</option>
              <option value="US">{t("countryUS")}</option>
              <option value="FR">{t("countryFR")}</option>
              <option value="DE">{t("countryDE")}</option>
              <option value="GB">{t("countryGB")}</option>
            </select>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
