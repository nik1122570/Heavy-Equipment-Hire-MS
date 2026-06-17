import frappe
from frappe.utils import date_diff, flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": "Machine", "fieldname": "machine", "fieldtype": "Link", "options": "Equipment Machine", "width": 180},
		{"label": "Machine Name", "fieldname": "machine_name", "fieldtype": "Data", "width": 180},
		{"label": "Cost Center", "fieldname": "cost_center", "fieldtype": "Link", "options": "Cost Center", "width": 170},
		{"label": "Hired Days", "fieldname": "hired_days", "fieldtype": "Float", "width": 120},
		{"label": "Utilization %", "fieldname": "utilization", "fieldtype": "Percent", "width": 120},
		{"label": "Hire Revenue", "fieldname": "hire_amount", "fieldtype": "Currency", "width": 140},
		{"label": "Fuel Cost", "fieldname": "fuel_cost", "fieldtype": "Currency", "width": 140},
		{"label": "Maintenance Cost", "fieldname": "maintenance_cost", "fieldtype": "Currency", "width": 150},
		{"label": "Net Margin", "fieldname": "net_margin", "fieldtype": "Currency", "width": 140},
	]


def get_data(filters):
	filters = frappe._dict(filters or {})
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	available_days = max(date_diff(to_date, from_date) + 1, 1) if from_date and to_date else 0

	conditions = ["so.docstatus = 1", "so.custom_equipment_machine is not null"]
	params = {
		"available_days": available_days,
		"from_date": from_date,
		"to_date": to_date,
	}
	if filters.get("from_date"):
		conditions.append("so.custom_hire_to_date >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("so.custom_hire_from_date <= %(to_date)s")

	rows = frappe.db.sql(
		f"""
		select
			em.name as machine,
			em.machine_name,
			em.cost_center,
			coalesce(
				sum(
					datediff(
						least(so.custom_hire_to_date, coalesce(%(to_date)s, so.custom_hire_to_date)),
						greatest(so.custom_hire_from_date, coalesce(%(from_date)s, so.custom_hire_from_date))
					) + 1
				),
				0
			) as hired_days,
			coalesce(sum(so.grand_total), 0) as hire_amount,
			0 as fuel_cost,
			0 as maintenance_cost,
			coalesce(sum(so.grand_total), 0) as net_margin
		from `tabEquipment Machine` em
		left join `tabSales Order` so
			on so.custom_equipment_machine = em.name and {" and ".join(conditions)}
		group by em.name, em.machine_name, em.cost_center
		order by em.machine_name
		""",
		params,
		as_dict=True,
	)
	for row in rows:
		row.utilization = flt(row.hired_days) / available_days * 100 if available_days else 0
	return rows
