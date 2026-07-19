import re

import frappe
from frappe import _
from frappe.utils import flt, getdate, strip_html


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)
	rows = get_purchase_rows(filters)
	data = build_grouped_rows(rows)
	return get_columns(), data, None, get_chart(rows), get_report_summary(rows)


def validate_filters(filters):
	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("From Date and To Date are required."))
	if getdate(filters.to_date) < getdate(filters.from_date):
		frappe.throw(_("To Date cannot be before From Date."))


def get_columns():
	return [
		{"label": _("Cost Center"), "fieldname": "cost_center", "fieldtype": "Data", "width": 230},
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": _("Description"), "fieldname": "description", "fieldtype": "Small Text", "width": 430},
		{"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 190},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 145},
		{"label": _("Account"), "fieldname": "account", "fieldtype": "Link", "options": "Account", "width": 210},
		{"label": _("Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 150},
		{
			"label": _("Purchase Invoice"),
			"fieldname": "purchase_invoice",
			"fieldtype": "Link",
			"options": "Purchase Invoice",
			"width": 160,
		},
	]


def get_purchase_rows(filters):
	conditions = [
		"pi.docstatus = 1",
		"pi.posting_date between %(from_date)s and %(to_date)s",
	]
	params = {
		"from_date": filters.from_date,
		"to_date": filters.to_date,
	}

	if filters.get("cost_center"):
		conditions.append("pii.cost_center = %(cost_center)s")
		params["cost_center"] = filters.cost_center
	if filters.get("supplier"):
		conditions.append("pi.supplier = %(supplier)s")
		params["supplier"] = filters.supplier
	if filters.get("item"):
		conditions.append("pii.item_code = %(item)s")
		params["item"] = filters.item
	if filters.get("account"):
		conditions.append("pii.expense_account = %(account)s")
		params["account"] = filters.account

	return frappe.db.sql(
		f"""
		select
			pi.posting_date as date,
			pi.name as purchase_invoice,
			pi.supplier,
			coalesce(pi.supplier_name, pi.supplier) as supplier_name,
			pii.item_code as item,
			pii.item_name,
			pii.description,
			pii.cost_center,
			pii.expense_account as account,
			pii.base_amount as amount
		from `tabPurchase Invoice` pi
		inner join `tabPurchase Invoice Item` pii on pii.parent = pi.name
		where {" and ".join(conditions)}
		order by pii.cost_center asc, pi.posting_date asc, pi.name asc, pii.idx asc
		""",
		params,
		as_dict=True,
	)


def build_grouped_rows(rows):
	grouped = {}
	for row in rows:
		cost_center = row.cost_center or _("No Cost Center")
		grouped.setdefault(cost_center, [])
		grouped[cost_center].append(row)

	data = []
	for cost_center, cost_center_rows in grouped.items():
		total = sum(flt(row.amount) for row in cost_center_rows)
		data.append(
			frappe._dict(
				{
					"cost_center": f"{cost_center} ({len(cost_center_rows)})",
					"amount": total,
					"is_group": 1,
					"indent": 0,
				}
			)
		)

		for row in cost_center_rows:
			data.append(
				frappe._dict(
					{
						"cost_center": "",
						"date": row.date,
						"description": clean_description(row.description) or row.item_name or row.item,
						"supplier": row.supplier,
						"amount": flt(row.amount),
						"account": row.account,
						"item": row.item,
						"purchase_invoice": row.purchase_invoice,
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
	cost_centers = len({row.cost_center for row in rows if row.cost_center})
	suppliers = len({row.supplier for row in rows if row.supplier})
	items = len({row.item for row in rows if row.item})

	return [
		{"value": total_amount, "label": _("Total Procurement"), "datatype": "Currency", "indicator": "Blue"},
		{"value": len(rows), "label": _("Invoice Lines"), "datatype": "Int", "indicator": "Green"},
		{"value": cost_centers, "label": _("Cost Centers"), "datatype": "Int", "indicator": "Orange"},
		{"value": suppliers, "label": _("Suppliers"), "datatype": "Int", "indicator": "Purple"},
		{"value": items, "label": _("Items"), "datatype": "Int", "indicator": "Grey"},
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
					"name": _("Procurement Amount"),
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
		"colors": ["#0ea5e9"],
	}
