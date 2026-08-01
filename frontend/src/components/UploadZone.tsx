import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { uploadPdf, type InboxStatus } from '../api/client'

type Props = {
  inbox: InboxStatus | null
  onUploaded: () => void
}

export function UploadZone({ inbox, onUploaded }: Props) {
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback(
    async (files: File[]) => {
      if (!files.length) return
      setBusy(true)
      setError(null)
      setMessage(null)
      try {
        for (const file of files) {
          const result = await uploadPdf(file)
          setMessage(`${result.message}: ${result.statement.source_filename}`)
        }
        onUploaded()
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Falha no upload')
      } finally {
        setBusy(false)
      }
    },
    [onUploaded],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: true,
    disabled: busy,
  })

  return (
    <section className="animate-fade-up-delay">
      <div
        {...getRootProps()}
        className={[
          'rounded-2xl border border-dashed px-5 py-7 transition-colors cursor-pointer',
          isDragActive
            ? 'border-[var(--color-accent)] bg-[var(--color-accent-soft)]'
            : 'border-[var(--color-line)] bg-[var(--color-panel)]/70 hover:border-[var(--color-accent)]',
          busy ? 'opacity-70 cursor-wait' : '',
        ].join(' ')}
      >
        <input {...getInputProps()} />
        <p className="font-[family-name:var(--font-display)] text-xl text-[var(--color-ink)]">
          {busy ? 'Processando fatura…' : 'Arraste PDFs de fatura aqui'}
        </p>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Ou clique para selecionar. Também monitoramos a pasta inbox automaticamente.
        </p>
        {inbox && (
          <p className="mt-3 text-xs text-[var(--color-muted)]">
            Inbox: <span className="font-medium text-[var(--color-ink)]">{inbox.inbox_dir}</span>
            {' · '}
            {inbox.processed_count} faturas importadas
            {inbox.pending_pdfs.length > 0 && (
              <span className="ml-1 text-[var(--color-warn)] animate-pulse-soft">
                · {inbox.pending_pdfs.length} pendente(s)
              </span>
            )}
          </p>
        )}
      </div>
      {message && <p className="mt-2 text-sm text-[var(--color-accent)]">{message}</p>}
      {error && <p className="mt-2 text-sm text-red-700">{error}</p>}
    </section>
  )
}
