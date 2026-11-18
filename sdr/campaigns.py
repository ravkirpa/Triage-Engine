"""Bottleneck -> campaign copy. Technology only (TankhaPay Global HRMS + payroll); claims come from the TankhaPay deck."""
import re

CAMPAIGNS = [
 ("multi_entity", r"multi.?entit|multiple (entit|compan|subsidiar|branch)|subsidiar|group compan|separate (tool|system)|branch|stores",
  dict(pain="payroll and HR management across multiple entities",
       impact="delays, inconsistent policies and duplicated effort across entities",
       solution="run every entity on one platform, with group-level policies and entity-level customisation",
       value="one consolidated view of the whole workforce and consistent compliance",
       roi="duplicate data entry and tool sprawl")),
 ("integration", r"integrat|erp|\bsap\b|oracle|disconnect|silo|\bapi\b|spreadsheet|excel|manual data|re.?entry|legacy",
  dict(pain="disconnected HR, payroll and finance systems",
       impact="re-keying, reconciliation gaps and slow month-end closes",
       solution="connect payroll and HRIS to SAP, Oracle and 50+ systems through a secure, documented API",
       value="clean data flowing between HR and finance",
       roi="manual re-entry and reconciliation time")),
 ("payroll_compliance", r"payroll|salary|statutory|complian|filing|tax|social security|withholding|vat|penalt|error",
  dict(pain="global payroll accuracy and statutory compliance",
       impact="salary delays, calculation errors and filing penalties across countries",
       solution="automate multi-country payroll with local statutory and tax rules for every jurisdiction you operate in",
       value="accurate payroll every cycle and on-time filings",
       roi="rework, manual corrections and penalty costs")),
 ("attendance", r"attendance|proxy|punch|shift|roster|time.?track|leave|geofenc",
  dict(pain="attendance tracking and proxy punching",
       impact="an inflated wage bill and hours of manual reconciliation",
       solution="verify attendance with geofencing and face check, feeding straight into payroll",
       value="a wage bill that reflects hours actually worked",
       roi="manual reconciliation and payroll disputes")),
 ("workforce_mix", r"contract|off.?roll|on.?roll|apprentic|gig|temp|diverse|worker type|blue.?collar|frontline",
  dict(pain="managing a mix of on-roll, off-roll and contract workers",
       impact="fragmented records and inconsistent pay and compliance handling",
       solution="manage every worker type on one platform with a single employee record",
       value="one process and one source of truth for the whole workforce",
       roi="spreadsheet handling and admin effort")),
 ("performance_ld", r"performance|appraisal|review|okr|kra|feedback|training|learning|l&d|development",
  dict(pain="performance reviews and learning impact",
       impact="untracked goals, inconsistent ratings and training nobody can measure",
       solution="run OKRs, 360 feedback, calibrated ratings and learning tracking inside the same HRMS",
       value="consistent ratings and visible training impact",
       roi="admin time spent chasing reviews and reports")),
 ("onboarding_admin", r"onboard|document|helpdesk|admin|paperwork|self.?service|approval|workflow|headcount|hr tasks|efficien",
  dict(pain="manual HR administration",
       impact="slow onboarding, approval bottlenecks and a stretched HR team",
       solution="automate 100+ HR tasks, from onboarding and approvals to self-service, on one platform",
       value="faster HR operations and a better employee experience",
       roi="admin time, rework and errors")),
]

HYPOTHESES = [  # exact phrases from the account-intelligence Bottleneck Bank
 ("Roster changes, qualifications and leave approvals", "bank_rosters", dict(
   pain="roster, qualification and leave-approval management", impact="manual reconciliation and delayed or inconsistent payroll inputs",
   solution="bring rosters, leave and approvals together with attendance feeding payroll directly",
   value="payroll inputs you can trust without chasing managers", roi="reconciliation time and pay corrections")),
 ("timesheets and employee-versus-subcontractor", "bank_timesheets", dict(
   pain="project and site timesheet management across employees and contractors", impact="rework on hours, job allocation and onboarding documentation",
   solution="manage every worker type, on-roll, off-roll and contract, with attendance and timesheets feeding payroll on one platform",
   value="clean hours and one source of truth for the whole workforce", roi="rework on hours and onboarding paperwork")),
 ("joiner/leaver approvals may be spread across managers", "bank_approvals", dict(
   pain="joiner, leaver and leave approval management spread across managers and finance", impact="approval delays and duplicated employee administration",
   solution="run approval workflows and employee records from one HRMS that feeds payroll",
   value="faster approvals and a single employee record", roi="duplicate admin and approval chasing")),
 ("Location-level shifts, joiners and casual-worker changes", "bank_locations", dict(
   pain="shift and casual-worker management across locations", impact="reconciliation across managers before every pay run",
   solution="manage shifts, geofenced attendance and multi-location payroll centrally, with entity-level rules where needed",
   value="consistent pay and compliance across every location", roi="manual reconciliation and payroll errors")),
 ("different time and employee-data processes", "bank_mixed_teams", dict(
   pain="time and employee-data management across office, warehouse and production teams", impact="inconsistent records and manual consolidation",
   solution="unify employee data, attendance and payroll for every team on one platform",
   value="one consistent process and reliable workforce data", roi="manual consolidation and data re-entry")),
 ("separation from volunteers", "bank_volunteers", dict(
   pain="paid-employee record management alongside volunteers and grant-funded programmes", impact="messy payroll data and extra reporting effort",
   solution="manage different worker types and programme-level reporting from a single employee record feeding payroll",
   value="clean paid-employee data and easier funder reporting", roi="spreadsheet handling and reporting effort")),
 ("Split shifts, casual educator changes", "bank_split_shifts", dict(
   pain="split-shift and casual staff management across centres", impact="inconsistent payroll inputs and approval delays",
   solution="automate shifts, leave and centre-level approvals so they feed payroll accurately",
   value="accurate pay for casual and split-shift staff", roi="manual rework and approval delays")),
 ("split across specialist applications", "bank_fragmented_apps", dict(
   pain="fragmented employee data and onboarding across specialist applications", impact="duplicate admin and gaps between systems",
   solution="put onboarding, employee records, approvals and payroll on one platform, with API links to 50+ HR and finance systems",
   value="one connected view of the workforce", roi="duplicate entry and system hopping")),
]
GENERIC_MARK = "require qualification before a specific HRMS bottleneck"

def build(bottleneck):
    b0 = (bottleneck or "")
    for phrase, key, c in HYPOTHESES:
        if phrase.lower() in b0.lower(): return key, dict(c)
    return _build_regex(bottleneck)

def _build_regex(bottleneck):
    """Pick the campaign that matches the databank's bottleneck text; fall back to using their words."""
    b = (bottleneck or "").strip()
    for key, rx, c in CAMPAIGNS:
        if re.search(rx, b, re.I):
            return key, dict(c)
    return "general", dict(
        pain=b.rstrip(".") or "running payroll and HR across the business",
        impact="delays, errors and extra manual effort for your HR and finance teams",
        solution="bring global payroll, compliance and HR workflows onto one unified platform",
        value="accurate, on-time payroll and a single view of your workforce",
        roi="admin time, rework and costs")
