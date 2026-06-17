// SecureFlow AI - TypeScript Type Definitions

export interface DashboardStats {
  total_events: number;
  events_today: number;
  total_alerts: number;
  open_alerts: number;
  critical_alerts: number;
  high_alerts: number;
  medium_alerts: number;
  low_alerts: number;
  total_incidents: number;
  open_incidents: number;
  total_tickets: number;
  open_tickets: number;
  resolved_tickets: number;
  risk_score: number;
  risk_level: string;
  agent_actions_today: number;
  false_positive_rate: number;
  events_per_hour: number;
}

export interface Alert {
  id: number;
  event_id?: number;
  alert_type: string;
  severity: string;
  confidence: number;
  title: string;
  description?: string;
  affected_assets?: string[];
  evidence?: Record<string, any>;
  mitre_id?: string;
  mitre_tactic?: string;
  mitre_technique_name?: string;
  source_ip?: string;
  dest_ip?: string;
  status: string;
  priority: string;
  assigned_to?: string;
  investigation_summary?: string;
  remediation_plan?: string;
  created_at?: string;
  updated_at?: string;
  resolved_at?: string;
}

export interface Incident {
  id: number;
  title: string;
  description?: string;
  severity: string;
  status: string;
  priority: string;
  related_alert_ids?: number[];
  investigation_results?: Record<string, any>;
  root_cause?: string;
  attack_path?: string;
  affected_systems?: any[];
  remediation_plan?: any;
  remediation_status: string;
  assigned_to?: string;
  executive_summary?: string;
  technical_summary?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Ticket {
  id: number;
  title: string;
  description?: string;
  category: string;
  priority: string;
  status: string;
  owner?: string;
  requester?: string;
  source: string;
  diagnosis?: string;
  resolution?: string;
  escalation_reason?: string;
  timeline?: any[];
  tags?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface ChatMessage {
  role: string;
  content: string;
  agent?: string;
  timestamp?: string;
}

export interface ChatResponse {
  response: string;
  agent_used: string;
  confidence?: number;
  evidence?: any[];
  actions_taken?: string[];
  session_id: number;
  security_validated: boolean;
  blocked: boolean;
  block_reason?: string;
}

export interface AgentActivity {
  id: number;
  agent_name: string;
  action_type: string;
  input_summary?: string;
  output_summary?: string;
  confidence: number;
  status: string;
  duration_ms?: number;
  created_at?: string;
}

export interface SystemHealth {
  service: string;
  status: string;
  uptime?: string;
  last_check?: string;
}

export interface DemoScenario {
  id: string;
  name: string;
  description: string;
  type: string;
}

export interface ThreatTrend {
  timestamp: string;
  count: number;
  severity: string;
}

export interface AnalysisResult {
  triage: Record<string, any>;
  investigation: Record<string, any>;
  remediation: Record<string, any>;
  report: Record<string, any>;
  incident_id?: number;
  ticket_created?: number;
  confidence: number;
  processing_time_ms: number;
  multi_llm?: boolean;
  agent_providers?: Record<string, { agent: string; llm: string; ai_powered: boolean; duration_ms: number }>;
}

export interface DashboardData {
  stats: DashboardStats;
  threat_trends: ThreatTrend[];
  recent_alerts: Alert[];
  recent_agent_activity: AgentActivity[];
  system_health: SystemHealth[];
  top_attack_types: { type: string; count: number }[];
  severity_distribution: Record<string, number>;
}

export interface Notification {
  id: number;
  title: string;
  message: string;
  severity: string;
  category: string;
  is_read: boolean;
  related_alert_id?: number;
  related_incident_id?: number;
  created_at?: string;
}

export interface IngestionStatus {
  running: boolean;
  log_dir: string;
  interval_seconds: number;
  simulator: {
    lines_written: number;
    attack_events: number;
    running: boolean;
  };
  events_ingested: number;
  alerts_created: number;
  errors: number;
  last_ingestion?: string;
  started_at?: string;
}

export interface HealthCheck {
  status: string;
  service: string;
  version: string;
  components: {
    knowledge_base: {
      status: string;
      documents: number;
    };
    ingestion: {
      status: string;
      events_ingested: number;
    };
    security: {
      prompt_injection: string;
      output_validation: string;
      canary_tokens: string;
      policy_engine: string;
    };
  };
}
