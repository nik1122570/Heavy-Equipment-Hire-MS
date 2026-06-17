import frappe

from heavy_equipment_hire.equipment_status import update_all_machine_hire_statuses
from heavy_equipment_hire.heavy_equipment_hire.doctype.equipment_machine.equipment_machine import get_insurance_status_details


def update_insurance_statuses():
	for policy in frappe.get_all(
		"Insurance Policy",
		filters={"docstatus": ["<", 2]},
		fields=["name", "machine", "expiry_date"],
	):
		status, summary = get_insurance_status_details(policy.expiry_date)
		frappe.db.set_value("Insurance Policy", policy.name, "status", status, update_modified=False)
		if policy.machine:
			frappe.db.set_value(
				"Equipment Machine",
				policy.machine,
				{
					"insurance_policy": policy.name,
					"insurance_expiry_date": policy.expiry_date,
					"insurance_status": status,
					"insurance_status_summary": summary,
				},
				update_modified=False,
			)

	for machine in frappe.get_all(
		"Equipment Machine",
		fields=["name", "insurance_expiry_date"],
	):
		status, summary = get_insurance_status_details(machine.insurance_expiry_date)
		frappe.db.set_value(
			"Equipment Machine",
			machine.name,
			{"insurance_status": status, "insurance_status_summary": summary},
			update_modified=False,
		)


def get_insurance_status(expiry_date):
	status, _summary = get_insurance_status_details(expiry_date)
	return "Draft" if status == "Not Set" else status


def update_machine_statuses():
	update_all_machine_hire_statuses()
