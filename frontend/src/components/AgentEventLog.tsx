import { useState } from 'react'
import { Activity, ChevronDown, ChevronRight, GitBranch, Shield, TestTube2, Users, Rocket, BarChart3, Palette, Brain, Bell, AlertTriangle } from 'lucide-react'
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
  const d = event.data || {}
  const type = event.type

  // GitLab events
  if (type === 'gitlab.code.pushed') {
    const branch = (d.ref || '').replace('refs/heads/', '')
    const count = d.total_commits || d.commits?.length || 0
    const msg = d.commits?.[0]?.message?.split('\n')[0] || ''
    return `${count} commit${count !== 1 ? 's' : ''} pushed to ${branch}${msg ? ` — "${msg}"` : ''}`
  }
  if (type === 'gitlab.pr.opened' || type === 'gitlab.pr.ready_for_review') {
    return `!${d.mr_iid || '?'} "${d.title || 'Untitled'}" (${d.source_branch} → ${d.target_branch})`
  }
  if (type === 'gitlab.pr.approved') {
    return `!${d.mr_iid || '?'} "${d.title || 'Untitled'}" approved`
  }
  if (type === 'gitlab.merge.main') {
    return `!${d.mr_iid || '?'} "${d.title || 'Untitled'}" merged to ${d.ref || 'main'}`
  }
  if (type === 'gitlab.pipeline.started') return `Pipeline #${d.pipeline_id} started on ${d.ref}`
  if (type === 'gitlab.pipeline.completed') return `Pipeline #${d.pipeline_id} succeeded on ${d.ref}`
  if (type === 'gitlab.pipeline.failed') return `Pipeline #${d.pipeline_id} failed on ${d.ref}`

  // Jira events
  if (type === 'jira.ticket.created') return `${d.key} "${d.title}" — ${d.priority || 'No priority'}`
  if (type === 'jira.ticket.updated') return `${d.key} "${d.title}" → ${d.status}`

  // Figma events
  if (type === 'figma.design.changed') return `"${d.file_name || d.file_key}" updated`

  // Agent: Product Intelligence
  if (type === 'agent.product.requirements_analyzed') return `Analyzed ${d.ticket_key || 'ticket'}: ${d.analysis?.summary || d.summary || 'requirements processed'}`
  if (type === 'agent.product.complexity_tagged') return `${d.ticket_key || 'Ticket'} tagged as ${d.complexity || 'unknown'} complexity (${d.effort_points || '?'} pts)`
  if (type === 'agent.product.stories_extracted') return `${d.stories_count || d.stories?.length || 0} stories extracted from ${d.ticket_key || 'ticket'}`

  // Agent: Design Sync
  if (type === 'agent.design.compared') return `Compared design "${d.file_name || ''}" — ${d.match_score ? d.match_score + '% match' : 'analysis complete'}`
  if (type === 'agent.design.impl_notes') return `Generated implementation notes for ${d.ticket_key || 'design changes'}`

  // Agent: Code Orchestration
  if (type === 'agent.code.branch_created') return `Created branch ${d.branch || 'unknown'}`
  if (type === 'agent.code.boilerplate_generated') return `Generated ${d.files?.length || 0} files on ${d.branch || 'branch'}`
  if (type === 'agent.code.pr_template_created') return `Created MR !${d.mr_iid || '?'} for ${d.ticket_key || d.branch || 'feature'}`

  // Agent: Security
  if (type === 'agent.security.scan_complete') {
    const risk = d.overall_risk || 'unknown'
    return `Scan ${d.passed ? 'passed' : 'FAILED'} — ${risk} risk, ${d.vulnerability_count || 0} issues`
  }
  if (type === 'agent.security.vulnerability_found') return `${d.count || 0} vulnerabilities (${d.critical || 0} critical, ${d.high || 0} high) in MR !${d.mr_iid || '?'}`
  if (type === 'agent.security.merge_blocked') return `MR !${d.mr_iid || '?'} blocked: ${d.reason || 'critical vulnerabilities'}`
  if (type === 'agent.security.compliance_report') return `Compliance report generated for MR !${d.mr_iid || '?'}`

  // Agent: Test Intelligence
  if (type === 'agent.test.suggestions_generated') return `${d.unit_tests_count || 0} unit + ${d.integration_tests_count || 0} integration tests suggested for MR !${d.mr_iid || '?'}`
  if (type === 'agent.test.report_created') return `Test report: ${d.total_suggested || 0} tests suggested, ${d.coverage_gaps?.length || 0} coverage gaps`
  if (type === 'agent.test.coverage_report') return `Coverage report for MR !${d.mr_iid || '?'}`

  // Agent: Review Coordination
  if (type === 'agent.review.reviewers_assigned') {
    const count = d.reviewers?.length || d.reviewer_count || 0
    return `${count} reviewer${count !== 1 ? 's' : ''} assigned to MR !${d.mr_iid || '?'} — ${d.complexity || 'unknown'} complexity`
  }
  if (type === 'agent.review.reminder_sent') return `Review reminder sent for MR !${d.mr_iid || '?'}`
  if (type === 'agent.review.sla_breached') return `SLA breached for MR !${d.mr_iid || '?'} — overdue by ${d.hours_overdue || '?'}h`
  if (type === 'agent.review.auto_merged') return `MR !${d.mr_iid || '?'} auto-merged`

  // Agent: Deployment
  if (type === 'agent.deploy.started') return `Deploying ${d.ref || 'main'} — pipeline #${d.pipeline_id || '?'}`
  if (type === 'agent.deploy.complete') return `Deployed successfully — ${d.ref || 'main'}`
  if (type === 'agent.deploy.failed') return `Deploy failed: ${d.reason || 'unknown error'}`
  if (type === 'agent.deploy.rollback') return `Rollback triggered: ${d.reason || 'health check failed'}`
  if (type === 'agent.deploy.release_notes') return `Release notes generated (${d.commit_count || '?'} commits)`

  // Agent: Analytics
  if (type === 'agent.analytics.metrics_collected') return `Metrics collected for project`
  if (type === 'agent.analytics.report_generated') return `${d.report_type || 'Analytics'} report generated`
  if (type === 'agent.analytics.bottleneck_detected') return `Bottleneck: ${d.description || d.bottleneck || 'detected'}`

  // Notifications
  if (type === 'notification.slack') return d.message ? `"${(d.message as string).slice(0, 80)}${(d.message as string).length > 80 ? '...' : ''}"` : 'Slack notification sent'

  // Errors
  if (type === 'agent.error') return `${d.agent || 'Agent'} error: ${d.error || 'unknown'}`

  // Fallback: pick the most interesting field
  if (d.summary) return String(d.summary).slice(0, 100)
  if (d.message) return String(d.message).slice(0, 100)
  if (d.title) return String(d.title).slice(0, 100)
  return 'Event processed'
}

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
          <pre className="text-xs text-gray-600 bg-gray-50 rounded-lg p-3 overflow-x-auto max-h-48">
            {JSON.stringify(event.data, null, 2)}
          </pre>
          {event.correlation_id && (
            <p className="text-[10px] text-gray-400 mt-1">
              Correlation: {event.correlation_id}
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
