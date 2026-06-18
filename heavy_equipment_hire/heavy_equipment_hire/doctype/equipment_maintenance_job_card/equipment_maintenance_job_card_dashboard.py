from frappe import _


def get_data(data=None):
	if data is None:
		data = {}

	data["fieldname"] = "custom_equipment_maintenance_job_card"
	data.setdefault("non_standard_fieldnames", {}).update(
		{
			"Purchase Order": "custom_equipment_maintenance_job_card",
		}
	)
	data.setdefault("internal_links", {}).update(
		{
			"Equipment Machine": "equipment_machine",
		}
	)
	data.setdefault("transactions", []).extend(
		[
			{"label": _("Machine"), "items": ["Equipment Machine"]},
			{"label": _("Procurement"), "items": ["Purchase Order"]},
		]
	)
	return data
