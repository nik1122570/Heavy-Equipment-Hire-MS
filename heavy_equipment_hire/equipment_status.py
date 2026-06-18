import frappe
from frappe.utils import getdate, today


MANUAL_STATUSES = {"Under Maintenance", "Maintenance Required", "Out of Service"}


def update_machine_hire_status(machine, force=False):
	if not machine:
		return

	if has_open_maintenance(machine):
		frappe.db.set_value("Equipment Machine", machine, "status", "Under Maintenance", update_modified=False)
		return

	current_status = frappe.db.get_value("Equipment Machine", machine, "status")
	if current_status in MANUAL_STATUSES and not force:
		return

	status = get_machine_hire_status(machine)
	frappe.db.set_value("Equipment Machine", machine, "status", status, update_modified=False)


def update_all_machine_hire_statuses():
	for machine in frappe.get_all("Equipment Machine", pluck="name"):
		update_machine_hire_status(machine)


def get_machine_hire_status(machine):
	current_date = getdate(today())

	active = frappe.db.exists(
		"Sales Order",
		{
			"docstatus": 1,
			"custom_equipment_machine": machine,
			"custom_hire_from_date": ["<=", current_date],
			"custom_hire_to_date": [">=", current_date],
		},
	)
	if active:
		return "On Hire"

	future = frappe.db.exists(
		"Sales Order",
		{
			"docstatus": 1,
			"custom_equipment_machine": machine,
			"custom_hire_from_date": [">", current_date],
		},
	)
	if future:
		return "Booked"

	return "Available"


def has_open_maintenance(machine):
	if not machine:
		return False

	return bool(
		frappe.db.exists(
			"Equipment Maintenance Job Card",
			{
				"docstatus": 1,
				"equipment_machine": machine,
				"status": "Open",
			},
		)
	)
