"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { 
  Loader2, 
  CheckCircle2, 
  AlertCircle, 
  AlertTriangle,
  Mail,
  User,
  ShieldCheck
} from "lucide-react"
import { PortalFieldRenderer } from "../PortalFieldRenderer"
import { SENSITIVE_DATA_REQUEST_FIELDS } from "../_hooks/useDataRequest"
import type { useDataRequest } from "../_hooks/useDataRequest"

type DataRequestReturn = ReturnType<typeof useDataRequest>

interface DataRequestFormProps {
  hook: DataRequestReturn
}

export function DataRequestForm({ hook }: DataRequestFormProps) {
  const {
    step,
    portalData,
    errorMessage,
    otpCode,
    otpLoading,
    otpError,
    otpChannel,
    setOtpChannel,
    otpSent,
    otpResendTimer,
    otpInputRefs,
    formValues,
    formErrors,
    fileUploads,
    uploadProgress,
    submitting,
    saving,
    primaryColor,
    primaryBgColor,
    requestOTP,
    verifyOTP,
    handleOtpChange,
    handleOtpKeyDown,
    handleOtpPaste,
    handleFieldChange,
    handleFileChange,
    saveProgress,
    submitForm,
    consentChecked,
    setConsentChecked,
    hasSensitiveFields,
  } = hook

  if (step === "loading") {
    return (
      <div className="min-h-screen bg-lia-bg-primary dark:bg-lia-btn-primary-bg flex items-center justify-center p-4" role="status" aria-live="polite" aria-label="Carregando...">
        <div className="text-center" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-12 h-12 animate-spin motion-reduce:animate-none text-lia-text-tertiary dark:text-lia-text-secondary mx-auto mb-4" />
          <p className="text-lia-text-secondary dark:text-lia-text-tertiary">Carregando...</p>
        </div>
      </div>
    )
  }

  if (step === "error") {
    return (
      <div className="min-h-screen bg-lia-bg-primary dark:bg-lia-btn-primary-bg flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 text-center">
            <AlertCircle className="w-16 h-16 text-status-error mx-auto mb-4" />
            <h1 className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-tertiary mb-2">Ops!</h1>
            <p className="text-lia-text-secondary dark:text-lia-text-disabled">{errorMessage}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (step === "expired") {
    return (
      <div className="min-h-screen bg-lia-bg-primary dark:bg-lia-btn-primary-bg flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 text-center">
            <AlertCircle className="w-16 h-16 text-status-warning mx-auto mb-4" />
            <h1 className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-tertiary mb-2">Link Expirado</h1>
            <p className="text-lia-text-secondary dark:text-lia-text-disabled">{errorMessage}</p>
            <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary mt-4">
              Entre em contato com o recrutador para solicitar um novo link.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (step === "otp") {
    return (
      <div className="min-h-screen bg-lia-bg-primary dark:bg-lia-btn-primary-bg flex flex-col">
        {portalData?.branding.logo_url && (
          <div className="p-4 flex justify-center">
            <img
              src={portalData.branding.logo_url}
              alt="Logo"
              className="h-12 object-contain"
            />
          </div>
        )}

        <div className="flex-1 flex items-center justify-center p-4">
          <Card className="w-full max-w-md">
            <CardHeader className="text-center">
              <div
                className="w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center"
                style={{backgroundColor: primaryBgColor}}
              >
                <User className="w-8 h-8" style={{color: primaryColor}} />
              </div>
              <CardTitle className="text-xl">Olá, {portalData?.candidate_info.name}!</CardTitle>
              <CardDescription>
                Para sua segurança, precisamos verificar sua identidade.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {!otpSent ? (
                <>
                  <p className="text-sm text-lia-text-secondary dark:text-lia-text-disabled text-center">
                    Enviaremos um código de 6 dígitos para você.
                  </p>
                  
                  <div className="space-y-3">
                    <button
                      onClick={() => setOtpChannel("email")}
                      className={`w-full p-4 rounded-md border-2 flex items-center gap-3 transition-colors motion-reduce:transition-none ${
                        otpChannel === "email"
                          ? "border-lia-btn-primary-bg dark:border-lia-border-medium bg-lia-bg-secondary dark:bg-lia-bg-inverse"
                          : "border-lia-border-subtle hover:border-lia-border-default"
                      }`}
                    >
                      <Mail className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-muted" />
                      <div className="text-left">
                        <p className="text-sm font-medium">E-mail</p>
                        <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                          {portalData?.candidate_info.email_masked}
                        </p>
                      </div>
                    </button>
                  </div>

                  <Button
                    onClick={requestOTP}
                    disabled={otpLoading}
                    className="w-full h-12"
                    style={{backgroundColor: primaryColor}}
                  >
                    {otpLoading ? (
                      <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none" />
                    ) : (
                      "Enviar Código"
                    )}
                  </Button>
                </>
              ) : (
                <>
                  <p className="text-sm text-lia-text-secondary dark:text-lia-text-disabled text-center">
                    Digite o código de 6 dígitos enviado para{" "}
                    <span className="font-medium">
                      {portalData?.candidate_info.email_masked}
                    </span>
                  </p>

                  <div className="flex justify-center gap-2">
                    {otpCode.map((digit, index) => (
                      <input
                        key={`otp-${index}`}
                        ref={(el) => { otpInputRefs.current[index] = el }}
                        type="text"
                        inputMode="numeric"
                        maxLength={1}
                        value={digit}
                        onChange={(e) => handleOtpChange(index, e.target.value)}
                        onKeyDown={(e) => handleOtpKeyDown(index, e)}
                        onPaste={index === 0 ? handleOtpPaste : undefined}
                        className="w-12 h-14 text-center text-2xl font-semibold border-2 border-lia-border-default dark:border-lia-border-medium rounded-xl focus:border-lia-border-medium focus:outline-none focus:ring-2 focus:ring-lia-border-subtle dark:bg-lia-btn-primary-hover dark:text-lia-text-tertiary"
                      />
                    ))}
                  </div>

                  {otpError && (
                    <p className="text-sm text-status-error text-center flex items-center justify-center gap-1">
                      <AlertCircle className="w-4 h-4" />
                      {otpError}
                    </p>
                  )}

                  <Button
                    onClick={verifyOTP}
                    disabled={otpLoading || otpCode.join("").length !== 6}
                    className="w-full h-12"
                    style={{backgroundColor: primaryColor}}
                  >
                    {otpLoading ? (
                      <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none" />
                    ) : (
                      "Verificar"
                    )}
                  </Button>

                  <div className="text-center">
                    {otpResendTimer > 0 ? (
                      <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                        Reenviar código em {otpResendTimer}s
                      </p>
                    ) : (
                      <button
                        onClick={requestOTP}
                        disabled={otpLoading}
                        className="text-sm hover:underline"
                        style={{color: primaryColor}}
                      >
                        Reenviar código
                      </button>
                    )}
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  if (step === "completed") {
    return (
      <div className="min-h-screen bg-lia-bg-primary dark:bg-lia-btn-primary-bg flex flex-col">
        {portalData?.branding.logo_url && (
          <div className="p-4 flex justify-center">
            <img
              src={portalData.branding.logo_url}
              alt="Logo"
              className="h-12 object-contain"
            />
          </div>
        )}

        <div className="flex-1 flex items-center justify-center p-4">
          <Card className="w-full max-w-md">
            <CardContent className="pt-8 pb-8 text-center">
              <div
                className="w-20 h-20 rounded-full mx-auto mb-6 flex items-center justify-center"
                style={{backgroundColor: primaryBgColor}}
              >
                <CheckCircle2 className="w-10 h-10" style={{color: primaryColor}} />
              </div>
              <h1 className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-tertiary mb-3">
                Obrigado!
              </h1>
              <p className="text-lia-text-secondary dark:text-lia-text-disabled mb-6">
                {portalData?.branding.thank_you_message ||
                  "Seus dados foram enviados com sucesso. Entraremos em contato em breve."}
              </p>
              {portalData?.vacancy_info && (
                <div className="bg-lia-bg-secondary dark:bg-lia-btn-primary-hover rounded-xl p-4 text-left">
                  <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary uppercase tracking-wider mb-1" aria-live="polite" aria-atomic="true">
                    Vaga
                  </p>
                  <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-tertiary">
                    {portalData.vacancy_info.title}
                  </p>
                  {portalData.vacancy_info.department && (
                    <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                      {portalData.vacancy_info.department}
                    </p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-lia-bg-primary dark:bg-lia-btn-primary-bg flex flex-col">
      {portalData?.branding.logo_url && (
        <div className="p-4 flex justify-center bg-lia-bg-primary dark:bg-lia-btn-primary-hover border-b dark:border-lia-border-strong">
          <img
            src={portalData.branding.logo_url}
            alt="Logo"
            className="h-10 object-contain"
          />
        </div>
      )}

      <div className="sticky top-0 z-10 bg-lia-bg-primary dark:bg-lia-btn-primary-hover border-b dark:border-lia-border-strong px-4 py-3">
        <div className="max-w-lg mx-auto">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-lia-text-secondary dark:text-lia-text-tertiary">Progresso</span>
            <span className="text-xs font-semibold" style={{color: primaryColor}}>
              {Math.round(portalData?.completion_percentage || 0)}%
            </span>
          </div>
          <div className="relative h-2 bg-lia-interactive-active dark:bg-lia-bg-inverse rounded-full overflow-hidden">
            <div
              className="absolute left-0 top-0 h-full transition-[width,height] duration-500 rounded-full"
              style={{width: `${portalData?.completion_percentage || 0}%`,
                backgroundColor: primaryColor}}
            />
          </div>
        </div>
      </div>

      <div className="flex-1 p-4">
        <div className="max-w-lg mx-auto">
          {portalData?.branding.welcome_message && (
            <div className="mb-6 p-4 bg-lia-bg-primary dark:bg-lia-btn-primary-hover rounded-xl border dark:border-lia-border-strong">
              <p className="text-sm text-lia-text-secondary dark:text-lia-text-disabled">{portalData.branding.welcome_message}</p>
            </div>
          )}

          {portalData?.vacancy_info && (
            <div className="mb-6 p-4 bg-lia-bg-primary dark:bg-lia-btn-primary-hover rounded-xl border dark:border-lia-border-strong">
              <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary uppercase tracking-wider mb-1">
                Preenchendo dados para
              </p>
              <p className="text-base font-medium text-lia-text-primary dark:text-lia-text-tertiary">
                {portalData.vacancy_info.title}
              </p>
              {portalData.vacancy_info.department && (
                <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">{portalData.vacancy_info.department}</p>
              )}
            </div>
          )}

          {/* Phase 3a: LGPD Art. 11 sensitive-field consent block */}
          {hasSensitiveFields && (
            <Card className="mb-6 border-amber-200 dark:border-amber-700 bg-amber-50 dark:bg-amber-950">
              <CardContent className="pt-5 space-y-4">
                <div className="flex items-start gap-3">
                  <ShieldCheck className="w-5 h-5 text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-semibold text-amber-800 dark:text-amber-300 mb-1">
                      Este formulario coleta dados sensiveis (LGPD Art. 11)
                    </p>
                    <p className="text-xs text-amber-700 dark:text-amber-400">
                      Sua privacidade e protegida. Os dados abaixo sao coletados somente com seu consentimento
                      explicito, conforme a Lei Geral de Protecao de Dados.
                    </p>
                  </div>
                </div>

                <div className="pl-8">
                  <p className="text-xs font-medium text-amber-700 dark:text-amber-400 mb-2">
                    Campos sensiveis que serao coletados:
                  </p>
                  <ul className="space-y-1">
                    {portalData?.fields
                      .filter((f) => SENSITIVE_DATA_REQUEST_FIELDS.has(f.name) || SENSITIVE_DATA_REQUEST_FIELDS.has(f.field_type))
                      .map((f) => (
                        <li key={f.name} className="text-xs text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
                          <AlertTriangle className="w-3 h-3" />
                          {f.label}
                        </li>
                      ))}
                  </ul>
                </div>

                <div className="pl-8">
                  <p className="text-xs text-amber-600 dark:text-amber-500 mb-3">
                    <strong>Base legal:</strong> Art. 11, paragrafo 2, II LGPD — Consentimento explicito do titular
                  </p>
                  <label className="flex items-start gap-3 cursor-pointer">
                    <Checkbox
                      id="lgpd-art11-consent"
                      checked={consentChecked}
                      onCheckedChange={(v) => setConsentChecked(v === true)}
                      className="mt-0.5 border-amber-500 data-[state=checked]:bg-amber-600"
                    />
                    <span className="text-sm text-amber-800 dark:text-amber-300 leading-snug">
                      Consinto com a coleta e tratamento dos dados sensiveis listados acima para fins do
                      processo seletivo, conforme a LGPD.
                    </span>
                  </label>
                </div>
              </CardContent>
            </Card>
          )}

          <Card className="mb-6">
            <CardContent className="pt-6 space-y-6">
              {portalData?.fields.map((field) => (
              <PortalFieldRenderer
                key={field.name}
                field={field}
                value={formValues[field.name] || ""}
                error={formErrors[field.name]}
                upload={fileUploads[field.name]}
                uploadProgress={uploadProgress[field.name]}
                completedFile={portalData?.fields_completed.find((c) => c.name === field.name && c.file_url)}
                onChange={handleFieldChange}
                onFileChange={handleFileChange}
              />
            ))}
            </CardContent>
          </Card>

          <div className="space-y-3 pb-8">
            <Button
              onClick={submitForm}
              disabled={submitting || saving || (hasSensitiveFields && !consentChecked)}
              className="w-full h-12 text-base font-medium"
              style={{backgroundColor: primaryColor}}
            >
              {submitting ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none mr-2" />
                  Enviando...
                </>
              ) : (
                "Enviar Dados"
              )}
            </Button>

            <Button
              onClick={saveProgress}
              disabled={submitting || saving}
              variant="outline"
              className="w-full h-10"
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none mr-2" />
                  Salvando...
                </>
              ) : (
                "Salvar e Continuar Depois"
              )}
            </Button>

            {portalData?.branding.privacy_policy_url && (
              <p className="text-xs text-center text-lia-text-secondary dark:text-lia-text-tertiary">
                Ao enviar, você concorda com nossa{" "}
                <a
                  href={portalData.branding.privacy_policy_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline hover:text-lia-text-primary dark:hover:text-lia-text-muted"
                >
                  Política de Privacidade
                </a>
                {portalData.branding.terms_url && (
                  <>
                    {" "}e{" "}
                    <a
                      href={portalData.branding.terms_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline hover:text-lia-text-primary dark:hover:text-lia-text-muted"
                    >
                      Termos de Uso
                    </a>
                  </>
                )}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
