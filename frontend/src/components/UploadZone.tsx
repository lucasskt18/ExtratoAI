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
    <div>
      <div
        {...getRootProps()}
        className={['dropzone', isDragActive ? 'is-active' : '', busy ? 'is-busy' : ''].join(' ')}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0">
            <p className="text-[15px] font-extrabold tracking-tight text-[var(--color-brand-ink)]">
              {busy
                ? 'Processando fatura…'
                : isDragActive
                  ? 'Solte o PDF para importar'
                  : 'Importar fatura PDF'}
            </p>
            <p className="mt-1 text-sm font-medium text-[var(--color-muted)]">
              Arraste aqui ou clique para escolher. Inbox monitorada automaticamente.
            </p>
          </div>
          <span className="btn btn-primary shrink-0 pointer-events-none">
            {busy ? 'Aguarde…' : 'Escolher arquivo'}
          </span>
        </div>

        {inbox && (
          <div className="dropzone-meta">
            {inbox.pending_pdfs.length > 0 && (
              <span className="chip chip-warn">{inbox.pending_pdfs.length} pendente(s)</span>
            )}
            <span
              className="truncate text-[11px] font-medium text-[var(--color-muted-2)]"
              title={inbox.inbox_dir}
            >
              {inbox.inbox_dir}
            </span>
          </div>
        )}
      </div>

      {message && (
        <p className="mt-2 text-sm font-semibold text-[var(--color-success)]">{message}</p>
      )}
      {error && <p className="mt-2 text-sm font-semibold text-[var(--color-danger)]">{error}</p>}
    </div>
  )
}
