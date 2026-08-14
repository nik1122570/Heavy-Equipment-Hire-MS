import re

import frappe
from frappe import _
from frappe.utils import flt, getdate, strip_html


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)
	rows = get_invoice_rows(filters)
	data = build_grouped_rows(rows)
	return get_columns(), data, None, get_chart(rows), get_report_summary(rows)


def validate_filters(filters):
	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("From Date and To Date are required."))
	if getdate(filters.to_date) < getdate(filters.from_date):
		frappe.throw(_("To Date cannot be before From Date."))


def get_columns():
	return [
		{"label": _("Machine"), "fieldname": "machine", "fieldtype": "Data", "width": 260},
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 115},
		{"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 185},
		{"label": _("Item"), "fieldname": "item", "fieldtype": "Data", "width": 260},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 145},
		{"label": _("Sales Invoice"), "fieldname": "sales_invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 160},
	]


def get_invoice_rows(filters):
	conditions = [
		"si.docstatus = 1",
		"si.posting_date between %(from_date)s and %(to_date)s",
	]
	params = {
		"from_date": filters.from_date,
		"to_date": filters.to_date,
	}

	if filters.get("cost_center"):
		conditions.append("sii.cost_center = %(cost_center)s")
		params["cost_center"] = filters.cost_center
	if filters.get("customer"):
		conditions.append("si.customer = %(customer)s")
		params["customer"] = filters.customer

	return frappe.db.sql(
		f"""
		select
			si.posting_date,
			si.name as sales_invoice,
			si.customer,
			coalesce(si.customer_name, si.customer) as customer_name,
			sii.item_code,
			sii.item_name,
			sii.description,
			sii.cost_center,
			sii.base_net_amount as amount
		from `tabSales Invoice` si
		inner join `tabSales Invoice Item` sii on sii.parent = si.name
		where {" and ".join(conditions)}
		order by sii.cost_center asc, si.posting_date asc, si.customer_name asc, si.customer asc, si.name asc, sii.idx asc
		""",
		params,
		as_dict=True,
	)


def build_grouped_rows(rows):
	grouped = {}
	for row in rows:
		machine = row.cost_center or _("No Machine / Cost Center")
		grouped.setdefault(machine, [])
		grouped[machine].append(row)

	data = []
	for machine, machine_rows in grouped.items():
		total = sum(flt(row.amount) for row in machine_rows)
		data.append(
			frappe._dict(
				{
					"machine": f"{machine} ({len(machine_rows)})",
					"amount": total,
					"is_group": 1,
					"indent": 0,
				}
			)
		)

		for row in machine_rows:
			data.append(
				frappe._dict(
					{
						"machine": "",
						"date": row.posting_date,
						"customer": row.customer,
						"item": clean_description(row.description) or row.item_name or row.item_code,
						"amount": flt(row.amount),
						"sales_invoice": row.sales_invoice,
						"indent": 1,
					}
				)
			)

	return data


def clean_description(description):
	if not description:
		return ""
	description = strip_html(description)
	description = re.sub(r"\s+", " ", description)
	return description.strip()


def get_report_summary(rows):
	total_amount = sum(flt(row.amount) for row in rows)
	customers = len({row.customer for row in rows if row.customer})
	cost_centers = len({row.cost_center for row in rows if row.cost_center})
	invoices = len({row.sales_invoice for row in rows if row.sales_invoice})

	return [
		{"value": total_amount, "label": _("Total Sales"), "datatype": "Currency", "indicator": "Blue"},
		{"value": len(rows), "label": _("Sales Lines"), "datatype": "Int", "indicator": "Green"},
		{"value": customers, "label": _("Customers"), "datatype": "Int", "indicator": "Purple"},
		{"value": cost_centers, "label": _("Cost Centers"), "datatype": "Int", "indicator": "Orange"},
		{"value": invoices, "label": _("Invoices"), "datatype": "Int", "indicator": "Grey"},
	]


def get_chart(rows):
	if not rows:
		return {}

	totals = {}
	for row in rows:
		cost_center = row.cost_center or _("No Cost Center")
		totals[cost_center] = totals.get(cost_center, 0) + flt(row.amount)

	top_cost_centers = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:12]
	return {
		"data": {
			"labels": [cost_center for cost_center, _amount in top_cost_centers],
			"datasets": [
				{
					"name": _("Sales Amount"),
					"values": [flt(amount, 2) for _cost_center, amount in top_cost_centers],
				}
			],
		},
		"type": "line",
		"lineOptions": {
			"regionFill": 1,
			"hideDots": 0,
			"heatline": 1,
		},
		"axisOptions": {
			"xIsSeries": 1,
		},
		"colors": ["#10b981"],
	}
