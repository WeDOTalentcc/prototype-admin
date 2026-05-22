"use client"

import { Card, CardContent } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import {
  FileText, Video, Mic, Image, Award, Eye, Download, Play, Upload, Plus,
} from"lucide-react"

type CandidateRecord = {
  name: string
  avatar_url?: string
  avatar?: string
  [key: string]: unknown
}

interface CandidatePageFilesTabProps {
  _candidate: CandidateRecord
  isDragging: boolean
  setIsDragging: (v: boolean) => void
  setSelectedFile: (file: Record<string, unknown>) => void
  setPreviewType: (type: string) => void
  setShowPreview: (v: boolean) => void
  setShowVideoModal: (v: { title: string; url: string } | null) => void
}

export function CandidatePageFilesTab({
  _candidate,
  isDragging,
  setIsDragging,
  setSelectedFile,
  setPreviewType,
  setShowPreview,
  setShowVideoModal,
}: CandidatePageFilesTabProps) {
  return (
    <div className="space-y-4">
      {/* Upload Area */}
      <Card className="border-2 border-dashed border-lia-border-default dark:border-lia-border-default hover:border-lia-border-medium dark:hover:border-lia-border-medium">
        <CardContent className="p-6">
          <div
            className={`text-center cursor-pointer transition-colors ${isDragging ? 'bg-blue-50 dark:bg-blue-900/20' : ''}`}
            onDragOver={(e) => {
              e.preventDefault()
              setIsDragging(true)
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => {
              e.preventDefault()
              setIsDragging(false)
            }}
            onClick={() => {
              const input = document.createElement("input")
              input.type ="file"
              input.multiple = true
              input.accept =".pdf,.doc,.docx,.jpg,.jpeg,.png,.mp4,.mov,.mp3,.wav,.m4a,.webm,.ogg"
              input.onchange = () => {}
              input.click()
            }}
          >
            <Upload className="w-8 h-8 text-lia-text-secondary mx-auto mb-3" />
            <h3 className="text-sm font-medium mb-2">
              {isDragging ?"Solte os arquivos aqui" :"Arraste arquivos ou clique para selecionar"}
            </h3>
            <p className="text-xs text-lia-text-secondary">PDF, DOC, JPG, PNG, MP4, MP3, WAV até 25MB</p>
            <Button className="mt-3 h-7 text-xs">
              <Plus className="w-3 h-3 mr-1" />
              Selecionar Arquivos
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Lista de Arquivos */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* CV */}
        <Card className="hover:transition-shadow">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <FileText className="w-5 h-5 text-status-error" />
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-sm truncate">CV_{(_candidate.name as string).replace("","_")}_2025.pdf</h4>
                <p className="text-xs text-lia-text-primary">2.1 MB • há 3 dias</p>
                <div className="flex gap-1 mt-2">
                  <Chip density="relaxed" variant="neutral" muted >✓ Verificado</Chip>
                  <Chip density="relaxed" variant="neutral" muted className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary">LIA: 95%</Chip>
                </div>
              </div>
            </div>
            <div className="flex gap-1 mt-3">
              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0"
                onClick={() => {
                  setSelectedFile({ name:"CV_" + (_candidate.name as string) +".pdf", type:"pdf" })
                  setPreviewType("pdf")
                  setShowPreview(true)
                }}
              >
                <Eye className="w-3.5 h-3.5" />
              </Button>
              <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                <Download className="w-3.5 h-3.5" />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Portfolio */}
        <Card className="hover:transition-shadow">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <FileText className="w-5 h-5 text-wedo-purple" />
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-sm truncate">Portfolio_UX_2025.pdf</h4>
                <p className="text-xs text-lia-text-primary">12.3 MB • há 1 dia</p>
                <div className="flex gap-1 mt-2">
                  <Chip density="relaxed" variant="neutral" muted >✓ Verificado</Chip>
                  <Chip density="relaxed" variant="neutral" muted >Destacado</Chip>
                </div>
              </div>
            </div>
            <div className="flex gap-1 mt-3">
              <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                <Eye className="w-3.5 h-3.5" />
              </Button>
              <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                <Download className="w-3.5 h-3.5" />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Vídeo de Apresentação */}
        <Card className="hover:transition-shadow">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Video className="w-5 h-5 text-status-error" />
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-sm truncate">Apresentacao_Pessoal.mp4</h4>
                <p className="text-xs text-lia-text-primary">25.4 MB • 3:45 min</p>
                <div className="flex gap-1 mt-2">
                  <Chip density="relaxed" variant="neutral" muted >✓ Analisado</Chip>
                  <Chip density="relaxed" variant="neutral" muted >Triagem</Chip>
                </div>
              </div>
            </div>
            <div className="flex gap-1 mt-3">
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs gap-1"
                onClick={() => setShowVideoModal({ title:"Apresentação Pessoal", url:"video.mp4" })}
              >
                <Play className="w-3.5 h-3.5" />
                Assistir
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Vídeo de Case Técnico */}
        <Card className="hover:transition-shadow">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Video className="w-5 h-5 text-wedo-purple" />
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-sm truncate">Case_UX_Design.mp4</h4>
                <p className="text-xs text-lia-text-primary">45.2 MB • 8:20 min</p>
                <div className="flex gap-1 mt-2">
                  <Chip density="relaxed" variant="neutral" muted >Destaque</Chip>
                  <Chip density="relaxed" variant="neutral" muted >Nota: 88%</Chip>
                </div>
              </div>
            </div>
            <div className="flex gap-1 mt-3">
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs gap-1"
                onClick={() => setShowVideoModal({ title:"Case UX Design", url:"case.mp4" })}
              >
                <Play className="w-3.5 h-3.5" />
                Assistir
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Gravacao de Audio */}
        <Card className="hover:transition-shadow">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Mic className="w-5 h-5 text-lia-text-secondary" />
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-sm truncate">Triagem_Voz_{_candidate.name.split("")[0]}.mp3</h4>
                <p className="text-xs text-lia-text-primary">1.8 MB • 4:32 min • há 1 dia</p>
                <div className="flex gap-1 mt-2">
                  <Chip density="relaxed" variant="neutral" muted className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary">Triagem WSI</Chip>
                  <Chip density="relaxed" variant="neutral" muted >Nota: 92%</Chip>
                </div>
              </div>
            </div>
            <div className="flex gap-1 mt-3">
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs gap-1"
                onClick={() => {
                  setSelectedFile({
                    name: `Triagem_Voz_${_candidate.name.split("")[0]}.mp3`,
                    type:"audio",
                    transcription:"Olá, meu nome é Maria Oliveira e sou UX Designer há 8 anos. Trabalho atualmente na empresa XYZ como Design Lead...",
                    aiAnalysis: { confidence: 92, communication: 88, enthusiasm: 85, clarity: 90 },
                  })
                  setPreviewType("audio")
                  setShowPreview(true)
                }}
              >
                <Play className="w-3.5 h-3.5" />
                Ouvir
              </Button>
              <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                <Download className="w-3.5 h-3.5" />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Foto do Candidato */}
        <Card className="hover:transition-shadow">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Image className="w-5 h-5 text-status-success" />
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-sm truncate">foto_perfil.jpg</h4>
                <p className="text-xs text-lia-text-primary">456 KB • há 2 horas</p>
                <div className="flex gap-1 mt-2">
                  <Chip density="relaxed" variant="neutral" muted >✓ Verificado</Chip>
                </div>
              </div>
            </div>
            {(_candidate.avatar_url || _candidate.avatar) && (
              <div className="mt-3">
                <img
                  src={_candidate.avatar_url || _candidate.avatar}
                  alt="Preview"
                  className="w-full h-24 rounded-md object-cover cursor-pointer hover:opacity-80 transition-opacity motion-reduce:transition-none"
                  onClick={() => {
                    setSelectedFile({
                      name:"foto_perfil.jpg",
                      type:"image",
                      url: _candidate.avatar_url || _candidate.avatar,
                    })
                    setPreviewType("image")
                    setShowPreview(true)
                  }}
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Certificados */}
        <Card className="hover:transition-shadow">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Award className="w-5 h-5 text-wedo-orange" />
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-sm truncate">Certificados.zip</h4>
                <p className="text-xs text-lia-text-primary">3.2 MB • há 1 semana</p>
                <div className="flex gap-1 mt-2">
                  <Chip density="relaxed" variant="neutral" muted >5 arquivos</Chip>
                </div>
              </div>
            </div>
            <div className="flex gap-1 mt-3">
              <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                <Download className="w-3.5 h-3.5" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
