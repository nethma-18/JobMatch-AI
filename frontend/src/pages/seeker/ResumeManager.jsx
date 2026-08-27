import { useState, useEffect } from 'react'
import { sharedAPI } from '../../api/shared'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import Modal from '../../components/ui/Modal'
import { fmtDate } from '../../utils/helpers'
import { Upload, Trash2, Eye, FileText } from 'lucide-react'

export default function ResumeManager() {
  const [resumes, setResumes] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  
  // Details Modal
  const [selectedResume, setSelectedResume] = useState(null)
  const [detailsOpen, setDetailsOpen] = useState(false)

  const loadResumes = () => {
    sharedAPI.getMyResumes()
      .then((res) => {
        setResumes(res.data.resumes || [])
      })
      .catch(() => {
        toast.error('Failed to load resumes')
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadResumes()
  }, [])

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      if (!file.name.lowerCase?.endsWith('.pdf') && !file.name.endsWith('.pdf')) {
        toast.error('Only PDF files are supported')
        return
      }
      setSelectedFile(file)
    }
  }

  const handleUpload = (e) => {
    e.preventDefault()
    if (!selectedFile) return

    setUploading(true)
    const formData = new FormData()
    formData.append('file', selectedFile)

    sharedAPI.uploadResume(formData)
      .then(() => {
        toast.success('Resume uploaded and parsed successfully')
        setSelectedFile(null)
        loadResumes()
      })
      .catch((err) => {
        const msg = err.response?.data?.detail || 'Failed to upload resume'
        toast.error(msg)
      })
      .finally(() => setUploading(false))
  }

  const handleDelete = (id) => {
    if (!window.confirm('Are you sure you want to delete this resume?')) return

    sharedAPI.deleteResume(id)
      .then(() => {
        toast.success('Resume deleted successfully')
        loadResumes()
      })
      .catch(() => {
        toast.error('Failed to delete resume')
      })
  }

  const handleViewDetails = (id) => {
    sharedAPI.getResume(id)
      .then((res) => {
        setSelectedResume(res.data)
        setDetailsOpen(true)
      })
      .catch(() => {
        toast.error('Failed to load resume details')
      })
  }

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '40px' }}>Loading resumes...</div>
  }

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: 700 }}>Resume Manager</h1>
          <p style={{ color: 'var(--gray-500)', marginTop: '4px' }}>
            Upload, parse, and manage your PDF resumes.
          </p>
        </div>
      </div>

      {/* Upload Form */}
      <Card style={{ marginBottom: '28px' }}>
        <h2 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '14px' }}>Upload New Resume</h2>
        <form onSubmit={handleUpload} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              id="resume-file"
              style={{ display: 'none' }}
            />
            <label
              htmlFor="resume-file"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 14px',
                border: '1px dashed var(--gray-300)',
                borderRadius: 'var(--radius)',
                cursor: 'pointer',
                fontSize: '13px',
                color: 'var(--gray-600)',
                background: 'var(--input-bg, #fff)',
                width: '100%',
              }}
            >
              <Upload size={16} />
              {selectedFile ? selectedFile.name : 'Choose a PDF resume...'}
            </label>
          </div>
          <Button type="submit" disabled={!selectedFile || uploading}>
            {uploading ? 'Processing...' : 'Upload & Parse'}
          </Button>
        </form>
      </Card>

      {/* Resume List */}
      <h2 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '14px' }}>My Resumes</h2>
      {resumes.length === 0 ? (
        <Card style={{ textAlign: 'center', padding: '40px', color: 'var(--gray-500)' }}>
          <FileText size={48} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
          <p>No resumes uploaded yet. Choose a PDF file above to get started.</p>
        </Card>
      ) : (
        <Card padding="0">
          {resumes.map((r, i) => (
            <div
              key={r._id}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '16px 20px',
                borderBottom: i < resumes.length - 1 ? '1px solid var(--gray-100)' : 'none',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '40px', height: '40px', borderRadius: '8px',
                  background: 'var(--primary-light)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: 'var(--primary)'
                }}>
                  <FileText size={20} />
                </div>
                <div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--gray-800)' }}>
                    {r.original_filename}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--gray-500)', marginTop: '2px' }}>
                    Uploaded on {fmtDate(r.uploaded_at)} · {r.file_size_mb ? `${r.file_size_mb.toFixed(2)} MB` : 'N/A'}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <Badge variant={r.processing_status === 'completed' ? 'success' : 'danger'}>
                  {r.processing_status}
                </Badge>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => handleViewDetails(r._id)}
                    style={{
                      background: 'none', border: 'none', color: 'var(--primary)',
                      cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center'
                    }}
                    title="View details & parsed data"
                  >
                    <Eye size={16} />
                  </button>
                  <button
                    onClick={() => handleDelete(r._id)}
                    style={{
                      background: 'none', border: 'none', color: 'var(--danger)',
                      cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center'
                    }}
                    title="Delete resume"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </Card>
      )}

      {/* Details Modal */}
      {selectedResume && (
        <Modal
          open={detailsOpen}
          onClose={() => setDetailsOpen(false)}
          title={`Resume Details: ${selectedResume.original_filename}`}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxHeight: '70vh', overflowY: 'auto', paddingRight: '4px' }}>
            
            {/* Parsed Basic Info */}
            <div>
              <h3 style={{ fontSize: '14px', fontWeight: 600, borderBottom: '1px solid var(--gray-200)', paddingBottom: '6px', marginBottom: '10px' }}>
                Parsed Information
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px' }}>
                <div><strong>Email:</strong> {selectedResume.parsed_data?.email || 'Not found'}</div>
                <div><strong>Phone:</strong> {selectedResume.parsed_data?.phone || 'Not found'}</div>
                <div>
                  <strong>URLs found:</strong>
                  {selectedResume.parsed_data?.urls && selectedResume.parsed_data.urls.length > 0 ? (
                    <ul style={{ margin: '4px 0 0 16px', padding: 0 }}>
                      {selectedResume.parsed_data.urls.map((url, idx) => (
                        <li key={idx}>
                          <a href={url.startsWith('http') ? url : `https://${url}`} target="_blank" rel="noreferrer" style={{ color: 'var(--primary)' }}>
                            {url}
                          </a>
                        </li>
                      ))}
                    </ul>
                  ) : ' None'}
                </div>
              </div>
            </div>

            {/* Extracted Raw Text Preview */}
            <div>
              <h3 style={{ fontSize: '14px', fontWeight: 600, borderBottom: '1px solid var(--gray-200)', paddingBottom: '6px', marginBottom: '10px' }}>
                Extracted Text Preview
              </h3>
              <pre style={{
                background: 'var(--gray-50)',
                padding: '12px',
                borderRadius: 'var(--radius)',
                fontSize: '12px',
                whiteSpace: 'pre-wrap',
                fontFamily: 'monospace',
                maxHeight: '250px',
                overflowY: 'auto',
                border: '1px solid var(--gray-200)',
                color: 'var(--gray-700)',
              }}>
                {selectedResume.extracted_text || 'No text extracted.'}
              </pre>
            </div>
            
          </div>
        </Modal>
      )}
    </div>
  )
}
