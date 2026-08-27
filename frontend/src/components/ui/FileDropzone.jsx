import { useDropzone } from 'react-dropzone'
import { Upload } from 'lucide-react'

export default function FileDropzone({
  onDrop,
  accept = { 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'] },
  multiple = false,
  label = 'Drop your file here, or click to browse',
  hint = 'Supports PDF, DOCX — max 5MB',
  file,
}) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    multiple,
  })

  return (
    <div
      {...getRootProps()}
      style={{
        border:       `2px dashed ${isDragActive ? 'var(--primary)' : 'var(--gray-300)'}`,
        borderRadius: 'var(--radius)',
        padding:      '32px 24px',
        textAlign:    'center',
        cursor:       'pointer',
        background:   isDragActive ? 'var(--primary-light)' : 'var(--input-bg, var(--gray-50))',
        transition:   'all 0.15s, background-color 0.3s ease',
      }}
    >
      <input {...getInputProps()} />
      <Upload size={28} color={isDragActive ? 'var(--primary)' : 'var(--gray-400)'} />
      <p style={{ marginTop: 10, color: 'var(--gray-600)', fontSize: 14 }}>
        {file ? `✅ ${file.name}` : label}
      </p>
      <p style={{ marginTop: 4, color: 'var(--gray-400)', fontSize: 12 }}>{hint}</p>
    </div>
  )
}