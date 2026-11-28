import { useCallback, useEffect, useMemo, useState } from 'react'
import { platformApi, type SubjectSummary, type SystemStatus } from './api/platform'
import { AppShell, type NavSection } from './components/AppShell'
import { LandingView } from './sections/LandingView'
import { OverviewSection } from './sections/OverviewSection'
import { ContractsSection } from './sections/ContractsSection'
import { DocumentsSection } from './sections/DocumentsSection'
import { SimulationsSection } from './sections/SimulationsSection'
import { VerificationProofSection } from './sections/VerificationProofSection'
import { AnalysisGuardianSection } from './sections/AnalysisGuardianSection'
import { AuditSettingsSection } from './sections/AuditSettingsSection'

const CUSTOM_SUBJECTS_KEY = 'fp_custom_subjects'
const DEFAULT_SUBJECTS = ['merchant-settlement-q1']

function loadCustomSubjects(): string[] {
  if (typeof window === 'undefined') return DEFAULT_SUBJECTS
  try {
    const raw = window.localStorage.getItem(CUSTOM_SUBJECTS_KEY)
    const parsed = raw ? (JSON.parse(raw) as string[]) : []
    const clean = Array.isArray(parsed)
      ? parsed.map((s) => String(s).trim()).filter(Boolean)
      : []
    return clean.length > 0 ? clean : DEFAULT_SUBJECTS
  } catch {
    return DEFAULT_SUBJECTS
  }
}

export function App() {
  const [view, setView] = useState<'landing' | 'workspace'>('landing')
  const [activeSection, setActiveSection] = useState<NavSection>('overview')
  const [workspaceSubject, setWorkspaceSubject] = useState('merchant-settlement-q1')
  const [customSubjects, setCustomSubjects] = useState<string[]>(loadCustomSubjects)
  const [dbSubjects, setDbSubjects] = useState<SubjectSummary[]>([])
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)

  const refreshSystem = useCallback(async () => {
    try {
      const status = await platformApi.systemStatus()
      setSystemStatus(status)
    } catch {
      setSystemStatus(null)
    }
  }, [])

  const refreshSubjects = useCallback(async () => {
    try {
      const list = await platformApi.listSubjects()
      setDbSubjects(list)
    } catch {
      // Keep local subjects if endpoint is unreachable
    }
  }, [])

  useEffect(() => {
    void refreshSystem()
    void refreshSubjects()
  }, [refreshSystem, refreshSubjects])

  const subjects = useMemo<SubjectSummary[]>(() => {
    const byName = new Map<string, SubjectSummary>()
    for (const s of dbSubjects) {
      byName.set(s.subject, s)
    }
    const ensure = new Set<string>([
      ...DEFAULT_SUBJECTS,
      ...customSubjects,
      workspaceSubject.trim(),
    ])
    for (const name of ensure) {
      if (name && !byName.has(name)) {
        byName.set(name, {
          subject: name,
          proof_count: 0,
          ready_count: 0,
          latest_status: 'new',
          latest_confidence: '0.00',
        })
      }
    }
    return Array.from(byName.values()).sort((a, b) =>
      a.subject.localeCompare(b.subject),
    )
  }, [dbSubjects, customSubjects, workspaceSubject])

  const addSubject = useCallback((rawName: string) => {
    const clean = rawName.trim()
    if (!clean) return
    setCustomSubjects((prev) => {
      const next = prev.includes(clean) ? prev : [...prev, clean]
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(CUSTOM_SUBJECTS_KEY, JSON.stringify(next))
      }
      return next
    })
    setWorkspaceSubject(clean)
  }, [])

  const removeCustomSubject = useCallback(
    (name: string) => {
      setCustomSubjects((prev) => {
        const next = prev.filter((item) => item !== name)
        const finalNext = next.length > 0 ? next : DEFAULT_SUBJECTS
        if (typeof window !== 'undefined') {
          window.localStorage.setItem(CUSTOM_SUBJECTS_KEY, JSON.stringify(finalNext))
        }
        return finalNext
      })
      if (workspaceSubject === name) {
        const fallback = subjects.find((s) => s.subject !== name)?.subject || 'merchant-settlement-q1'
        setWorkspaceSubject(fallback)
      }
    },
    [workspaceSubject, subjects],
  )

  return view === 'landing' ? (
    <LandingView
      systemStatus={systemStatus}
      onEnterWorkspace={(section = 'overview') => {
        setActiveSection(section)
        setView('workspace')
      }}
    />
  ) : (
    <AppShell
      activeSection={activeSection}
      onSelectSection={setActiveSection}
      onOpenLanding={() => setView('landing')}
      workspaceSubject={workspaceSubject}
      subjects={subjects}
      onChangeSubject={setWorkspaceSubject}
      onAddSubject={addSubject}
      systemStatus={systemStatus}
    >
      {activeSection === 'overview' && (
        <OverviewSection
          workspaceSubject={workspaceSubject}
          subjects={subjects}
          onSelectSubject={setWorkspaceSubject}
          onAddSubject={addSubject}
          onRemoveSubject={removeCustomSubject}
          systemStatus={systemStatus}
          onRefreshSystem={async () => {
            await Promise.all([refreshSystem(), refreshSubjects()])
          }}
          onNavigate={setActiveSection}
        />
      )}
      {activeSection === 'contracts' && <ContractsSection />}
      {activeSection === 'documents' && <DocumentsSection />}
      {activeSection === 'simulations' && <SimulationsSection />}
      {activeSection === 'verification' && (
        <VerificationProofSection
          workspaceSubject={workspaceSubject}
          subjects={subjects}
          onSelectSubject={setWorkspaceSubject}
          onProofChanged={refreshSubjects}
        />
      )}
      {activeSection === 'analysis' && (
        <AnalysisGuardianSection
          persistResults={systemStatus?.database === 'connected'}
        />
      )}
      {activeSection === 'audit' && <AuditSettingsSection />}
    </AppShell>
  )
}

export default App
