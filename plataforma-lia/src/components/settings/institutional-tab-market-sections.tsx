"use client"

import { useTranslations } from "next-intl"
import { CURRENCY_SYMBOL } from"@/lib/pricing"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import {
  MessageSquare, Target, Network,
  Plus, Edit
} from"lucide-react"

interface SectionProps {
  onSettingsChange: (changed: boolean) => void
}

export function SocialMediaSection({ onSettingsChange }: SectionProps) {
  const t = useTranslations("settings.socialMediaSection")
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <MessageSquare className="w-4 h-4" />
            {t("title")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-wedo-magenta rounded-md"></div>
                {t("instagram")}
              </label>
              <input
                type="url"
                placeholder="https://instagram.com/sodexobrasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-lia-bg-inverse rounded-xl"></div>
                {t("facebook")}
              </label>
              <input
                type="url"
                placeholder="https://facebook.com/sodexobrasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-wedo-cyan-dark rounded-md"></div>
                {t("linkedin")}
              </label>
              <input
                type="url"
                defaultValue="https://linkedin.com/company/sodexo"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-lia-btn-primary-bg rounded-md"></div>
                {t("twitterX")}
              </label>
              <input
                type="url"
                placeholder="https://twitter.com/sodexobrasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-status-error rounded-md"></div>
                {t("youtube")}
              </label>
              <input
                type="url"
                placeholder="https://youtube.com/@sodexobrasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-black rounded-md"></div>
                {t("tiktok")}
              </label>
              <input
                type="url"
                placeholder="https://tiktok.com/@sodexobrasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-lia-border-subtle dark:border-lia-border-subtle">
            <h4 className="text-sm font-medium text-lia-text-primary mb-3">{t("otherChannels")}</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                  {t("corporateBlog")}
                </label>
                <input
                  type="url"
                  placeholder="https://blog.sodexo.com.br"
                  onChange={() => onSettingsChange(true)}
                  className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                  {t("careersPortal")}
                </label>
                <input
                  type="url"
                  placeholder="https://carreiras.sodexo.com.br"
                  onChange={() => onSettingsChange(true)}
                  className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export function SegmentSection({ onSettingsChange }: SectionProps) {
  const t = useTranslations("settings.segmentSection")
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <Target className="w-4 h-4" />
            {t("title")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("mainSector")}
              </label>
              <select
                defaultValue="servicos"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              >
                <option value="">{t("selectSector")}</option>
                <option value="servicos">{t("foodAndServices")}</option>
                <option value="tecnologia">{t("technology")}</option>
                <option value="saude">{t("healthcare")}</option>
                <option value="educacao">{t("education")}</option>
                <option value="financeiro">{t("financial")}</option>
                <option value="industria">{t("manufacturing")}</option>
                <option value="varejo">{t("retail")}</option>
                <option value="construcao">{t("construction")}</option>
                <option value="energia">{t("energy")}</option>
                <option value="agronegocio">{t("agribusiness")}</option>
                <option value="telecomunicacoes">{t("telecom")}</option>
                <option value="consultoria">{t("consulting")}</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("subSector")}
              </label>
              <input
                key={t("subSectorDefault")}
                type="text"
                defaultValue={t("subSectorDefault")}
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
                placeholder={t("subSectorPlaceholder")}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("companyPhase")}
              </label>
              <select
                defaultValue="grande"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              >
                <option value="startup">{t("phaseStartup")}</option>
                <option value="scaleup">{t("phaseScaleup")}</option>
                <option value="media">{t("phaseMedium")}</option>
                <option value="grande">{t("phaseLarge")}</option>
                <option value="multinacional">{t("phaseMultinational")}</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("businessModel")}
              </label>
              <select
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              >
                <option value="">{t("selectModel")}</option>
                <option value="b2b">{t("modelB2B")}</option>
                <option value="b2c">{t("modelB2C")}</option>
                <option value="b2b2c">{t("modelB2B2C")}</option>
                <option value="marketplace">{t("modelMarketplace")}</option>
                <option value="saas">{t("modelSaaS")}</option>
                <option value="consultoria">{t("consultingServices")}</option>
                <option value="produto">{t("physicalProduct")}</option>
                <option value="hibrido">{t("hybridModel")}</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("annualRevenue")}
              </label>
              <select
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              >
                <option value="">{t("selectRange")}</option>
                <option value="ate100k">{`${t("upTo")} ${CURRENCY_SYMBOL} 100.000`}</option>
                <option value="100k500k">{`${CURRENCY_SYMBOL} 100.001 ${t("toRange")} ${CURRENCY_SYMBOL} 500.000`}</option>
                <option value="500k2m">{`${CURRENCY_SYMBOL} 500.001 ${t("toRange")} ${CURRENCY_SYMBOL} 2.000.000`}</option>
                <option value="2m10m">{`${CURRENCY_SYMBOL} 2.000.001 ${t("toRange")} ${CURRENCY_SYMBOL} 10.000.000`}</option>
                <option value="10m50m">{`${CURRENCY_SYMBOL} 10.000.001 ${t("toRange")} ${CURRENCY_SYMBOL} 50.000.000`}</option>
                <option value="acima50m">{`${t("above")} ${CURRENCY_SYMBOL} 50.000.000`}</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("operatingCountries")}
              </label>
              <input
                key={t("operatingCountriesDefault")}
                type="text"
                defaultValue={t("operatingCountriesDefault")}
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
                placeholder={t("operatingCountriesPlaceholder")}
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-lia-text-primary mb-3 block">
              {t("mainProducts")}
            </label>
            <textarea
              key={t("mainProductsDefault")}
              rows={3}
              defaultValue={t("mainProductsDefault")}
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              placeholder={t("mainProductsPlaceholder")}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export function BranchesSection() {
  const t = useTranslations("settings.branchesSection")
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Network className="w-4 h-4" />
              {t("title")}
            </div>
            <Button className="gap-2">
              <Plus className="w-4 h-4" />
              {t("newBranch")}
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              {
                id: 1,
                name: t("branch1Name"),
                cnpj:"12.345.678/0001-90",
                address: t("branch1Address"),
                typeKey:"headquarters",
                manager:"Ana Silva",
                employees: 450,
              },
              {
                id: 2,
                name: t("branch2Name"),
                cnpj:"12.345.678/0002-71",
                address: t("branch2Address"),
                typeKey:"branch",
                manager:"Carlos Santos",
                employees: 280,
              },
              {
                id: 3,
                name: t("branch3Name"),
                cnpj:"12.345.678/0003-52",
                address: t("branch3Address"),
                typeKey:"branch",
                manager:"Maria Costa",
                employees: 150,
              }
            ].map((branch) => (
              <div key={branch.id} className="p-4 border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h4 className="font-medium text-lia-text-primary">{branch.name}</h4>
                    <p className="text-sm text-lia-text-primary">{t("cnpjLabel")} {branch.cnpj}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Chip variant="neutral" muted>
                      {t(branch.typeKey as never)}
                    </Chip>
                    <Chip variant="success">
                      {t("statusActive")}
                    </Chip>
                    <Button variant="ghost" size="sm">
                      <Edit className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-lia-text-primary">{t("addressLabel")}</span>
                    <p className="font-medium text-lia-text-primary">{branch.address}</p>
                  </div>
                  <div>
                    <span className="text-lia-text-primary">{t("managerLabel")}</span>
                    <p className="font-medium text-lia-text-primary">{branch.manager}</p>
                  </div>
                  <div>
                    <span className="text-lia-text-primary">{t("employeesLabel")}</span>
                    <p className="font-medium text-lia-text-primary">{branch.employees}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
