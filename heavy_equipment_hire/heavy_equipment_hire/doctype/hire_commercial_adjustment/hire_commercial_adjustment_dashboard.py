from frappe import _


def get_data(data=None):
	if data is None:
		data = {}

	data["fieldname"] = "custom_hire_commercial_adjustment"
	data.setdefault("non_standard_fieldnames", {}).update(
		{
			"Purchase Invoice": "custom_hire_commercial_adjustment",
			"Sales Invoice": "custom_hire_commercial_adjustment",
		}
	)
	data.setdefault("internal_links", {}).update(
		{
			"Hire Quotation Simulation": "hire_quotation_simulation",
			"Sales Order": "sales_order",
		}
	)

	transactions = data.setdefault("transactions", [])
	for transaction in (
		{"label": _("Source"), "items": ["Hire Quotation Simulation", "Sales Order"]},
		{"label": _("Accounting"), "items": ["Purchase Invoice", "Sales Invoice"]},
	):
		if not any(existing.get("label") == transaction["label"] for existing in transactions):
			transactions.append(transaction)

	return data
