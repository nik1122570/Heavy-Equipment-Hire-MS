import frappe
from frappe import _

from heavy_equipment_hire.compliance import get_compliance_status_details


def execute(filters=None):
	filters = frappe._dict(filters or {})
	rows = get_rows(filters)
	return get_columns(), rows, None, get_chart(rows), get_summary(rows)


def get_columns():
	return [
		{"label": _("Driver Name"), "fieldname": "driver_name", "fieldtype": "Data", "width": 220},
		{"label": _("Registration ID"), "fieldname": "registration_id", "fieldtype": "Data", "width": 150},
		{"label": _("License No"), "fieldname": "license_no", "fieldtype": "Data", "width": 160},
		{"label": _("Authorised Classes"), "fieldname": "license_classes", "fieldtype": "Data", "width": 200},
		{"label": _("Expiry Date"), "fieldname": "expiry_date", "fieldtype": "Date", "width": 120},
		{"label": _("Days Remaining"), "fieldname": "days_remaining", "fieldtype": "Int", "width": 130},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 130},
		{"label": _("Reference"), "fieldname": "driver_compliance", "fieldtype": "Link", "options": "Driver Compliance", "width": 170},
	]


def get_rows(filters):
	conditions = {"docstatus": ["<", 2]}

	rows = frappe.get_all(
		"Driver Compliance",
		filters=conditions,
		fields=[
			"name as driver_compliance",
			"driver_name",
			"registration_id",
			"license_no",
			"license_classes",
			"expiry_date",
			"status",
			"days_remaining",
		],
		order_by="expiry_date asc, driver_name asc",
	)

	filtered = []
	for row in rows:
		if filters.get("driver_name") and filters.driver_name.lower() not in (row.driver_name or "").lower():
			continue
		status, _summary, days_remaining = get_compliance_status_details(row.expiry_date)
		row.status = status
		row.days_remaining = days_remaining
		if filters.get("status") and row.status != filters.status:
			continue
		filtered.append(row)
	return filtered


def get_summary(rows):
	return [
		{"value": len(rows), "label": _("Drivers"), "datatype": "Int", "indicator": "Blue"},
		{"value": len([row for row in rows if row.status == "Active"]), "label": _("Active"), "datatype": "Int", "indicator": "Green"},
		{"value": len([row for row in rows if row.status == "Expiring Soon"]), "label": _("Expiring Soon"), "datatype": "Int", "indicator": "Orange"},
		{"value": len([row for row in rows if row.status == "Expired"]), "label": _("Expired"), "datatype": "Int", "indicator": "Red"},
	]


def get_chart(rows):
	counts = {
		"Active": len([row for row in rows if row.status == "Active"]),
		"Expiring Soon": len([row for row in rows if row.status == "Expiring Soon"]),
		"Expired": len([row for row in rows if row.status == "Expired"]),
	}
	return {
		"data": {
			"labels": list(counts),
			"datasets": [{"name": _("Drivers"), "values": list(counts.values())}],
		},
		"type": "donut",
		"colors": ["#10b981", "#f59e0b", "#ef4444"],
	}
