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

def build(bottleneck):
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
