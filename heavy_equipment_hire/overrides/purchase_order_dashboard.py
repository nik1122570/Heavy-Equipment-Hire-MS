from frappe import _
from erpnext.buying.doctype.purchase_order.purchase_order_dashboard import (
	get_data as get_erpnext_purchase_order_dashboard,
)


def get_data(data=None):
	if data is None:
		data = get_erpnext_purchase_order_dashboard()

	data.setdefault("internal_links", {}).update(
		{
			"Equipment Maintenance Job Card": "custom_equipment_maintenance_job_card",
			"Equipment Machine": "custom_equipment_machine",
		}
	)

	hire_transaction = {"label": _("Maintenance"), "items": ["Equipment Maintenance Job Card", "Equipment Machine"]}
	transactions = data.setdefault("transactions", [])
	if not any(transaction.get("label") == hire_transaction["label"] for transaction in transactions):
		transactions.append(hire_transaction)

	return data
