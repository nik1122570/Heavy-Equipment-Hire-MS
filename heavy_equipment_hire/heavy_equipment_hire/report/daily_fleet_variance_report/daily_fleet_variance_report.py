import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)
	data = get_data(filters)
	return get_columns(), data, None, get_chart(data), get_report_summary(data)


def validate_filters(filters):
	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("From Date and To Date are required."))
	if getdate(filters.to_date) < getdate(filters.from_date):
		frappe.throw(_("To Date cannot be before From Date."))


def get_columns():
	return [
		{"label": _("Date"), "fieldname": "tracking_date", "fieldtype": "Date", "width": 105},
		{"label": _("Fleet Owner"), "fieldname": "fleet_owner", "fieldtype": "Data", "width": 105},
		{"label": _("Asset Group"), "fieldname": "asset_group", "fieldtype": "Data", "width": 105},
		{
			"label": _("Equipment Machine"),
			"fieldname": "equipment_machine",
			"fieldtype": "Link",
			"options": "Equipment Machine",
			"width": 150,
		},
		{"label": _("Machine Name"), "fieldname": "machine_name", "fieldtype": "Data", "width": 170},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 105},
		{"label": _("GPS Hours"), "fieldname": "gps_hours", "fieldtype": "Float", "width": 105},
		{"label": _("Physical Hours"), "fieldname": "physical_hours", "fieldtype": "Float", "width": 115},
		{"label": _("Variance Hours"), "fieldname": "variance_hours", "fieldtype": "Float", "width": 120},
		{"label": _("Variance Direction"), "fieldname": "variance_direction", "fieldtype": "Data", "width": 140},
		{"label": _("Reason Required"), "fieldname": "reason_required", "fieldtype": "Data", "width": 120},
		{"label": _("Mileage"), "fieldname": "mileage", "fieldtype": "Float", "width": 95},
		{"label": _("Starting Location"), "fieldname": "starting_location", "fieldtype": "Small Text", "width": 220},
		{"label": _("Ending Location"), "fieldname": "ending_location", "fieldtype": "Small Text", "width": 220},
		{"label": _("Reason"), "fieldname": "reason", "fieldtype": "Small Text", "width": 220},
		{"label": _("Remarks"), "fieldname": "remarks", "fieldtype": "Small Text", "width": 220},
		{"label": _("Cost Center"), "fieldname": "cost_center", "fieldtype": "Link", "options": "Cost Center", "width": 150},
		{"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 150},
		{"label": _("Fleet Tracker"), "fieldname": "name", "fieldtype": "Link", "options": "Fleet Tracker", "width": 145},
	]


def get_data(filters):
	conditions = ["docstatus != 2", "tracking_date between %(from_date)s and %(to_date)s"]
	params = {"from_date": filters.from_date, "to_date": filters.to_date}

	for fieldname in ("fleet_owner", "asset_group", "equipment_machine", "variance_direction"):
		if filters.get(fieldname):
			conditions.append(f"{fieldname} = %({fieldname})s")
			params[fieldname] = filters.get(fieldname)

	if filters.get("exceptions_only"):
		conditions.append("abs(variance_hours) > 0")

	if filters.get("missing_reason_only"):
		conditions.append("variance_hours > 0 and coalesce(reason, '') = ''")

	rows = frappe.db.sql(
		f"""
		select
			name,
			tracking_date,
			fleet_owner,
			asset_group,
			equipment_machine,
			machine_name,
			status,
			gps_hours,
			physical_hours,
			variance_hours,
			variance_direction,
			mileage,
			starting_location,
			ending_location,
			reason,
			remarks,
			cost_center,
			project
		from `tabFleet Tracker`
		where {" and ".join(conditions)}
		order by tracking_date asc, fleet_owner asc, asset_group asc, equipment_machine asc
		""",
		params,
		as_dict=True,
	)

	for row in rows:
		row.gps_hours = flt(row.gps_hours, 2)
		row.physical_hours = flt(row.physical_hours, 2)
		row.variance_hours = flt(row.variance_hours, 2)
		row.mileage = flt(row.mileage, 2)
		row.reason_required = "Required" if row.variance_hours > 0 and not row.reason else ""

	return rows


def get_report_summary(data):
	total_gps = sum(flt(row.gps_hours) for row in data)
	total_physical = sum(flt(row.physical_hours) for row in data)
	net_variance = total_gps - total_physical
	gps_greater = sum(1 for row in data if flt(row.variance_hours) > 0)
	physical_greater = sum(1 for row in data if flt(row.variance_hours) < 0)
	no_variance = sum(1 for row in data if flt(row.variance_hours) == 0)
	missing_reason = sum(1 for row in data if flt(row.variance_hours) > 0 and not row.reason)

	return [
		{"value": len(data), "label": _("Records"), "datatype": "Int", "indicator": "Blue"},
		{"value": total_gps, "label": _("GPS Hours"), "datatype": "Float", "indicator": "Blue"},
		{"value": total_physical, "label": _("Physical Hours"), "datatype": "Float", "indicator": "Green"},
		{
			"value": net_variance,
			"label": _("Net Variance"),
			"datatype": "Float",
			"indicator": "Red" if net_variance > 0 else "Orange" if net_variance < 0 else "Green",
		},
		{"value": gps_greater, "label": _("GPS Greater Days"), "datatype": "Int", "indicator": "Red"},
		{"value": physical_greater, "label": _("Physical Greater Days"), "datatype": "Int", "indicator": "Orange"},
		{"value": no_variance, "label": _("No Variance Days"), "datatype": "Int", "indicator": "Green"},
		{"value": missing_reason, "label": _("Missing Reasons"), "datatype": "Int", "indicator": "Red" if missing_reason else "Green"},
	]


def get_chart(data):
	if not data:
		return {}

	machine_summary = {}
	for row in data:
		machine = row.equipment_machine
		if machine not in machine_summary:
			machine_summary[machine] = {"positive": 0, "negative": 0, "absolute": 0}

		variance = flt(row.variance_hours)
		if variance > 0:
			machine_summary[machine]["positive"] += variance
		elif variance < 0:
			machine_summary[machine]["negative"] += abs(variance)
		machine_summary[machine]["absolute"] += abs(variance)

	top_machines = sorted(
		machine_summary.items(),
		key=lambda item: item[1]["absolute"],
		reverse=True,
	)[:12]

	return {
		"data": {
			"labels": [machine for machine, _values in top_machines],
			"datasets": [
				{
					"name": _("GPS Greater"),
					"values": [flt(values["positive"], 2) for _machine, values in top_machines],
				},
				{
					"name": _("Physical Greater"),
					"values": [flt(values["negative"], 2) for _machine, values in top_machines],
				},
			],
		},
		"type": "bar",
		"barOptions": {"stacked": False},
		"colors": ["#dc2626", "#f59e0b"],
	}
