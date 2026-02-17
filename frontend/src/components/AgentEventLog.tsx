import { useState } from 'react'
import { Activity, ChevronDown, ChevronRight, GitBranch, Shield, TestTube2, Users, Rocket, BarChart3, Palette, Brain, Bell, AlertTriangle, FileCode, CheckCircle2, XCircle, AlertOctagon, ArrowRight, Clock, Zap } from 'lucide-react'
import type { AgentEvent } from '../types'

interface AgentEventLogProps {
  events: AgentEvent[]
  loading?: boolean
}

const TYPE_COLORS: Record<string, string> = {
  'jira.': 'bg-blue-100 text-blue-700',
  'gitlab.': 'bg-orange-100 text-orange-700',
  'figma.': 'bg-purple-100 text-purple-700',
  'agent.product.': 'bg-emerald-100 text-emerald-700',
  'agent.design.': 'bg-pink-100 text-pink-700',
  'agent.code.': 'bg-yellow-100 text-yellow-700',
  'agent.security.': 'bg-red-100 text-red-700',
  'agent.test.': 'bg-cyan-100 text-cyan-700',
  'agent.review.': 'bg-indigo-100 text-indigo-700',
  'agent.deploy.': 'bg-teal-100 text-teal-700',
  'agent.analytics.': 'bg-violet-100 text-violet-700',
  'notification.': 'bg-gray-100 text-gray-700',
  'agent.error': 'bg-red-200 text-red-800',
}

function getTypeColor(type: string): string {
  for (const [prefix, color] of Object.entries(TYPE_COLORS)) {
    if (type.startsWith(prefix)) return color
  }
  return 'bg-gray-100 text-gray-600'
}

function getEventIcon(type: string) {
  if (type.startsWith('gitlab.')) return <GitBranch className="w-4 h-4 text-orange-500" />
  if (type.startsWith('agent.security.')) return <Shield className="w-4 h-4 text-red-500" />
  if (type.startsWith('agent.test.')) return <TestTube2 className="w-4 h-4 text-cyan-500" />
  if (type.startsWith('agent.review.')) return <Users className="w-4 h-4 text-indigo-500" />
  if (type.startsWith('agent.deploy.')) return <Rocket className="w-4 h-4 text-teal-500" />
  if (type.startsWith('agent.analytics.')) return <BarChart3 className="w-4 h-4 text-violet-500" />
  if (type.startsWith('agent.design.') || type.startsWith('figma.')) return <Palette className="w-4 h-4 text-pink-500" />
  if (type.startsWith('agent.product.') || type.startsWith('jira.')) return <Brain className="w-4 h-4 text-emerald-500" />
  if (type.startsWith('agent.code.')) return <GitBranch className="w-4 h-4 text-yellow-500" />
  if (type.startsWith('notification.')) return <Bell className="w-4 h-4 text-gray-500" />
  if (type.startsWith('agent.error')) return <AlertTriangle className="w-4 h-4 text-red-600" />
  return <Activity className="w-4 h-4 text-gray-400" />
}

function getEventLabel(type: string): string {
  const labels: Record<string, string> = {
    'gitlab.code.pushed': 'Code Pushed',
    'gitlab.pr.opened': 'MR Opened',
    'gitlab.pr.ready_for_review': 'MR Ready for Review',
    'gitlab.pr.approved': 'MR Approved',
    'gitlab.merge.main': 'Merged to Main',
    'gitlab.issue.assigned': 'Issue Assigned',
    'gitlab.pipeline.started': 'Pipeline Started',
    'gitlab.pipeline.completed': 'Pipeline Completed',
    'gitlab.pipeline.failed': 'Pipeline Failed',
    'jira.ticket.created': 'Jira Ticket Created',
    'jira.ticket.updated': 'Jira Ticket Updated',
    'figma.design.changed': 'Design Updated',
    'agent.product.requirements_analyzed': 'Requirements Analyzed',
    'agent.product.complexity_tagged': 'Complexity Tagged',
    'agent.product.stories_extracted': 'Stories Extracted',
    'agent.design.compared': 'Design Compared',
    'agent.design.impl_notes': 'Implementation Notes',
    'agent.code.branch_created': 'Branch Created',
    'agent.code.boilerplate_generated': 'Boilerplate Generated',
    'agent.code.pr_template_created': 'PR Template Created',
    'agent.security.scan_complete': 'Security Scan Done',
    'agent.security.vulnerability_found': 'Vulnerability Found',
    'agent.security.merge_blocked': 'Merge Blocked',
    'agent.security.compliance_report': 'Compliance Report',
    'agent.test.suggestions_generated': 'Test Suggestions',
    'agent.test.report_created': 'Test Report',
    'agent.test.coverage_report': 'Coverage Report',
    'agent.review.reviewers_assigned': 'Reviewers Assigned',
    'agent.review.reminder_sent': 'Review Reminder',
    'agent.review.sla_breached': 'SLA Breached',
    'agent.review.auto_merged': 'Auto-Merged',
    'agent.deploy.started': 'Deploy Started',
    'agent.deploy.complete': 'Deploy Complete',
    'agent.deploy.failed': 'Deploy Failed',
    'agent.deploy.rollback': 'Rollback Triggered',
    'agent.deploy.release_notes': 'Release Notes',
    'agent.analytics.metrics_collected': 'Metrics Collected',
    'agent.analytics.report_generated': 'Report Generated',
    'agent.analytics.bottleneck_detected': 'Bottleneck Detected',
    'notification.slack': 'Slack Notification',
    'agent.error': 'Agent Error',
  }
  return labels[type] || type.split('.').pop()?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || type
}

function getSourceLabel(source: string): string {
  const labels: Record<string, string> = {
    'gitlab_webhook': 'GitLab',
    'jira_webhook': 'Jira',
    'figma_webhook': 'Figma',
    'manual_trigger': 'Manual',
    'product_intelligence': 'Product Intelligence',
    'design_sync': 'Design Sync',
    'code_orchestration': 'Code Orchestration',
    'security_compliance': 'Security Agent',
    'test_intelligence': 'Test Agent',
    'review_coordination': 'Review Agent',
    'deployment_orchestrator': 'Deploy Agent',
    'analytics_insights': 'Analytics Agent',
    'system': 'System',
  }
  return labels[source] || source.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

function summarizeEvent(event: AgentEvent): string {
  const d: any = event.data || {}
  const type = event.type

  if (type === 'gitlab.code.pushed') {
    const branch = (d.ref || '').replace('refs/heads/', '')
    const count = d.total_commits || d.commits?.length || 0
    const msg = d.commits?.[0]?.message?.split('\n')[0] || ''
    return `${count} commit${count !== 1 ? 's' : ''} pushed to ${branch}${msg ? ` — "${msg}"` : ''}`
  }
  if (type === 'gitlab.pr.opened' || type === 'gitlab.pr.ready_for_review') {
    return `!${d.mr_iid || '?'} "${d.title || 'Untitled'}" (${d.source_branch} → ${d.target_branch})`
  }
  if (type === 'gitlab.pr.approved') return `!${d.mr_iid || '?'} "${d.title || 'Untitled'}" approved`
  if (type === 'gitlab.merge.main') return `!${d.mr_iid || '?'} "${d.title || 'Untitled'}" merged to ${d.ref || 'main'}`
  if (type === 'gitlab.pipeline.started') return `Pipeline #${d.pipeline_id} started on ${d.ref}`
  if (type === 'gitlab.pipeline.completed') return `Pipeline #${d.pipeline_id} succeeded on ${d.ref}`
  if (type === 'gitlab.pipeline.failed') return `Pipeline #${d.pipeline_id} failed on ${d.ref}`
  if (type === 'jira.ticket.created') return `${d.key} "${d.title}" — ${d.priority || 'No priority'}`
  if (type === 'jira.ticket.updated') return `${d.key} "${d.title}" → ${d.status}`
  if (type === 'figma.design.changed') return `"${d.file_name || d.file_key}" updated`
  if (type === 'agent.product.requirements_analyzed') return `Analyzed ${d.ticket_key || 'ticket'}: ${d.analysis?.summary || d.summary || 'requirements processed'}`
  if (type === 'agent.product.complexity_tagged') return `${d.ticket_key || 'Ticket'} tagged as ${d.complexity || 'unknown'} complexity (${d.estimated_effort_hours || d.effort_points || '?'}h)`
  if (type === 'agent.product.stories_extracted') return `${d.stories_count || d.stories?.length || 0} stories extracted from ${d.ticket_key || 'ticket'}`
  if (type === 'agent.design.compared') return `Design "${d.file_key || ''}" — alignment: ${d.alignment || 'analyzed'}`
  if (type === 'agent.design.impl_notes') return `Generated implementation notes for ${d.ticket_key || d.file_key || 'design changes'}`
  if (type === 'agent.code.branch_created') return `Created branch ${d.branch || 'unknown'}`
  if (type === 'agent.code.boilerplate_generated') return `Generated ${d.files?.length || 0} files on ${d.branch || 'branch'}`
  if (type === 'agent.code.pr_template_created') return `Created MR !${d.mr_iid || '?'} for ${d.ticket_key || d.branch || 'feature'}`
  if (type === 'agent.security.scan_complete') return `Scan ${d.passed ? 'passed' : 'FAILED'} — ${d.overall_risk || 'unknown'} risk, ${d.vulnerability_count || 0} issues`
  if (type === 'agent.security.vulnerability_found') return `${d.count || 0} vulnerabilities (${d.critical || 0} critical, ${d.high || 0} high) in MR !${d.mr_iid || '?'}`
  if (type === 'agent.security.merge_blocked') return `MR !${d.mr_iid || '?'} blocked: ${d.reason || 'critical vulnerabilities'}`
  if (type === 'agent.security.compliance_report') return `Compliance report generated for MR !${d.mr_iid || '?'}`
  if (type === 'agent.test.suggestions_generated') return `${d.unit_tests_count || 0} unit + ${d.integration_tests_count || 0} integration tests suggested for MR !${d.mr_iid || '?'}`
  if (type === 'agent.test.report_created') return `Test report: ${d.total_suggested || 0} tests suggested, ${d.coverage_gaps?.length || 0} coverage gaps`
  if (type === 'agent.test.coverage_report') return `Coverage report for MR !${d.mr_iid || '?'}`
  if (type === 'agent.review.reviewers_assigned') {
    const count = d.reviewers?.length || d.reviewer_count || 0
    return `${count} reviewer${count !== 1 ? 's' : ''} assigned to MR !${d.mr_iid || '?'} — ${d.complexity || 'unknown'} complexity`
  }
  if (type === 'agent.review.reminder_sent') return `Review reminder sent for MR !${d.mr_iid || '?'}`
  if (type === 'agent.review.sla_breached') return `SLA breached for MR !${d.mr_iid || '?'} — overdue by ${d.hours_overdue || '?'}h`
  if (type === 'agent.review.auto_merged') return `MR !${d.mr_iid || '?'} auto-merged`
  if (type === 'agent.deploy.started') return `Deploying ${d.ref || 'main'} — pipeline #${d.pipeline_id || '?'}`
  if (type === 'agent.deploy.complete') return `Deployed successfully — ${d.ref || 'main'}`
  if (type === 'agent.deploy.failed') return `Deploy failed: ${d.reason || 'unknown error'}`
  if (type === 'agent.deploy.rollback') return `Rollback triggered: ${d.reason || 'health check failed'}`
  if (type === 'agent.deploy.release_notes') return `Release notes generated (${d.commit_count || d.features?.length || '?'} items)`
  if (type === 'agent.analytics.metrics_collected') return `Metrics collected for project`
  if (type === 'agent.analytics.report_generated') return `Analytics report generated`
  if (type === 'agent.analytics.bottleneck_detected') return `Bottleneck detected in project`
  if (type === 'notification.slack') return d.message ? String(d.message).replace(/\*/g, '').slice(0, 80) + (String(d.message).length > 80 ? '...' : '') : 'Slack notification sent'
  if (type === 'agent.error') return `${d.agent || 'Agent'} error: ${d.error || 'unknown'}`
  if (d.summary) return String(d.summary).slice(0, 100)
  if (d.message) return String(d.message).replace(/\*/g, '').slice(0, 100)
  if (d.title) return String(d.title).slice(0, 100)
  return 'Event processed'
}

// ── Severity/risk badge ─────────────────────────────────────────────────

function SeverityBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    critical: 'bg-red-600 text-white',
    high: 'bg-orange-500 text-white',
    medium: 'bg-yellow-400 text-yellow-900',
    low: 'bg-green-100 text-green-700',
  }
  return (
    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${colors[level] || 'bg-gray-200 text-gray-600'}`}>
      {level.toUpperCase()}
    </span>
  )
}

function DetailRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex gap-2 text-xs">
      <span className="text-gray-400 min-w-[5.5rem] flex-shrink-0">{label}</span>
      <span className="text-gray-700">{children}</span>
    </div>
  )
}

// ── Human-readable event details ────────────────────────────────────────

function EventDetails({ event }: { event: AgentEvent }) {
  const d: any = event.data || {}
  const type = event.type

  // Product Intelligence: Requirements
  if (type === 'agent.product.requirements_analyzed') {
    const analysis = d.analysis || {}
    const stories = analysis.stories || d.stories || []
    return (
      <div className="space-y-2">
        {analysis.summary && <DetailRow label="Summary">{analysis.summary}</DetailRow>}
        <DetailRow label="Complexity">
          <span className={`font-semibold ${analysis.complexity === 'high' ? 'text-red-600' : analysis.complexity === 'medium' ? 'text-yellow-600' : 'text-green-600'}`}>
            {analysis.complexity || 'unknown'}
          </span>
          {analysis.estimated_effort_hours && <span className="text-gray-400 ml-1">({analysis.estimated_effort_hours}h est.)</span>}
        </DetailRow>
        {analysis.tags?.length > 0 && (
          <DetailRow label="Tags">
            <div className="flex flex-wrap gap-1">
              {analysis.tags.map((t: string, i: number) => (
                <span key={i} className="bg-gray-100 text-gray-600 text-[10px] px-1.5 py-0.5 rounded">{t}</span>
              ))}
            </div>
          </DetailRow>
        )}
        {stories.length > 0 && (
          <div className="mt-1.5">
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Stories ({stories.length})</span>
            <div className="mt-1 space-y-1">
              {stories.slice(0, 5).map((s: any, i: number) => (
                <div key={i} className="flex items-start gap-1.5 text-xs">
                  <ArrowRight className="w-3 h-3 text-emerald-400 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">{String(s.title || s.description || 'Story')}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  // Product Intelligence: Complexity
  if (type === 'agent.product.complexity_tagged') {
    return (
      <div className="space-y-1.5">
        <DetailRow label="Ticket">{d.ticket_key}</DetailRow>
        <DetailRow label="Complexity">
          <span className={`font-semibold ${d.complexity === 'high' ? 'text-red-600' : d.complexity === 'medium' ? 'text-yellow-600' : 'text-green-600'}`}>
            {d.complexity}
          </span>
        </DetailRow>
        <DetailRow label="Effort">{d.estimated_effort_hours}h estimated</DetailRow>
        {d.tags?.length > 0 && (
          <DetailRow label="Tags">
            <div className="flex flex-wrap gap-1">
              {d.tags.map((t: string, i: number) => (
                <span key={i} className="bg-gray-100 text-gray-600 text-[10px] px-1.5 py-0.5 rounded">{t}</span>
              ))}
            </div>
          </DetailRow>
        )}
      </div>
    )
  }

  // Product Intelligence: Stories
  if (type === 'agent.product.stories_extracted') {
    const stories = d.stories || []
    return (
      <div className="space-y-1">
        <DetailRow label="Ticket">{d.ticket_key}</DetailRow>
        {stories.slice(0, 6).map((s: any, i: number) => (
          <div key={i} className="flex items-start gap-1.5 text-xs">
            <span className="text-emerald-500 font-mono text-[10px] mt-0.5 flex-shrink-0">{i + 1}.</span>
            <div>
              <span className="font-medium text-gray-800">{String(s.title || '')}</span>
              {s.description && <p className="text-gray-500 mt-0.5">{String(s.description).slice(0, 120)}</p>}
            </div>
          </div>
        ))}
      </div>
    )
  }

  // Design Sync: Compared
  if (type === 'agent.design.compared') {
    const specs = d.component_specs || []
    return (
      <div className="space-y-1.5">
        <DetailRow label="File">{d.file_key}</DetailRow>
        <DetailRow label="Alignment">
          <span className={`font-semibold ${d.alignment === 'matched' ? 'text-green-600' : d.alignment === 'mismatched' ? 'text-red-600' : 'text-yellow-600'}`}>
            {d.alignment}
          </span>
        </DetailRow>
        {specs.length > 0 && (
          <div className="mt-1">
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Components ({specs.length})</span>
            {specs.slice(0, 4).map((s: any, i: number) => (
              <div key={i} className="flex items-center gap-1.5 text-xs mt-0.5">
                <Palette className="w-3 h-3 text-pink-400 flex-shrink-0" />
                <span className="font-medium text-gray-700">{String(s.name || 'Component')}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Design Sync: Impl Notes
  if (type === 'agent.design.impl_notes') {
    const notes = d.notes || {}
    const steps = notes.implementation_steps || d.implementation_steps || []
    const specs = notes.component_specs || []
    return (
      <div className="space-y-1.5">
        <DetailRow label="File">{d.file_key}</DetailRow>
        {d.ticket_key && <DetailRow label="Ticket">{d.ticket_key}</DetailRow>}
        {specs.length > 0 && (
          <div className="mt-1">
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Component Specs</span>
            {specs.slice(0, 4).map((s: any, i: number) => (
              <div key={i} className="text-xs mt-0.5 text-gray-700">
                <span className="font-medium">{String(s.name || '')}</span>
                {s.css_changes && <span className="text-gray-400 ml-1">- CSS changes</span>}
                {s.props && <span className="text-gray-400 ml-1">- Props: {String(s.props).slice(0, 60)}</span>}
              </div>
            ))}
          </div>
        )}
        {steps.length > 0 && (
          <div className="mt-1">
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Steps</span>
            {steps.slice(0, 5).map((s: string, i: number) => (
              <div key={i} className="flex items-start gap-1.5 text-xs mt-0.5">
                <span className="text-pink-400 font-mono text-[10px] mt-0.5">{i + 1}.</span>
                <span className="text-gray-700">{s}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Code Orchestration: Branch
  if (type === 'agent.code.branch_created') {
    return (
      <div className="space-y-1.5">
        <DetailRow label="Branch">
          <span className="font-mono text-yellow-700 bg-yellow-50 px-1.5 py-0.5 rounded text-[11px]">{d.branch}</span>
        </DetailRow>
        {d.ticket_key && <DetailRow label="Ticket">{d.ticket_key}</DetailRow>}
        {d.issue_id && <DetailRow label="Issue">#{d.issue_id}</DetailRow>}
      </div>
    )
  }

  // Code Orchestration: Boilerplate
  if (type === 'agent.code.boilerplate_generated') {
    const files = d.files || []
    return (
      <div className="space-y-1.5">
        <DetailRow label="Branch">
          <span className="font-mono text-yellow-700 bg-yellow-50 px-1.5 py-0.5 rounded text-[11px]">{d.branch}</span>
        </DetailRow>
        {files.length > 0 && (
          <div className="mt-1">
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Files ({files.length})</span>
            {files.slice(0, 8).map((f: string, i: number) => (
              <div key={i} className="flex items-center gap-1.5 text-xs mt-0.5">
                <FileCode className="w-3 h-3 text-gray-400 flex-shrink-0" />
                <span className="font-mono text-gray-600 text-[11px]">{f}</span>
              </div>
            ))}
            {files.length > 8 && <p className="text-[10px] text-gray-400 mt-0.5">+{files.length - 8} more files</p>}
          </div>
        )}
      </div>
    )
  }

  // Code Orchestration: PR Template
  if (type === 'agent.code.pr_template_created') {
    return (
      <div className="space-y-1.5">
        <DetailRow label="MR">!{d.mr_iid}</DetailRow>
        <DetailRow label="Branch">
          <span className="font-mono text-yellow-700 bg-yellow-50 px-1.5 py-0.5 rounded text-[11px]">{d.branch}</span>
        </DetailRow>
        {d.ticket_key && <DetailRow label="Ticket">{d.ticket_key}</DetailRow>}
      </div>
    )
  }

  // Security: Vulnerability Found
  if (type === 'agent.security.vulnerability_found') {
    const vulns = d.vulnerabilities || []
    return (
      <div className="space-y-1.5">
        <DetailRow label="MR">!{d.mr_iid}</DetailRow>
        <div className="flex gap-3 text-xs">
          <span className="text-gray-400 min-w-[5.5rem] flex-shrink-0">Counts</span>
          <div className="flex gap-2">
            {d.critical > 0 && <span className="text-red-600 font-semibold">{d.critical} critical</span>}
            {d.high > 0 && <span className="text-orange-600 font-semibold">{d.high} high</span>}
            <span className="text-gray-500">{d.count} total</span>
          </div>
        </div>
        {vulns.length > 0 && (
          <div className="mt-1 space-y-1.5">
            {vulns.slice(0, 5).map((v: any, i: number) => (
              <div key={i} className="bg-red-50/50 rounded-lg p-2 text-xs space-y-0.5">
                <div className="flex items-center gap-2">
                  <SeverityBadge level={String(v.severity || 'medium')} />
                  <span className="font-semibold text-gray-800">{String(v.type || 'Vulnerability')}</span>
                </div>
                {v.file && (
                  <div className="flex items-center gap-1 text-gray-500">
                    <FileCode className="w-3 h-3" />
                    <span className="font-mono text-[11px]">{String(v.file)}{v.line ? `:${v.line}` : ''}</span>
                  </div>
                )}
                {v.description && <p className="text-gray-600">{String(v.description).slice(0, 150)}</p>}
                {v.recommendation && (
                  <p className="text-emerald-700 flex items-start gap-1">
                    <CheckCircle2 className="w-3 h-3 mt-0.5 flex-shrink-0" />
                    {String(v.recommendation).slice(0, 150)}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Security: Scan Complete
  if (type === 'agent.security.scan_complete') {
    return (
      <div className="space-y-1.5">
        <DetailRow label="MR">!{d.mr_iid}</DetailRow>
        <DetailRow label="Status">
          <span className={`font-semibold flex items-center gap-1 ${d.passed ? 'text-green-600' : 'text-red-600'}`}>
            {d.passed ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
            {d.passed ? 'Passed' : 'Failed'}
          </span>
        </DetailRow>
        <DetailRow label="Risk"><SeverityBadge level={d.overall_risk || 'unknown'} /></DetailRow>
        <DetailRow label="Issues">{d.vulnerability_count || 0} found</DetailRow>
        {d.summary && <DetailRow label="Summary">{String(d.summary).slice(0, 200)}</DetailRow>}
      </div>
    )
  }

  // Security: Compliance Report
  if (type === 'agent.security.compliance_report') {
    const scan = d.scan_result || {}
    const vulns = scan.vulnerabilities || []
    return (
      <div className="space-y-1.5">
        <DetailRow label="MR">!{d.mr_iid}</DetailRow>
        <DetailRow label="Risk"><SeverityBadge level={scan.overall_risk || 'unknown'} /></DetailRow>
        <DetailRow label="Status">{scan.passed ? 'Compliant' : 'Non-compliant'}</DetailRow>
        {vulns.length > 0 && (
          <DetailRow label="Issues">
            {vulns.slice(0, 3).map((v: any, i: number) => (
              <span key={i} className="block">{String(v.type || '')} in {String(v.file || 'unknown')}</span>
            ))}
          </DetailRow>
        )}
      </div>
    )
  }

  // Security: Merge Blocked
  if (type === 'agent.security.merge_blocked') {
    return (
      <div className="space-y-1.5">
        <DetailRow label="MR">!{d.mr_iid}</DetailRow>
        <DetailRow label="Reason">
          <span className="text-red-600 font-medium flex items-center gap-1">
            <AlertOctagon className="w-3.5 h-3.5" />
            {d.reason || 'Critical vulnerabilities'}
          </span>
        </DetailRow>
      </div>
    )
  }

  // Test Intelligence: Suggestions
  if (type === 'agent.test.suggestions_generated') {
    const suggestions = d.suggestions || {}
    const unitTests = suggestions.unit_tests || []
    const integTests = suggestions.integration_tests || []
    const edgeCases = d.edge_cases || suggestions.edge_cases || []
    return (
      <div className="space-y-1.5">
        <DetailRow label="MR">!{d.mr_iid}</DetailRow>
        <div className="flex gap-3 text-xs">
          <span className="text-gray-400 min-w-[5.5rem] flex-shrink-0">Tests</span>
          <div className="flex gap-3">
            <span className="text-cyan-600 font-semibold">{d.unit_tests_count} unit</span>
            <span className="text-blue-600 font-semibold">{d.integration_tests_count} integration</span>
          </div>
        </div>
        {unitTests.length > 0 && (
          <div className="mt-1">
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Unit Tests</span>
            {unitTests.slice(0, 4).map((t: any, i: number) => (
              <div key={i} className="flex items-start gap-1.5 text-xs mt-0.5">
                <TestTube2 className="w-3 h-3 text-cyan-400 mt-0.5 flex-shrink-0" />
                <div>
                  <span className="font-medium text-gray-700">{String(t.name || 'Test')}</span>
                  {t.description && <span className="text-gray-400 ml-1">- {String(t.description).slice(0, 80)}</span>}
                </div>
              </div>
            ))}
          </div>
        )}
        {integTests.length > 0 && (
          <div className="mt-1">
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Integration Tests</span>
            {integTests.slice(0, 3).map((t: any, i: number) => (
              <div key={i} className="flex items-start gap-1.5 text-xs mt-0.5">
                <Zap className="w-3 h-3 text-blue-400 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700">{String(t.name || t.description || 'Test')}</span>
              </div>
            ))}
          </div>
        )}
        {edgeCases.length > 0 && (
          <div className="mt-1">
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Edge Cases</span>
            {edgeCases.slice(0, 4).map((ec: string, i: number) => (
              <div key={i} className="flex items-start gap-1.5 text-xs mt-0.5">
                <AlertTriangle className="w-3 h-3 text-yellow-400 mt-0.5 flex-shrink-0" />
                <span className="text-gray-600">{ec}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Test Intelligence: Report
  if (type === 'agent.test.report_created') {
    const gaps = d.coverage_gaps || []
    return (
      <div className="space-y-1.5">
        <DetailRow label="MR">!{d.mr_iid}</DetailRow>
        <DetailRow label="Tests Suggested">{d.total_suggested}</DetailRow>
        {gaps.length > 0 && (
          <div className="mt-1">
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Coverage Gaps ({gaps.length})</span>
            {gaps.slice(0, 4).map((g: string, i: number) => (
              <div key={i} className="flex items-start gap-1.5 text-xs mt-0.5">
                <XCircle className="w-3 h-3 text-orange-400 mt-0.5 flex-shrink-0" />
                <span className="text-gray-600">{g}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Review: Reviewers Assigned
  if (type === 'agent.review.reviewers_assigned') {
    const riskAreas = d.risk_areas || []
    return (
      <div className="space-y-1.5">
        <DetailRow label="MR">!{d.mr_iid}</DetailRow>
        <DetailRow label="Complexity">
          <span className={`font-semibold ${d.complexity === 'high' ? 'text-red-600' : d.complexity === 'medium' ? 'text-yellow-600' : 'text-green-600'}`}>
            {d.complexity}
          </span>
        </DetailRow>
        <DetailRow label="Review Time">
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3 text-gray-400" />
            ~{d.estimated_review_minutes}min
          </span>
        </DetailRow>
        <DetailRow label="Auto-merge">
          {d.auto_merge_eligible ? (
            <span className="text-green-600 flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Eligible</span>
          ) : (
            <span className="text-gray-400">Not eligible</span>
          )}
        </DetailRow>
        {riskAreas.length > 0 && (
          <DetailRow label="Risk Areas">
            <div className="flex flex-wrap gap-1">
              {riskAreas.map((r: string, i: number) => (
                <span key={i} className="bg-red-50 text-red-600 text-[10px] px-1.5 py-0.5 rounded font-medium">{r}</span>
              ))}
            </div>
          </DetailRow>
        )}
        {d.summary && <DetailRow label="Summary">{String(d.summary).slice(0, 200)}</DetailRow>}
      </div>
    )
  }

  // Deploy: Started
  if (type === 'agent.deploy.started') {
    return (
      <div className="space-y-1.5">
        <DetailRow label="Ref">
          <span className="font-mono text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded text-[11px]">{d.ref || 'main'}</span>
        </DetailRow>
        <DetailRow label="Trigger">{d.trigger_event?.replace(/\./g, ' ') || 'manual'}</DetailRow>
      </div>
    )
  }

  // Deploy: Complete
  if (type === 'agent.deploy.complete') {
    const health = d.health_check || {}
    const releaseNotes = d.release_notes || {}
    return (
      <div className="space-y-1.5">
        <DetailRow label="Status">
          <span className="text-green-600 font-semibold flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> Deployed
          </span>
        </DetailRow>
        {health.checks_run !== undefined && <DetailRow label="Health Checks">{health.checks_run} passed</DetailRow>}
        {releaseNotes.version_summary && <DetailRow label="Release">{releaseNotes.version_summary}</DetailRow>}
        {releaseNotes.features?.length > 0 && (
          <div className="mt-1">
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Features</span>
            {releaseNotes.features.slice(0, 4).map((f: string, i: number) => (
              <div key={i} className="flex items-start gap-1.5 text-xs mt-0.5">
                <Zap className="w-3 h-3 text-teal-400 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700">{f}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Deploy: Failed
  if (type === 'agent.deploy.failed') {
    const issues = d.issues || []
    return (
      <div className="space-y-1.5">
        <DetailRow label="Reason">
          <span className="text-red-600 font-medium">{d.reason || 'Unknown'}</span>
        </DetailRow>
        {issues.length > 0 && (
          <div className="mt-1">
            {issues.map((issue: string, i: number) => (
              <div key={i} className="flex items-start gap-1.5 text-xs mt-0.5">
                <XCircle className="w-3 h-3 text-red-400 mt-0.5 flex-shrink-0" />
                <span className="text-gray-600">{issue}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Deploy: Release Notes
  if (type === 'agent.deploy.release_notes') {
    const features = d.features || []
    const bugfixes = d.bugfixes || []
    return (
      <div className="space-y-1.5">
        {d.version_summary && <DetailRow label="Summary">{d.version_summary}</DetailRow>}
        {features.length > 0 && (
          <div className="mt-1">
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Features ({features.length})</span>
            {features.slice(0, 5).map((f: string, i: number) => (
              <div key={i} className="flex items-start gap-1.5 text-xs mt-0.5">
                <Zap className="w-3 h-3 text-teal-400 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700">{f}</span>
              </div>
            ))}
          </div>
        )}
        {bugfixes.length > 0 && (
          <div className="mt-1">
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Bug Fixes ({bugfixes.length})</span>
            {bugfixes.slice(0, 3).map((b: string, i: number) => (
              <div key={i} className="flex items-start gap-1.5 text-xs mt-0.5">
                <CheckCircle2 className="w-3 h-3 text-green-400 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700">{b}</span>
              </div>
            ))}
          </div>
        )}
        {d.breaking_changes?.length > 0 && (
          <div className="mt-1">
            <span className="text-[10px] font-semibold text-red-500 uppercase tracking-wide">Breaking Changes</span>
            {d.breaking_changes.map((b: string, i: number) => (
              <div key={i} className="flex items-start gap-1.5 text-xs mt-0.5">
                <AlertOctagon className="w-3 h-3 text-red-400 mt-0.5 flex-shrink-0" />
                <span className="text-red-700">{b}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Analytics: Bottleneck
  if (type === 'agent.analytics.bottleneck_detected') {
    const bottlenecks = d.bottlenecks || []
    const recommendations = d.recommendations || []
    return (
      <div className="space-y-1.5">
        {bottlenecks.length > 0 && (
          <div className="space-y-1.5">
            {bottlenecks.map((b: any, i: number) => (
              <div key={i} className="bg-violet-50/50 rounded-lg p-2 text-xs space-y-0.5">
                <div className="flex items-center gap-2">
                  <SeverityBadge level={String(b.severity || 'medium')} />
                  <span className="font-semibold text-gray-800">{String(b.area || 'Bottleneck')}</span>
                </div>
                {b.description && <p className="text-gray-600">{String(b.description)}</p>}
              </div>
            ))}
          </div>
        )}
        {recommendations.length > 0 && (
          <div className="mt-1">
            <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Recommendations</span>
            {recommendations.slice(0, 4).map((r: string, i: number) => (
              <div key={i} className="flex items-start gap-1.5 text-xs mt-0.5">
                <CheckCircle2 className="w-3 h-3 text-violet-400 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700">{String(r)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Analytics: Report Generated
  if (type === 'agent.analytics.report_generated') {
    const analysis = d.analysis || {}
    const metrics = d.metrics || {}
    const taskDist = metrics.task_distribution || {}
    const predictions = analysis.predictions || {}
    return (
      <div className="space-y-1.5">
        {Object.keys(taskDist).length > 0 && (
          <DetailRow label="Tasks">
            <div className="flex gap-2 flex-wrap">
              {Object.entries(taskDist).map(([status, count]) => (
                <span key={status} className="text-gray-600">
                  <span className="font-medium">{String(count)}</span> {status}
                </span>
              ))}
            </div>
          </DetailRow>
        )}
        {metrics.completed_this_week !== undefined && (
          <DetailRow label="Completed">
            <span className="font-semibold text-green-600">{metrics.completed_this_week}</span> this week
          </DetailRow>
        )}
        {predictions.velocity_trend && (
          <DetailRow label="Velocity">
            <span className={`font-semibold ${predictions.velocity_trend === 'increasing' ? 'text-green-600' : predictions.velocity_trend === 'decreasing' ? 'text-red-600' : 'text-gray-600'}`}>
              {predictions.velocity_trend}
            </span>
          </DetailRow>
        )}
        {predictions.sprint_completion_pct !== undefined && (
          <DetailRow label="Sprint">~{predictions.sprint_completion_pct}% completion</DetailRow>
        )}
        {analysis.executive_summary && (
          <DetailRow label="Summary">{String(analysis.executive_summary).slice(0, 200)}</DetailRow>
        )}
      </div>
    )
  }

  // Slack Notification
  if (type === 'notification.slack') {
    const msg = String(d.message || '')
    // Remove Slack markdown formatting
    const clean = msg.replace(/\*/g, '').replace(/:[\w_]+:/g, '')
    return (
      <div className="text-xs text-gray-700 whitespace-pre-line leading-relaxed">{clean}</div>
    )
  }

  // Agent Error
  if (type === 'agent.error') {
    return (
      <div className="space-y-1.5">
        <DetailRow label="Agent">{d.agent}</DetailRow>
        <DetailRow label="Event">{d.event_type}</DetailRow>
        <DetailRow label="Error">
          <span className="text-red-600">{String(d.error || 'Unknown').slice(0, 200)}</span>
        </DetailRow>
        {d.processing_ms && <DetailRow label="Duration">{Math.round(d.processing_ms)}ms</DetailRow>}
      </div>
    )
  }

  // Fallback: render key-value pairs cleanly
  const entries = Object.entries(d).filter(([k]: [string, any]) => !['diff', 'scan_result', 'suggestions', 'analysis', 'notes', 'metrics'].includes(k))
  if (entries.length === 0) return <p className="text-xs text-gray-400">No additional details</p>
  return (
    <div className="space-y-1">
      {entries.slice(0, 8).map(([key, value]: [string, any]) => {
        const display = typeof value === 'object'
          ? Array.isArray(value) ? `${value.length} items` : 'object'
          : String(value).slice(0, 150)
        return (
          <DetailRow key={key} label={key.replace(/_/g, ' ')}>{display}</DetailRow>
        )
      })}
    </div>
  )
}

// ── Event Row ───────────────────────────────────────────────────────────

function EventRow({ event }: { event: AgentEvent }) {
  const [expanded, setExpanded] = useState(false)
  const color = getTypeColor(event.type)
  const time = new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  const icon = getEventIcon(event.type)
  const label = getEventLabel(event.type)
  const source = getSourceLabel(event.source_agent)
  const summary = summarizeEvent(event)

  return (
    <div className="border-b border-gray-100 last:border-0">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-start gap-3 px-4 py-3 hover:bg-gray-50 text-left transition-colors"
      >
        <div className="mt-0.5 flex-shrink-0">{icon}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${color} flex-shrink-0`}>
              {label}
            </span>
            <span className="text-[11px] text-gray-400">{source}</span>
            <span className="text-[11px] text-gray-300 ml-auto flex-shrink-0">{time}</span>
          </div>
          <p className="text-sm text-gray-700 mt-1 leading-snug">{summary}</p>
        </div>
        <div className="mt-1 flex-shrink-0">
          {expanded ? (
            <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
          )}
        </div>
      </button>
      {expanded && (
        <div className="px-4 pb-3 pl-11">
          <div className="bg-gray-50 rounded-lg p-3">
            <EventDetails event={event} />
          </div>
          {event.correlation_id && (
            <p className="text-[10px] text-gray-400 mt-1.5 flex items-center gap-1">
              <span className="text-gray-300">ID:</span> {event.correlation_id}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default function AgentEventLog({ events, loading }: AgentEventLogProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-200 bg-gray-50">
        <Activity className="w-4 h-4 text-indigo-500" />
        <h3 className="text-sm font-semibold text-gray-900">Event Log</h3>
        <span className="text-xs text-gray-400 ml-auto">{events.length} events</span>
      </div>
      <div className="max-h-[500px] overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-500" />
          </div>
        ) : events.length === 0 ? (
          <p className="text-center text-sm text-gray-400 py-8">No events yet</p>
        ) : (
          [...events].reverse().map((event) => <EventRow key={event.event_id} event={event} />)
        )}
      </div>
    </div>
  )
}
