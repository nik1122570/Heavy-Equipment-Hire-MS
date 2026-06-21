from frappe import _


def get_data():
	return {
		"non_standard_fieldnames": {
			"Hire Quotation Simulation": "machine",
			"Quotation": "custom_equipment_machine",
			"Sales Order": "custom_equipment_machine",
			"Insurance Policy": "machine",
			"Equipment Maintenance Job Card": "equipment_machine",
			"Purchase Order": "custom_equipment_machine",
			"Fleet Tracker": "equipment_machine",
		},
		"transactions": [
			{"label": _("Hire"), "items": ["Hire Quotation Simulation", "Quotation", "Sales Order"]},
			{"label": _("Operations"), "items": ["Fleet Tracker"]},
			{"label": _("Maintenance"), "items": ["Equipment Maintenance Job Card", "Purchase Order"]},
			{"label": _("Compliance"), "items": ["Insurance Policy"]},
		],
	}
