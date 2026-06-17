import frappe


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": "Sales Order", "fieldname": "sales_order", "fieldtype": "Link", "options": "Sales Order", "width": 180},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 180},
		{"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 180},
		{"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 180},
		{"label": "Machine", "fieldname": "machine", "fieldtype": "Link", "options": "Equipment Machine", "width": 180},
		{"label": "From Date", "fieldname": "from_date", "fieldtype": "Date", "width": 110},
		{"label": "To Date", "fieldname": "to_date", "fieldtype": "Date", "width": 110},
		{"label": "Discount", "fieldname": "discount_amount", "fieldtype": "Currency", "width": 120},
		{"label": "Net Total", "fieldname": "net_total", "fieldtype": "Currency", "width": 130},
		{"label": "Grand Total", "fieldname": "grand_total", "fieldtype": "Currency", "width": 140},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 120},
	]


def get_data(filters):
	conditions = ["docstatus = 1"]
	params = {}
	filter_field_map = {
		"customer": "customer",
		"project": "project",
		"machine": "custom_equipment_machine",
	}
	for fieldname, db_fieldname in filter_field_map.items():
		if filters.get(fieldname):
			conditions.append(f"{db_fieldname} = %({fieldname})s")
			params[fieldname] = filters.get(fieldname)
	if filters.get("from_date"):
		conditions.append("custom_hire_from_date >= %(from_date)s")
		params["from_date"] = filters.from_date
	if filters.get("to_date"):
		conditions.append("custom_hire_to_date <= %(to_date)s")
		params["to_date"] = filters.to_date

	return frappe.db.sql(
		f"""
		select
			name as sales_order,
			customer,
			customer_name,
			project,
			custom_equipment_machine as machine,
			custom_hire_from_date as from_date,
			custom_hire_to_date as to_date,
			discount_amount,
			net_total,
			grand_total,
			status
		from `tabSales Order`
		where {" and ".join(conditions)}
			and custom_equipment_machine is not null
		order by customer, project, custom_equipment_machine, custom_hire_from_date
		""",
		params,
		as_dict=True,
	)
