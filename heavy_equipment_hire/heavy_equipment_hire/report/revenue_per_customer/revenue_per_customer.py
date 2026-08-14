import re

import frappe
from frappe import _
from frappe.utils import flt, getdate, strip_html


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)
	rows = get_revenue_rows(filters)
	data = build_grouped_rows(rows)
	return get_columns(), data, None, get_chart(rows, filters), get_report_summary(rows)


def validate_filters(filters):
	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("From Date and To Date are required."))
	if getdate(filters.to_date) < getdate(filters.from_date):
		frappe.throw(_("To Date cannot be before From Date."))


def get_columns():
	return [
		{"label": _("Customer"), "fieldname": "customer_header", "fieldtype": "Data", "width": 260},
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 115},
		{"label": _("Machine / Cost Center"), "fieldname": "machine", "fieldtype": "Link", "options": "Cost Center", "width": 245},
		{"label": _("Item"), "fieldname": "item", "fieldtype": "Data", "width": 260},
		{"label": _("Source"), "fieldname": "source", "fieldtype": "Data", "width": 110},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 145},
		{"label": _("Reference Type"), "fieldname": "reference_doctype", "fieldtype": "Data", "hidden": 1},
		{
			"label": _("Reference"),
			"fieldname": "reference_name",
			"fieldtype": "Dynamic Link",
			"options": "reference_doctype",
			"width": 170,
		},
	]


def get_revenue_rows(filters):
	rows = get_invoice_rows(filters) + get_journal_entry_rows(filters)
	return sorted(
		rows,
		key=lambda row: (
			row.customer_name or row.customer or "",
			row.customer or "",
			getdate(row.posting_date),
			row.cost_center or "",
			row.reference_name or "",
			row.idx or 0,
		),
	)


def get_invoice_rows(filters):
	conditions = [
		"si.docstatus = 1",
		"si.posting_date between %(from_date)s and %(to_date)s",
	]
	params = {
		"from_date": filters.from_date,
		"to_date": filters.to_date,
	}

	if filters.get("customer"):
		conditions.append("si.customer = %(customer)s")
		params["customer"] = filters.customer
	if filters.get("cost_center"):
		conditions.append("sii.cost_center = %(cost_center)s")
		params["cost_center"] = filters.cost_center

	return frappe.db.sql(
		f"""
		select
			si.posting_date,
			'Sales Invoice' as source,
			'Sales Invoice' as reference_doctype,
			si.name as reference_name,
			si.customer,
			coalesce(si.customer_name, si.customer) as customer_name,
			sii.item_code,
			sii.item_name,
			sii.description,
			sii.cost_center,
			sii.base_net_amount as amount,
			sii.idx
		from `tabSales Invoice` si
		inner join `tabSales Invoice Item` sii on sii.parent = si.name
		where {" and ".join(conditions)}
		order by si.customer_name asc, si.customer asc, si.posting_date asc, sii.cost_center asc, si.name asc, sii.idx asc
		""",
		params,
		as_dict=True,
	)


def get_journal_entry_rows(filters):
	customer_expr = """
		coalesce(
			nullif(if(jea.party_type = 'Customer', jea.party, ''), ''),
			if(customer_party.customer_count = 1, customer_party.customer, null)
		)
	"""
	conditions = [
		"je.docstatus = 1",
		"je.posting_date between %(from_date)s and %(to_date)s",
		f"{customer_expr} is not null",
		"account.root_type = 'Income'",
		"(jea.credit - jea.debit) != 0",
	]
	params = {
		"from_date": filters.from_date,
		"to_date": filters.to_date,
	}

	if filters.get("customer"):
		conditions.append(f"{customer_expr} = %(customer)s")
		params["customer"] = filters.customer
	if filters.get("cost_center"):
		conditions.append("jea.cost_center = %(cost_center)s")
		params["cost_center"] = filters.cost_center

	return frappe.db.sql(
		f"""
		select
			je.posting_date,
			'Journal Entry' as source,
			'Journal Entry' as reference_doctype,
			je.name as reference_name,
			{customer_expr} as customer,
			coalesce(customer.customer_name, {customer_expr}) as customer_name,
			jea.account as item_code,
			jea.account as item_name,
			coalesce(nullif(jea.user_remark, ''), nullif(je.remark, ''), jea.account) as description,
			jea.cost_center,
			(jea.credit - jea.debit) as amount,
			jea.idx
		from `tabJournal Entry` je
		inner join `tabJournal Entry Account` jea on jea.parent = je.name
		inner join `tabAccount` account on account.name = jea.account
		left join (
			select
				parent,
				min(party) as customer,
				count(distinct party) as customer_count
			from `tabJournal Entry Account`
			where party_type = 'Customer' and ifnull(party, '') != ''
			group by parent
		) customer_party on customer_party.parent = je.name
		left join `tabCustomer` customer on customer.name = {customer_expr}
		where {" and ".join(conditions)}
		order by customer.customer_name asc, jea.party asc, je.posting_date asc, jea.cost_center asc, je.name asc, jea.idx asc
		""",
		params,
		as_dict=True,
	)


def build_grouped_rows(rows):
	grouped = {}
	for row in rows:
		customer = row.customer_name or row.customer or _("No Customer")
		grouped.setdefault(customer, [])
		grouped[customer].append(row)

	data = []
	for customer, customer_rows in grouped.items():
		total = sum(flt(row.amount) for row in customer_rows)
		data.append(
			frappe._dict(
				{
					"customer_header": f"{customer} ({len(customer_rows)})",
					"amount": total,
					"is_group": 1,
					"indent": 0,
				}
			)
		)

		for row in customer_rows:
			data.append(
				frappe._dict(
					{
						"customer_header": "",
						"date": row.posting_date,
						"machine": row.cost_center,
						"item": clean_description(row.description) or row.item_name or row.item_code,
						"source": row.source,
						"amount": flt(row.amount),
						"reference_doctype": row.reference_doctype,
						"reference_name": row.reference_name,
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
	machines = len({row.cost_center for row in rows if row.cost_center})
	references = len({(row.reference_doctype, row.reference_name) for row in rows if row.reference_name})
	most_served = get_most_served_customer(rows)
	top_revenue = get_top_revenue_customer(rows)

	return [
		{"value": total_amount, "label": _("Total Revenue"), "datatype": "Currency", "indicator": "Blue"},
		{"value": len(rows), "label": _("Revenue Lines"), "datatype": "Int", "indicator": "Green"},
		{"value": customers, "label": _("Customers"), "datatype": "Int", "indicator": "Purple"},
		{"value": machines, "label": _("Machines"), "datatype": "Int", "indicator": "Orange"},
		{"value": references, "label": _("References"), "datatype": "Int", "indicator": "Grey"},
		{"value": most_served, "label": _("Most Served Customer"), "datatype": "Data", "indicator": "Green"},
		{"value": top_revenue, "label": _("Top Revenue Customer"), "datatype": "Data", "indicator": "Blue"},
	]


def get_most_served_customer(rows):
	if not rows:
		return ""

	references_by_customer = {}
	for row in rows:
		customer = row.customer_name or row.customer or _("No Customer")
		references_by_customer.setdefault(customer, set())
		if row.reference_name:
			references_by_customer[customer].add((row.reference_doctype, row.reference_name))

	customer, references = max(references_by_customer.items(), key=lambda item: len(item[1]))
	return _("{0} ({1})").format(customer, len(references))


def get_top_revenue_customer(rows):
	if not rows:
		return ""

	revenue_by_customer = {}
	for row in rows:
		customer = row.customer_name or row.customer or _("No Customer")
		revenue_by_customer[customer] = revenue_by_customer.get(customer, 0) + flt(row.amount)

	customer, amount = max(revenue_by_customer.items(), key=lambda item: item[1])
	return _("{0} ({1})").format(customer, frappe.format(flt(amount, 2), {"fieldtype": "Currency"}))


def get_chart(rows, filters):
	if not rows:
		return {}

	if filters.get("chart_view") == "Most Served Customers":
		return get_customer_pie_chart(rows)

	return get_revenue_line_chart(rows)


def get_revenue_line_chart(rows):
	daily_revenue = {}
	for row in rows:
		date = str(row.posting_date)
		daily_revenue[date] = daily_revenue.get(date, 0) + flt(row.amount)

	labels = sorted(daily_revenue)
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": _("Revenue"),
					"values": [flt(daily_revenue[date], 2) for date in labels],
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
		"colors": ["#2563eb"],
	}


def get_customer_pie_chart(rows):
	references_by_customer = {}
	for row in rows:
		customer = row.customer_name or row.customer or _("No Customer")
		references_by_customer.setdefault(customer, set())
		if row.reference_name:
			references_by_customer[customer].add((row.reference_doctype, row.reference_name))

	top_customers = sorted(references_by_customer.items(), key=lambda item: len(item[1]), reverse=True)[:10]
	return {
		"data": {
			"labels": [customer for customer, _references in top_customers],
			"datasets": [
				{
					"name": _("References Served"),
					"values": [len(references) for _customer, references in top_customers],
				}
			],
		},
		"type": "pie",
		"colors": ["#2563eb", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#84cc16", "#f97316", "#ec4899", "#64748b"],
	}
