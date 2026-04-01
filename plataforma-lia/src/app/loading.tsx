export default function Loading() {
  return (
    <div className="min-h-content-lg flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-8 h-8 border-2 border-wedo-cyan border-t-transparent rounded-full animate-spin motion-reduce:animate-none" />
        <p className="text-sm text-lia-text-secondary">Carregando...</p>
      </div>
    </div>
  )
}
