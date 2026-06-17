from frappe import _
from erpnext.selling.doctype.quotation.quotation_dashboard import get_data as get_erpnext_quotation_dashboard


def get_data(data=None):
	if data is None:
		data = get_erpnext_quotation_dashboard()

	data.setdefault("non_standard_fieldnames", {}).update(
		{
			"Hire Quotation Simulation": "quotation",
		}
	)
	data.setdefault("internal_links", {}).update(
		{
			"Hire Quotation Simulation": "custom_hire_quotation_simulation",
			"Equipment Machine": "custom_equipment_machine",
		}
	)

	hire_transaction = {"label": _("Hire"), "items": ["Hire Quotation Simulation", "Equipment Machine"]}
	transactions = data.setdefault("transactions", [])
	if not any(transaction.get("label") == hire_transaction["label"] for transaction in transactions):
		transactions.append(hire_transaction)

	return data
