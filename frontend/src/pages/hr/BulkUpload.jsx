import { useState, useEffect } from 'react'
import { hrAPI } from '../../api/hr'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import { useDropzone } from 'react-dropzone'
import { Upload, CheckCircle, XCircle, FileText, Zap } from 'lucide-react'

export default function BulkUpload() {
  const [jobs, setJobs]         = useState([])
  const [jobId, setJobId]       = useState('')
  const [files, setFiles]       = useState([])
  const [uploading, setUploading] = useState(false)
  const [result, setResult]     = useState(null)
  const [mode, setMode]         = useState('files')  // files | zip

  useEffect(() => {
    hrAPI.getJobs({ status: 'open' }).then((r) => {
      const list = r.data.jobs || []
      setJobs(list)
      if (list.length > 0) setJobId(list[0].id)
    })
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop:   (f) => setFiles((p) => [...p, ...f]),
    accept:   mode === 'zip'
      ? { 'application/zip': ['.zip'] }
      : {
          'application/pdf': ['.pdf'],
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
        },
    multiple: mode !== 'zip',
  })

  const handleUpload = async () => {
    if (!jobId) { toast.error('Select a job first'); return }
    if (files.length === 0) { toast.error('Add files first'); return }
    setUploading(true)
    try {
      const fd = new FormData()
      if (mode === 'zip') {
        fd.append('file', files[0])
        const res = await hrAPI.bulkUploadZip(jobId, fd)
        setResult(res.data)
      } else {
        files.forEach((f) => fd.append('files', f))
        const res = await hrAPI.bulkUpload(jobId, fd)
        setResult(res.data)
      }
      toast.success('Upload complete!')
      setFiles([])
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const selectStyle = {
    width: '100%', padding: '9px 12px',
    border: '1px solid var(--gray-300)',
    borderRadius: 10, fontSize: 14, background: 'var(--input-bg, #fff)', color: 'var(--gray-800)',
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Bulk CV Upload</h1>
        <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>
          Upload multiple CVs at once — automatically parsed and validated
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '400px 1fr', gap: 24 }}>
        {/* Upload panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <h3 style={{ fontWeight: 600, marginBottom: 14 }}>Settings</h3>

            <div style={{ marginBottom: 14 }}>
              <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)', display: 'block', marginBottom: 6 }}>
                Select Job Post
              </label>
              <select value={jobId} onChange={(e) => setJobId(e.target.value)} style={selectStyle}>
                <option value="">-- Select a job --</option>
                {jobs.map((j) => <option key={j.id} value={j.id}>{j.title}</option>)}
              </select>
            </div>

            {/* Mode toggle */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
              {['files', 'zip'].map((m) => (
                <button key={m} onClick={() => { setMode(m); setFiles([]) }} style={{
                  flex: 1, padding: '8px', borderRadius: 8,
                  border: `2px solid ${mode === m ? 'var(--primary)' : 'var(--gray-200)'}`,
                  background: mode === m ? 'var(--primary-light)' : '#fff',
                  color: mode === m ? 'var(--primary)' : 'var(--gray-600)',
                  fontSize: 13, cursor: 'pointer', fontWeight: 500,
                }}>
                  {m === 'files' ? 'Multiple Files' : 'ZIP Archive'}
                </button>
              ))}
            </div>

            {/* Dropzone */}
            <div {...getRootProps()} style={{
              border: `2px dashed ${isDragActive ? 'var(--primary)' : 'var(--gray-300)'}`,
              borderRadius: 10, padding: '28px 16px',
              textAlign: 'center', cursor: 'pointer',
              background: isDragActive ? 'var(--primary-light)' : 'var(--gray-50)',
              transition: 'all 0.15s',
            }}>
              <input {...getInputProps()} />
              <Upload size={28} color={isDragActive ? 'var(--primary)' : 'var(--gray-400)'} />
              <p style={{ marginTop: 10, fontSize: 14, color: 'var(--gray-600)' }}>
                {isDragActive ? 'Drop files here' :
                  mode === 'zip' ? 'Drop ZIP file here or click to browse' :
                  'Drop PDF/DOCX files or click to browse'}
              </p>
              <p style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 4 }}>
                {mode === 'zip' ? '.zip archive only' : 'PDF and DOCX · max 5MB each'}
              </p>
            </div>

            {/* File list */}
            {files.length > 0 && (
              <div style={{ marginTop: 12 }}>
                <p style={{ fontSize: 12, color: 'var(--gray-500)', marginBottom: 6 }}>
                  {files.length} file{files.length > 1 ? 's' : ''} selected
                </p>
                <div style={{ maxHeight: 120, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {files.map((f, i) => (
                    <div key={i} style={{
                      display: 'flex', alignItems: 'center', gap: 6,
                      fontSize: 12, color: 'var(--gray-600)',
                      padding: '4px 8px', background: 'var(--gray-50)', borderRadius: 6,
                    }}>
                      <FileText size={12} color="var(--primary)" />
                      <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {f.name}
                      </span>
                      <span style={{ color: 'var(--gray-400)', flexShrink: 0 }}>
                        {(f.size / 1024).toFixed(0)}KB
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>

          <Button onClick={handleUpload} loading={uploading} fullWidth size="lg" disabled={!jobId || files.length === 0}>
            <Upload size={16} /> Upload & Parse CVs
          </Button>
        </div>

        {/* Results */}
        <div>
          {result ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Summary */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                {[
                  { label: 'Uploaded',       value: result.total_uploaded || result.total_in_zip,     color: 'var(--primary)' },
                  { label: 'Parsed OK',      value: result.successfully_parsed, color: 'var(--success)' },
                  { label: 'Failed',         value: result.failed,              color: 'var(--danger)'  },
                ].map((s) => (
                  <Card key={s.label} padding="16px" style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 28, fontWeight: 700, color: s.color }}>{s.value}</div>
                    <div style={{ fontSize: 12, color: 'var(--gray-500)', marginTop: 4 }}>{s.label}</div>
                  </Card>
                ))}
              </div>

              {/* Ready to rank */}
              {result.ready_to_rank && (
                <Card style={{ background: '#f0fdf4', border: '1px solid #bbf7d0' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <CheckCircle size={20} color="var(--success)" />
                      <div>
                        <p style={{ fontWeight: 600, color: 'var(--success)' }}>CVs Ready to Rank</p>
                        <p style={{ fontSize: 12, color: 'var(--gray-600)', marginTop: 2 }}>
                          {result.successfully_parsed} CVs uploaded and parsed successfully
                        </p>
                      </div>
                    </div>
                    <Button size="sm" onClick={() => window.location.href = '/hr/ranking'}>
                      <Zap size={13} /> Go to Ranking
                    </Button>
                  </div>
                </Card>
              )}

              {/* Parsed resumes */}
              {result.parsed_resumes?.length > 0 && (
                <Card>
                  <h3 style={{ fontWeight: 600, marginBottom: 12 }}>
                    Parsed Successfully ({result.parsed_resumes.length})
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {result.parsed_resumes.map((r) => (
                      <div key={r.resume_id} style={{
                        display: 'flex', alignItems: 'center', gap: 12,
                        padding: '10px 14px',
                        background: 'var(--gray-50)', borderRadius: 8,
                      }}>
                        <CheckCircle size={16} color="var(--success)" style={{ flexShrink: 0 }} />
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: 13, fontWeight: 500 }}>
                            {r.candidate_name !== 'Unknown' ? r.candidate_name : r.filename}
                          </div>
                          <div style={{ fontSize: 11, color: 'var(--gray-400)', marginTop: 1 }}>
                            {r.char_count?.toLocaleString()} chars · {r.skills_found?.length} skills
                            {r.experience_years ? ` · ${r.experience_years}y exp` : ''}
                          </div>
                        </div>
                        {r.skills_found?.slice(0, 3).map((s) => (
                          <Badge key={s} variant="info" style={{ fontSize: 10 }}>{s}</Badge>
                        ))}
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Failed files */}
              {result.failed_files?.length > 0 && (
                <Card>
                  <h3 style={{ fontWeight: 600, marginBottom: 12, color: 'var(--danger)' }}>
                    Failed ({result.failed_files.length})
                  </h3>
                  {result.failed_files.map((f, i) => (
                    <div key={i} style={{
                      display: 'flex', alignItems: 'center', gap: 10,
                      padding: '8px 12px', background: '#fef2f2',
                      borderRadius: 8, marginBottom: 6,
                    }}>
                      <XCircle size={15} color="var(--danger)" />
                      <div>
                        <div style={{ fontSize: 13 }}>{f.filename}</div>
                        <div style={{ fontSize: 11, color: 'var(--danger)', marginTop: 1 }}>{f.error}</div>
                      </div>
                    </div>
                  ))}
                </Card>
              )}
            </div>
          ) : (
            <Card style={{
              minHeight: 400, display: 'flex',
              alignItems: 'center', justifyContent: 'center',
              flexDirection: 'column', gap: 12,
            }}>
              <Upload size={48} color="var(--gray-300)" />
              <p style={{ color: 'var(--gray-400)', fontSize: 14 }}>
                Upload CVs to see parsed results here
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}