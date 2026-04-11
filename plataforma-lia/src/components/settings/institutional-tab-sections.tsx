"use client"

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
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Building className="w-4 h-4" />
            Informações Básicas
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                Razão Social
              </label>
              <input
                type="text"
                defaultValue="Sodexo do Brasil Comercial S.A."
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                Nome Fantasia
              </label>
              <input
                type="text"
                defaultValue="Sodexo Brasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                CNPJ
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
                Inscrição Estadual
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
                Data de Fundação
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
                Número de Funcionários
              </label>
              <select
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              >
                <option>1-10 funcionários</option>
                <option>11-50 funcionários</option>
                <option>51-200 funcionários</option>
                <option>201-1000 funcionários</option>
                <option>1001-5000 funcionários</option>
                <option>5000+ funcionários</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                Site Institucional
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
                Email Principal
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
                Telefone Principal
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
                WhatsApp Corporativo
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
              Descrição da Empresa
            </label>
            <textarea
              rows={4}
              defaultValue="A Sodexo é uma empresa francesa líder mundial em serviços de alimentação e facilities management, presente em 55 países. No Brasil desde 1997, oferece soluções integradas que melhoram a qualidade de vida diária."
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Logotipo da Empresa</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-xl p-6 text-center bg-lia-bg-secondary dark:bg-lia-bg-secondary">
            <Upload className="w-8 h-8 mx-auto mb-2 text-lia-text-primary" />
            <p className="text-sm text-lia-text-primary mb-2">
              Faça upload do logotipo da empresa
            </p>
            <p className="text-xs text-lia-text-primary">PNG, JPG ou SVG até 2MB • Tamanho recomendado: 400x400px</p>
            <Button variant="outline" className="mt-3" size="sm">
              Escolher Arquivo
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export function AddressSection({ onSettingsChange }: SectionProps) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Globe className="w-4 h-4" />
            Endereço da Matriz
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                CEP
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
                Logradouro
              </label>
              <input
                type="text"
                defaultValue="Rua Dr. Geraldo Campos Moreira"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                Número
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
                Complemento
              </label>
              <input
                type="text"
                placeholder="Andar, sala, bloco..."
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                Bairro
              </label>
              <input
                type="text"
                defaultValue="Cidade Monções"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                Cidade
              </label>
              <input
                type="text"
                defaultValue="São Paulo"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                Estado
              </label>
              <select
                defaultValue="SP"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
              >
                <option value="">Selecione o estado</option>
                <option value="AC">Acre</option>
                <option value="AL">Alagoas</option>
                <option value="AP">Amapá</option>
                <option value="AM">Amazonas</option>
                <option value="BA">Bahia</option>
                <option value="CE">Ceará</option>
                <option value="DF">Distrito Federal</option>
                <option value="ES">Espírito Santo</option>
                <option value="GO">Goiás</option>
                <option value="MA">Maranhão</option>
                <option value="MT">Mato Grosso</option>
                <option value="MS">Mato Grosso do Sul</option>
                <option value="MG">Minas Gerais</option>
                <option value="PA">Pará</option>
                <option value="PB">Paraíba</option>
                <option value="PR">Paraná</option>
                <option value="PE">Pernambuco</option>
                <option value="PI">Piauí</option>
                <option value="RJ">Rio de Janeiro</option>
                <option value="RN">Rio Grande do Norte</option>
                <option value="RS">Rio Grande do Sul</option>
                <option value="RO">Rondônia</option>
                <option value="RR">Roraima</option>
                <option value="SC">Santa Catarina</option>
                <option value="SP">São Paulo</option>
                <option value="SE">Sergipe</option>
                <option value="TO">Tocantins</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-lia-text-primary mb-3 block">
              País
            </label>
            <select
              defaultValue="BR"
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary"
            >
              <option value="BR">Brasil</option>
              <option value="US">Estados Unidos</option>
              <option value="FR">França</option>
              <option value="DE">Alemanha</option>
              <option value="GB">Reino Unido</option>
            </select>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
