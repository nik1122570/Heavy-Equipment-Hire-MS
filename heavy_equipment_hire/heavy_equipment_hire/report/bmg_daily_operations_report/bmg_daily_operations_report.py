import re

import frappe
from frappe import _
from frappe.utils import flt, getdate, strip_html


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)
	rows = get_operation_rows(filters)
	data = build_grouped_rows(rows)
	return get_columns(), data, None, get_chart(rows), get_report_summary(rows)


def validate_filters(filters):
	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("From Date and To Date are required."))
	if getdate(filters.to_date) < getdate(filters.from_date):
		frappe.throw(_("To Date cannot be before From Date."))


def get_columns():
	return [
		{"label": _("Date / Machine"), "fieldname": "operation_date", "fieldtype": "Data", "width": 150},
		{
			"label": _("Equipment Machine"),
			"fieldname": "equipment_machine",
			"fieldtype": "Link",
			"options": "Equipment Machine",
			"width": 155,
		},
		{"label": _("Machine Name"), "fieldname": "machine_name", "fieldtype": "Data", "width": 175},
		{"label": _("Fleet Owner"), "fieldname": "fleet_owner", "fieldtype": "Data", "width": 105},
		{"label": _("Asset Group"), "fieldname": "asset_group", "fieldtype": "Data", "width": 105},
		{"label": _("Status"), "fieldname": "operation_status", "fieldtype": "Data", "width": 135},
		{"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 165},
		{"label": _("Payment Status"), "fieldname": "payment_status", "fieldtype": "Data", "width": 125},
		{"label": _("Payment Amount"), "fieldname": "payment_amount", "fieldtype": "Currency", "width": 130},
		{"label": _("Hours Worked"), "fieldname": "hours_worked", "fieldtype": "Float", "width": 115},
		{"label": _("Meter Reading"), "fieldname": "hours_meter_reading", "fieldtype": "Float", "width": 120},
		{"label": _("Full Day"), "fieldname": "full_day", "fieldtype": "Check", "width": 85},
		{"label": _("Half Day"), "fieldname": "half_day", "fieldtype": "Check", "width": 85},
		{"label": _("Chargeable Days"), "fieldname": "chargeable_days", "fieldtype": "Float", "width": 125},
		{"label": _("Operator / Driver"), "fieldname": "operator", "fieldtype": "Link", "options": "Operator", "width": 145},
		{"label": _("Location"), "fieldname": "location", "fieldtype": "Data", "width": 150},
		{"label": _("Work Done / Notes"), "fieldname": "work_done", "fieldtype": "Small Text", "width": 300},
		{"label": _("Idle Reason"), "fieldname": "idle_reason", "fieldtype": "Small Text", "width": 220},
		{"label": _("Cost Center"), "fieldname": "cost_center", "fieldtype": "Link", "options": "Cost Center", "width": 170},
		{
			"label": _("Operation Log"),
			"fieldname": "operation_log",
			"fieldtype": "Link",
			"options": "Equipment Operation Log",
			"width": 155,
		},
	]


def get_operation_rows(filters):
	conditions = [
		"docstatus != 2",
		"operation_date between %(from_date)s and %(to_date)s",
	]
	params = {
		"from_date": filters.from_date,
		"to_date": filters.to_date,
	}

	for fieldname in (
		"equipment_machine",
		"fleet_owner",
		"asset_group",
		"operation_status",
		"customer",
		"cost_center",
	):
		if filters.get(fieldname):
			conditions.append(f"{fieldname} = %({fieldname})s")
			params[fieldname] = filters.get(fieldname)

	if filters.get("billable_only"):
		conditions.append("(full_day = 1 or half_day = 1)")

	rows = frappe.db.sql(
		f"""
		select
			name as operation_log,
			operation_date,
			equipment_machine,
			machine_name,
			fleet_owner,
			asset_group,
			operation_status,
			customer,
			payment_status,
			payment_amount,
			hours_worked,
			hours_meter_reading,
			full_day,
			half_day,
			operator,
			location,
			work_done,
			idle_reason,
			cost_center
		from `tabEquipment Operation Log`
		where {" and ".join(conditions)}
		order by operation_date asc, fleet_owner asc, asset_group asc, equipment_machine asc, name asc
		""",
		params,
		as_dict=True,
	)

	for row in rows:
		row.hours_worked = flt(row.hours_worked, 2)
		row.hours_meter_reading = flt(row.hours_meter_reading, 2)
		row.payment_amount = flt(row.payment_amount, 2)
		row.full_day = 1 if row.full_day else 0
		row.half_day = 1 if row.half_day else 0
		row.chargeable_days = get_chargeable_days(row)
		row.work_done = clean_text(row.work_done)
		row.idle_reason = clean_text(row.idle_reason)

	return rows


def build_grouped_rows(rows):
	grouped = {}
	for row in rows:
		grouped.setdefault(row.operation_date, [])
		grouped[row.operation_date].append(row)

	data = []
	for operation_date, date_rows in grouped.items():
		data.append(
			frappe._dict(
				{
					"operation_date": operation_date,
					"hours_worked": sum(flt(row.hours_worked) for row in date_rows),
					"payment_amount": sum(flt(row.payment_amount) for row in date_rows),
					"chargeable_days": sum(flt(row.chargeable_days) for row in date_rows),
					"is_group": 1,
					"indent": 0,
				}
			)
		)

		for row in date_rows:
			row.indent = 1
			data.append(row)

	return data


def get_chargeable_days(row):
	if row.full_day:
		return 1
	if row.half_day:
		return 0.5
	return 0


def clean_text(value):
	if not value:
		return ""
	value = strip_html(value)
	value = re.sub(r"\s+", " ", value)
	return value.strip()


def get_report_summary(rows):
	total_hours = sum(flt(row.hours_worked) for row in rows)
	full_days = sum(1 for row in rows if row.full_day)
	half_days = sum(1 for row in rows if row.half_day)
	chargeable_days = sum(flt(row.chargeable_days) for row in rows)
	total_payment = sum(flt(row.payment_amount) for row in rows)
	working_logs = sum(1 for row in rows if row.operation_status == "Working")
	idle_logs = sum(1 for row in rows if row.operation_status in ("Idle", "Waiting Customer Order", "Waiting Loading"))
	machines = len({row.equipment_machine for row in rows if row.equipment_machine})

	return [
		{"value": len(rows), "label": _("Operation Logs"), "datatype": "Int", "indicator": "Blue"},
		{"value": machines, "label": _("Machines"), "datatype": "Int", "indicator": "Purple"},
		{"value": total_hours, "label": _("Hours Worked"), "datatype": "Float", "indicator": "Green"},
		{"value": chargeable_days, "label": _("Chargeable Days"), "datatype": "Float", "indicator": "Green"},
		{"value": full_days, "label": _("Full Days"), "datatype": "Int", "indicator": "Blue"},
		{"value": half_days, "label": _("Half Days"), "datatype": "Int", "indicator": "Orange"},
		{"value": working_logs, "label": _("Working Logs"), "datatype": "Int", "indicator": "Green"},
		{"value": idle_logs, "label": _("Idle / Waiting Logs"), "datatype": "Int", "indicator": "Orange"},
		{"value": total_payment, "label": _("Payment Amount"), "datatype": "Currency", "indicator": "Blue"},
	]


def get_chart(rows):
	if not rows:
		return {}

	daily_summary = {}
	for row in rows:
		key = str(row.operation_date)
		if key not in daily_summary:
			daily_summary[key] = {"hours": 0, "chargeable_days": 0}
		daily_summary[key]["hours"] += flt(row.hours_worked)
		daily_summary[key]["chargeable_days"] += flt(row.chargeable_days)

	labels = sorted(daily_summary)
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": _("Hours Worked"),
					"values": [flt(daily_summary[date]["hours"], 2) for date in labels],
				},
				{
					"name": _("Chargeable Days"),
					"values": [flt(daily_summary[date]["chargeable_days"], 2) for date in labels],
				},
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
		"colors": ["#2563eb", "#f59e0b"],
	}
