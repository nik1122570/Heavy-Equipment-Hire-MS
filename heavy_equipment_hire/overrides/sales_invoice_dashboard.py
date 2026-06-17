from frappe import _
from erpnext.accounts.doctype.sales_invoice.sales_invoice_dashboard import (
	get_data as get_erpnext_sales_invoice_dashboard,
)


def get_data(data=None):
	if data is None:
		data = get_erpnext_sales_invoice_dashboard()

	data.setdefault("internal_links", {}).update(
		{
			"Hire Quotation Simulation": "custom_hire_quotation_simulation",
			"Hire Commercial Adjustment": "custom_hire_commercial_adjustment",
		}
	)

	hire_transaction = {"label": _("Hire"), "items": ["Hire Quotation Simulation", "Hire Commercial Adjustment"]}
	transactions = data.setdefault("transactions", [])
	if not any(transaction.get("label") == hire_transaction["label"] for transaction in transactions):
		transactions.append(hire_transaction)

	return data
