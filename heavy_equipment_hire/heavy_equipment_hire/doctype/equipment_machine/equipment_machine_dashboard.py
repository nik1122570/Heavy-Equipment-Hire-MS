from frappe import _


def get_data():
	return {
		"non_standard_fieldnames": {
			"Hire Quotation Simulation": "machine",
			"Quotation": "custom_equipment_machine",
			"Sales Order": "custom_equipment_machine",
			"Insurance Policy": "machine",
		},
		"transactions": [
			{"label": _("Hire"), "items": ["Hire Quotation Simulation", "Quotation", "Sales Order"]},
			{"label": _("Compliance"), "items": ["Insurance Policy"]},
		],
	}
