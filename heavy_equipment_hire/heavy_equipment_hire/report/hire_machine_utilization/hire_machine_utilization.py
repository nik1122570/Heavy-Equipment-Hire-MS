import frappe
from frappe.utils import date_diff, flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	data = get_data(filters)
	return get_columns(), data, None, get_chart(data)


def get_columns():
	return [
		{"label": "Machine", "fieldname": "machine", "fieldtype": "Link", "options": "Equipment Machine", "width": 170},
		{"label": "Cost Center", "fieldname": "cost_center", "fieldtype": "Link", "options": "Cost Center", "width": 170},
		{"label": "Hired Days", "fieldname": "hired_days", "fieldtype": "Float", "width": 110},
		{"label": "Available Days", "fieldname": "available_days", "fieldtype": "Float", "width": 120},
		{"label": "Utilization %", "fieldname": "utilization", "fieldtype": "Percent", "width": 120},
		{"label": "Idle %", "fieldname": "idle_percentage", "fieldtype": "Percent", "width": 100},
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
			machine.name as machine,
			machine.cost_center as cost_center,
			coalesce(hire.hired_days, 0) as hired_days,
			0 as actual_hours,
			coalesce(hire.revenue, 0) as revenue
		from `tabEquipment Machine` machine
		left join (
			select
				custom_equipment_machine as machine,
				sum(datediff(
					least(custom_hire_to_date, %(to_date)s),
					greatest(custom_hire_from_date, %(from_date)s)
				) + 1) as hired_days,
				sum(grand_total) as revenue
			from `tabSales Order`
			where docstatus = 1
				and custom_equipment_machine is not null
				and custom_hire_from_date <= %(to_date)s
				and custom_hire_to_date >= %(from_date)s
			group by custom_equipment_machine
		) hire on hire.machine = machine.name
		order by hired_days desc, machine.name
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)
	for row in rows:
		row.hired_days = min(flt(row.hired_days), available_days)
		row.available_days = available_days
		row.utilization = flt(row.hired_days) / available_days * 100
		row.idle_percentage = max(100 - flt(row.utilization), 0)
	return rows


def get_chart(data):
	chart_rows = sorted(data, key=lambda row: flt(row.utilization), reverse=True)
	return {
		"data": {
			"labels": [row.machine for row in chart_rows],
			"datasets": [
				{
					"name": "Utilization %",
					"values": [flt(row.utilization, 2) for row in chart_rows],
				}
			],
		},
		"type": "line",
		"colors": ["#2490ef"],
	}
