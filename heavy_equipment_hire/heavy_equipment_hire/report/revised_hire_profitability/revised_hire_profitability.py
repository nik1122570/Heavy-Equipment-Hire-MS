import frappe
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": "Simulation", "fieldname": "simulation", "fieldtype": "Link", "options": "Hire Quotation Simulation", "width": 170},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 170},
		{"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 150},
		{"label": "Machine", "fieldname": "machine", "fieldtype": "Link", "options": "Equipment Machine", "width": 150},
		{"label": "Sales Order", "fieldname": "sales_order", "fieldtype": "Link", "options": "Sales Order", "width": 160},
		{"label": "Original Revenue", "fieldname": "original_revenue", "fieldtype": "Currency", "width": 140},
		{"label": "Original Cost", "fieldname": "original_cost", "fieldtype": "Currency", "width": 130},
		{"label": "Original Profit", "fieldname": "original_profit", "fieldtype": "Currency", "width": 130},
		{"label": "Added Revenue", "fieldname": "added_revenue", "fieldtype": "Currency", "width": 130},
		{"label": "Added Cost", "fieldname": "added_cost", "fieldtype": "Currency", "width": 130},
		{"label": "Revised Revenue", "fieldname": "revised_revenue", "fieldtype": "Currency", "width": 140},
		{"label": "Revised Cost", "fieldname": "revised_cost", "fieldtype": "Currency", "width": 130},
		{"label": "Revised Profit", "fieldname": "revised_profit", "fieldtype": "Currency", "width": 130},
		{"label": "Revised Margin %", "fieldname": "revised_margin", "fieldtype": "Percent", "width": 130},
	]


def get_data(filters):
	conditions = ["hqs.docstatus = 1"]
	params = {}
	for fieldname in ("customer", "project", "machine"):
		if filters.get(fieldname):
			conditions.append(f"hqs.{fieldname} = %({fieldname})s")
			params[fieldname] = filters.get(fieldname)

	rows = frappe.db.sql(
		f"""
		select
			hqs.name as simulation,
			hqs.customer,
			hqs.project,
			hqs.machine,
			so.name as sales_order,
			hqs.total_expected_revenue as original_revenue,
			hqs.total_expected_cost as original_cost,
			hqs.expected_profit as original_profit,
			coalesce(sum(hca.additional_revenue), 0) as added_revenue,
			coalesce(sum(hca.additional_cost), 0) as added_cost
		from `tabHire Quotation Simulation` hqs
		left join `tabHire Commercial Adjustment` hca
			on hca.hire_quotation_simulation = hqs.name and hca.docstatus = 1
		left join `tabSales Order` so
			on so.custom_hire_quotation_simulation = hqs.name and so.docstatus != 2
		where {" and ".join(conditions)}
		group by hqs.name, hqs.customer, hqs.project, hqs.machine, so.name,
			hqs.total_expected_revenue, hqs.total_expected_cost, hqs.expected_profit
		order by hqs.modified desc
		""",
		params,
		as_dict=True,
	)

	for row in rows:
		row.revised_revenue = flt(row.original_revenue) + flt(row.added_revenue)
		row.revised_cost = flt(row.original_cost) + flt(row.added_cost)
		row.revised_profit = flt(row.revised_revenue) - flt(row.revised_cost)
		row.revised_margin = flt(row.revised_profit) / flt(row.revised_revenue) * 100 if flt(row.revised_revenue) else 0

	return rows
