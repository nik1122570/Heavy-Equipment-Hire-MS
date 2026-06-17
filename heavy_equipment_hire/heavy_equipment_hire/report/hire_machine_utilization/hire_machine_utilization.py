import frappe
from frappe.utils import date_diff, flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": "Machine", "fieldname": "machine", "fieldtype": "Link", "options": "Equipment Machine", "width": 170},
		{"label": "Cost Center", "fieldname": "cost_center", "fieldtype": "Link", "options": "Cost Center", "width": 170},
		{"label": "Hired Days", "fieldname": "hired_days", "fieldtype": "Float", "width": 110},
		{"label": "Available Days", "fieldname": "available_days", "fieldtype": "Float", "width": 120},
		{"label": "Utilization %", "fieldname": "utilization", "fieldtype": "Percent", "width": 120},
		{"label": "Actual Hours", "fieldname": "actual_hours", "fieldtype": "Float", "width": 110},
		{"label": "Revenue", "fieldname": "revenue", "fieldtype": "Currency", "width": 130},
	]


def get_data(filters):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	if not (from_date and to_date):
		frappe.throw("From Date and To Date are required.")

	available_days = max(date_diff(to_date, from_date) + 1, 1)
	rows = frappe.db.sql(
		"""
		select
			custom_equipment_machine as machine,
			custom_machine_cost_center as cost_center,
			sum(datediff(custom_hire_to_date, custom_hire_from_date) + 1) as hired_days,
			0 as actual_hours,
			sum(grand_total) as revenue
		from `tabSales Order`
		where docstatus = 1
			and custom_equipment_machine is not null
			and custom_hire_from_date <= %(to_date)s
			and custom_hire_to_date >= %(from_date)s
		group by custom_equipment_machine, custom_machine_cost_center
		order by custom_equipment_machine
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)
	for row in rows:
		row.available_days = available_days
		row.utilization = flt(row.hired_days) / available_days * 100
	return rows
