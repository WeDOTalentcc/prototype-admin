"use client"

import React from "react"
import { SmartImportDropArea } from "./smart-import/SmartImportDropArea"
import { SmartImportPreview } from "./smart-import/SmartImportPreview"
import { SmartImportStatusCard } from "./smart-import/SmartImportStatusCard"
import { useSmartImport } from "./smart-import/useSmartImport"

interface SmartImportZoneProps {
  title: string
  description: string
  importEndpoint: string
  onImportSuccess: () => void
  expectedFields: string[]
  templateDownloadEndpoint?: string
  disabled?: boolean
}

export function SmartImportZone({
  title,
  description,
  importEndpoint,
  onImportSuccess,
  expectedFields,
  templateDownloadEndpoint,
  disabled = false,
}: SmartImportZoneProps) {
  const {
    state,
    isDragging,
    file,
    previewData,
    errorMessage,
    successMessage,
    fileInputRef,
    resetState,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    handleFileSelect,
    handleConfirmImport,
    handleDownloadTemplate,
  } = useSmartImport({
    importEndpoint,
    expectedFields,
    templateDownloadEndpoint,
    disabled,
    onImportSuccess,
  })

  switch (state) {
    case 'uploading':
      return <SmartImportStatusCard variant="uploading" fileName={file?.name} />
    case 'analyzing':
      return <SmartImportStatusCard variant="analyzing" />
    case 'preview':
      return (
        <SmartImportPreview
          fileName={file?.name}
          previewData={previewData}
          onCancel={resetState}
          onConfirm={handleConfirmImport}
        />
      )
    case 'importing':
      return (
        <SmartImportStatusCard
          variant="importing"
          totalRows={previewData?.totalRows}
        />
      )
    case 'success':
      return (
        <SmartImportStatusCard
          variant="success"
          message={successMessage}
          onReset={resetState}
        />
      )
    case 'error':
      return (
        <SmartImportStatusCard
          variant="error"
          message={errorMessage}
          onReset={resetState}
        />
      )
    default:
      return (
        <SmartImportDropArea
          title={title}
          description={description}
          expectedFields={expectedFields}
          templateDownloadEndpoint={templateDownloadEndpoint}
          disabled={disabled}
          isDragging={isDragging}
          fileInputRef={fileInputRef}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onFileSelect={handleFileSelect}
          onDownloadTemplate={handleDownloadTemplate}
        />
      )
  }
}
