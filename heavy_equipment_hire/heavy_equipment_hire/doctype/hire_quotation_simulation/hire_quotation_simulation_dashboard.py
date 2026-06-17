from frappe import _


def get_data(data=None):
	if data is None:
		data = {}

	data["fieldname"] = "custom_hire_quotation_simulation"
	data.setdefault("non_standard_fieldnames", {}).update(
		{
			"Quotation": "custom_hire_quotation_simulation",
			"Sales Order": "custom_hire_quotation_simulation",
			"Purchase Invoice": "custom_hire_quotation_simulation",
			"Sales Invoice": "custom_hire_quotation_simulation",
			"Hire Commercial Adjustment": "hire_quotation_simulation",
		}
	)

	transactions = data.setdefault("transactions", [])
	for transaction in (
		{"label": _("Related"), "items": ["Quotation", "Sales Order"]},
		{"label": _("Adjustments"), "items": ["Hire Commercial Adjustment"]},
		{"label": _("Accounting"), "items": ["Purchase Invoice", "Sales Invoice"]},
	):
		if not any(existing.get("label") == transaction["label"] for existing in transactions):
			transactions.append(transaction)

	return {
		**data,
	}
