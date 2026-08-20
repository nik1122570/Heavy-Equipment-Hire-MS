import frappe
from frappe import _

from heavy_equipment_hire.compliance import MACHINE_COMPLIANCE_TYPES, get_compliance_status_details


FIELD_BY_TYPE = {
	"LATRA License": "latra_license",
	"OSHA Certificate": "osha_certificate",
	"Usalama Barabarani Sticker": "usalama_barabarani_sticker",
	"Tools Compliance": "tools_compliance",
	"Weight Inspection": "weight_inspection",
}


def execute(filters=None):
	filters = frappe._dict(filters or {})
	rows = get_rows(filters)
	return get_columns(), rows, None, get_chart(rows), get_summary(rows)


def get_columns():
	return [
		{"label": _("Machine"), "fieldname": "equipment_machine", "fieldtype": "Link", "options": "Equipment Machine", "width": 170},
		{"label": _("Registration No"), "fieldname": "registration_no", "fieldtype": "Data", "width": 130},
		{"label": _("Cost Center"), "fieldname": "cost_center", "fieldtype": "Link", "options": "Cost Center", "width": 220},
		{"label": _("LATRA"), "fieldname": "latra_license", "fieldtype": "Data", "width": 160},
		{"label": _("OSHA"), "fieldname": "osha_certificate", "fieldtype": "Data", "width": 160},
		{"label": _("Usalama Sticker"), "fieldname": "usalama_barabarani_sticker", "fieldtype": "Data", "width": 170},
		{"label": _("Tools"), "fieldname": "tools_compliance", "fieldtype": "Data", "width": 160},
		{"label": _("Weight Inspection"), "fieldname": "weight_inspection", "fieldtype": "Data", "width": 170},
		{"label": _("Overall Status"), "fieldname": "overall_status", "fieldtype": "Data", "width": 160},
	]


def get_rows(filters):
	machine_filters = {}
	if filters.get("company"):
		machine_filters["company"] = filters.company
	if filters.get("equipment_machine"):
		machine_filters["name"] = filters.equipment_machine

	machines = frappe.get_all(
		"Equipment Machine",
		filters=machine_filters,
		fields=["name", "registration_no", "cost_center"],
		order_by="registration_no asc",
	)
	certificates = get_certificates([machine.name for machine in machines])

	rows = []
	for machine in machines:
		row = frappe._dict(
			{
				"equipment_machine": machine.name,
				"registration_no": machine.registration_no,
				"cost_center": machine.cost_center,
			}
		)
		statuses = []
		for compliance_type in MACHINE_COMPLIANCE_TYPES:
			fieldname = FIELD_BY_TYPE[compliance_type]
			certificate = certificates.get((machine.name, compliance_type))
			row[fieldname] = get_status_label(certificate)
			statuses.append(row[fieldname])

		row.overall_status = get_overall_status(statuses)
		if filters.get("status") and row.overall_status != filters.status:
			continue
		rows.append(row)

	return rows


def get_certificates(machine_names):
	if not machine_names:
		return {}

	result = {}
	records = frappe.get_all(
		"Compliance Certificate",
		filters={
			"equipment_machine": ["in", machine_names],
			"compliance_type": ["in", MACHINE_COMPLIANCE_TYPES],
			"docstatus": ["<", 2],
		},
		fields=["name", "equipment_machine", "compliance_type", "expiry_date", "status", "status_summary"],
		order_by="expiry_date desc, modified desc",
	)
	for record in records:
		key = (record.equipment_machine, record.compliance_type)
		if key not in result:
			result[key] = record
	return result


def get_status_label(certificate):
	if not certificate:
		return _("Missing")

	status, summary, days_remaining = get_compliance_status_details(certificate.expiry_date)
	if status == "Expiring Soon" and days_remaining is not None:
		return _("Expiring Soon ({0} days)").format(days_remaining)
	return status or summary or _("Missing")


def get_overall_status(statuses):
	if any(status.startswith("Expired") or status.startswith("Missing") for status in statuses):
		return "Non-Compliant"
	if any(status.startswith("Expiring Soon") for status in statuses):
		return "Attention Required"
	return "Compliant"


def get_summary(rows):
	return [
		{"value": len(rows), "label": _("Machines"), "datatype": "Int", "indicator": "Blue"},
		{"value": len([row for row in rows if row.overall_status == "Compliant"]), "label": _("Compliant"), "datatype": "Int", "indicator": "Green"},
		{"value": len([row for row in rows if row.overall_status == "Attention Required"]), "label": _("Attention Required"), "datatype": "Int", "indicator": "Orange"},
		{"value": len([row for row in rows if row.overall_status == "Non-Compliant"]), "label": _("Non-Compliant"), "datatype": "Int", "indicator": "Red"},
	]


def get_chart(rows):
	counts = {
		"Compliant": len([row for row in rows if row.overall_status == "Compliant"]),
		"Attention Required": len([row for row in rows if row.overall_status == "Attention Required"]),
		"Non-Compliant": len([row for row in rows if row.overall_status == "Non-Compliant"]),
	}
	return {
		"data": {
			"labels": list(counts),
			"datasets": [{"name": _("Machines"), "values": list(counts.values())}],
		},
		"type": "donut",
		"colors": ["#10b981", "#f59e0b", "#ef4444"],
	}
