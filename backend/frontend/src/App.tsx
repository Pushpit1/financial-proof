import { useCallback, useEffect, useState } from 'react'
import { getAuthToken } from './api/client'
import { platformApi, type SystemStatus } from './api/platform'
import { AppShell, type NavSection } from './components/AppShell'
import { SignInModal } from './components/SignInModal'
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
  const [signInOpen, setSignInOpen] = useState(false)
  const [operatorEmail, setOperatorEmail] = useState(() =>
    getAuthToken() ? 'operator@financialproof.dev' : '',
  )

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

  const operatorLabel = operatorEmail
    ? `OPERATOR: ${operatorEmail.split('@')[0].toUpperCase()}`
    : 'OPERATOR: GUEST'

  return (
    <>
      <SignInModal
        open={signInOpen}
        initialEmail={operatorEmail}
        onClose={() => setSignInOpen(false)}
        onSignedIn={(email) => {
          setOperatorEmail(email)
          setView('workspace')
          void refreshSystem()
        }}
      />

      {view === 'landing' ? (
        <LandingView
          systemStatus={systemStatus}
          operatorLabel={operatorLabel}
          onOpenSignIn={() => setSignInOpen(true)}
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
          onOpenSignIn={() => setSignInOpen(true)}
          operatorLabel={operatorLabel}
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
      )}
    </>
  )
}

export default App
