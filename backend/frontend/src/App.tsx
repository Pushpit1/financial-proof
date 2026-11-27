import { useCallback, useEffect, useState } from 'react'
import { platformApi, type SystemStatus } from './api/platform'
import { AppShell, type NavSection } from './components/AppShell'
import { LandingView } from './sections/LandingView'
import { OverviewSection } from './sections/OverviewSection'
import { ContractsSection } from './sections/ContractsSection'
import { DocumentsSection } from './sections/DocumentsSection'
import { SimulationsSection } from './sections/SimulationsSection'
import { VerificationProofSection } from './sections/VerificationProofSection'
import { AnalysisGuardianSection } from './sections/AnalysisGuardianSection'
import { AuditSettingsSection } from './sections/AuditSettingsSection'

export function App() {
  const [view, setView] = useState<'landing' | 'workspace'>('landing')
  const [activeSection, setActiveSection] = useState<NavSection>('overview')
  const [workspaceSubject, setWorkspaceSubject] = useState('merchant-settlement-q1')
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)

  const refreshSystem = useCallback(async () => {
    try {
      const status = await platformApi.systemStatus()
      setSystemStatus(status)
    } catch {
      setSystemStatus(null)
    }
  }, [])

  useEffect(() => {
    void refreshSystem()
  }, [refreshSystem])

  if (view === 'landing') {
    return (
      <LandingView
        systemStatus={systemStatus}
        onEnterWorkspace={(section = 'overview') => {
          setActiveSection(section)
          setView('workspace')
        }}
      />
    )
  }

  return (
    <AppShell
      activeSection={activeSection}
      onSelectSection={setActiveSection}
      onOpenLanding={() => setView('landing')}
      workspaceSubject={workspaceSubject}
      onChangeSubject={setWorkspaceSubject}
      systemStatus={systemStatus}
    >
      {activeSection === 'overview' && (
        <OverviewSection
          workspaceSubject={workspaceSubject}
          systemStatus={systemStatus}
          onRefreshSystem={refreshSystem}
          onNavigate={setActiveSection}
        />
      )}
      {activeSection === 'contracts' && <ContractsSection />}
      {activeSection === 'documents' && <DocumentsSection />}
      {activeSection === 'simulations' && <SimulationsSection />}
      {activeSection === 'verification' && <VerificationProofSection />}
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
