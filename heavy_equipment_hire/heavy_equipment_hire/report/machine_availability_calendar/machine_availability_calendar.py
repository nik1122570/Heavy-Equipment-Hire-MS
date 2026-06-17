import frappe
from frappe.utils import add_days, date_diff, getdate, today


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Machine", "fieldname": "machine", "fieldtype": "Link", "options": "Equipment Machine", "width": 180},
		{"label": "Machine Name", "fieldname": "machine_name", "fieldtype": "Data", "width": 180},
		{"label": "Type", "fieldname": "machine_type", "fieldtype": "Data", "width": 120},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 140},
		{"label": "Availability", "fieldname": "availability", "fieldtype": "Data", "width": 130},
		{"label": "Insurance", "fieldname": "insurance_status_summary", "fieldtype": "Data", "width": 190},
		{"label": "Sales Order", "fieldname": "sales_order", "fieldtype": "Link", "options": "Sales Order", "width": 180},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 180},
		{"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 180},
		{"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 180},
		{"label": "From Date", "fieldname": "from_date", "fieldtype": "Date", "width": 110},
		{"label": "To Date", "fieldname": "to_date", "fieldtype": "Date", "width": 110},
		{"label": "Booked Days", "fieldname": "booked_days", "fieldtype": "Int", "width": 110},
	]


def get_data(filters):
	filters = normalize_filters(filters)
	params = {
		"from_date": filters.from_date,
		"to_date": filters.to_date,
		"machine": filters.get("machine"),
		"customer": filters.get("customer"),
		"project": filters.get("project"),
	}

	conditions = []
	if filters.get("machine"):
		conditions.append("em.name = %(machine)s")

	booking_conditions = [
		"so.custom_hire_from_date <= %(to_date)s",
		"so.custom_hire_to_date >= %(from_date)s",
	]
	if filters.get("customer"):
		booking_conditions.append("so.customer = %(customer)s")
	if filters.get("project"):
		booking_conditions.append("so.project = %(project)s")

	where_clause = f"where {' and '.join(conditions)}" if conditions else ""

	rows = frappe.db.sql(
		f"""
		select
			em.name as machine,
			em.machine_name,
			em.machine_type,
			em.status,
			em.insurance_status,
			em.insurance_status_summary,
			so.name as sales_order,
			so.customer,
			so.customer_name,
			so.project,
			so.custom_hire_from_date as from_date,
			so.custom_hire_to_date as to_date
		from `tabEquipment Machine` em
		left join `tabSales Order` so
			on so.custom_equipment_machine = em.name
			and so.docstatus = 1
			and {" and ".join(booking_conditions)}
		{where_clause}
		order by em.machine_name, so.custom_hire_from_date
		""",
		params,
		as_dict=True,
	)

	for row in rows:
		row.availability = get_availability(row)
		row.booked_days = get_booked_days(row, filters)

	return rows


def normalize_filters(filters):
	filters = frappe._dict(filters or {})
	if not filters.get("from_date"):
		filters.from_date = today()
	if not filters.get("to_date"):
		filters.to_date = add_days(filters.from_date, 30)
	if getdate(filters.to_date) < getdate(filters.from_date):
		frappe.throw("To Date cannot be before From Date.")
	return filters


def get_availability(row):
	if row.status in ("Under Maintenance", "Maintenance Required", "Out of Service"):
		return row.status
	if not row.sales_order:
		return "Available"
	current_date = getdate(today())
	if getdate(row.from_date) <= current_date <= getdate(row.to_date):
		return "On Hire"
	if getdate(row.from_date) > current_date:
		return "Booked"
	return "Completed"


def get_booked_days(row, filters):
	if not row.sales_order:
		return 0
	start = max(getdate(row.from_date), getdate(filters.from_date))
	end = min(getdate(row.to_date), getdate(filters.to_date))
	return max(date_diff(end, start) + 1, 0)


@frappe.whitelist()
def get_calendar_data(from_date=None, to_date=None, machine=None, customer=None, project=None):
	filters = normalize_filters(
		{
			"from_date": from_date,
			"to_date": to_date,
			"machine": machine,
			"customer": customer,
			"project": project,
		}
	)
	rows = get_data(filters)
	return {
		"from_date": filters.from_date,
		"to_date": filters.to_date,
		"dates": get_dates(filters.from_date, filters.to_date),
		"machines": group_by_machine(rows),
	}


def get_dates(from_date, to_date):
	days = date_diff(to_date, from_date)
	return [add_days(from_date, index) for index in range(days + 1)]


def group_by_machine(rows):
	machines = {}
	for row in rows:
		machine = machines.setdefault(
			row.machine,
			{
				"machine": row.machine,
				"machine_name": row.machine_name,
				"machine_type": row.machine_type,
				"status": row.status,
				"insurance_status": row.insurance_status,
				"insurance_status_summary": row.insurance_status_summary,
				"bookings": [],
			},
		)
		if row.sales_order:
			machine["bookings"].append(
				{
					"sales_order": row.sales_order,
					"customer": row.customer,
					"customer_name": row.customer_name,
					"project": row.project,
					"from_date": row.from_date,
					"to_date": row.to_date,
					"availability": row.availability,
					"booked_days": row.booked_days,
				}
			)

	return list(machines.values())
