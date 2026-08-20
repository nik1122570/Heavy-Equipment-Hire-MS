import frappe
from frappe import _
from frappe.utils import add_days, date_diff, get_link_to_form, getdate, today


MACHINE_COMPLIANCE_TYPES = [
	"LATRA License",
	"OSHA Certificate",
	"Usalama Barabarani Sticker",
	"Tools Compliance",
	"Weight Inspection",
]

CRITICAL_MACHINE_COMPLIANCE_TYPES = [
	"LATRA License",
	"OSHA Certificate",
	"Weight Inspection",
]


def get_compliance_status_details(expiry_date):
	if not expiry_date:
		return "Missing", "Missing", None

	expiry = getdate(expiry_date)
	current_date = getdate(today())
	days_remaining = date_diff(expiry, current_date)

	if expiry < current_date:
		return "Expired", "Expired", days_remaining
	if expiry <= getdate(add_days(current_date, 30)):
		day_label = "day" if days_remaining == 1 else "days"
		return "Expiring Soon", f"Expiring Soon - {days_remaining} {day_label} remaining", days_remaining
	return "Active", "Active", days_remaining


def get_latest_machine_compliance(machine, compliance_type):
	if not machine or not compliance_type:
		return None

	records = frappe.get_all(
		"Compliance Certificate",
		filters={
			"equipment_machine": machine,
			"compliance_type": compliance_type,
			"docstatus": ["<", 2],
		},
		fields=["name", "expiry_date", "status", "status_summary", "is_critical"],
		order_by="expiry_date desc, modified desc",
		limit=1,
	)
	return records[0] if records else None


def validate_machine_compliance_for_sales_order(doc):
	machine = doc.get("custom_equipment_machine")
	if not machine:
		return

	expired = []
	expiring_soon = []
	missing = []

	for compliance_type in MACHINE_COMPLIANCE_TYPES:
		certificate = get_latest_machine_compliance(machine, compliance_type)
		if not certificate:
			if compliance_type in CRITICAL_MACHINE_COMPLIANCE_TYPES:
				missing.append(compliance_type)
			continue

		status, summary, _days = get_compliance_status_details(certificate.expiry_date)
		if status != certificate.status:
			frappe.db.set_value(
				"Compliance Certificate",
				certificate.name,
				{"status": status, "status_summary": summary},
				update_modified=False,
			)

		if status == "Expired" and certificate.is_critical:
			expired.append((compliance_type, certificate.name))
		elif status == "Expiring Soon":
			expiring_soon.append((compliance_type, certificate.name, certificate.expiry_date))

	if expired:
		messages = []
		for compliance_type, certificate_name in expired:
			messages.append(
				_("{0}: expired certificate {1}").format(
					compliance_type,
					get_link_to_form("Compliance Certificate", certificate_name),
				)
			)

		frappe.throw(
			_("Cannot submit this Sales Order because {0} has non-compliant critical documents:<br>{1}").format(
				get_link_to_form("Equipment Machine", machine),
				"<br>".join(messages),
			),
			title=_("Machine Compliance Blocked"),
		)

	if missing:
		frappe.msgprint(
			_("{0} has missing critical compliance records:<br>{1}").format(
				get_link_to_form("Equipment Machine", machine),
				"<br>".join(missing),
			),
			title=_("Missing Machine Compliance"),
			indicator="orange",
		)

	if expiring_soon:
		warnings = [
			_("{0}: {1} expires on {2}").format(
				compliance_type,
				get_link_to_form("Compliance Certificate", certificate_name),
				frappe.format(expiry_date, {"fieldtype": "Date"}),
			)
			for compliance_type, certificate_name, expiry_date in expiring_soon
		]
		frappe.msgprint(
			_("Some compliance documents are expiring soon:<br>{0}").format("<br>".join(warnings)),
			title=_("Compliance Expiring Soon"),
			indicator="orange",
		)
