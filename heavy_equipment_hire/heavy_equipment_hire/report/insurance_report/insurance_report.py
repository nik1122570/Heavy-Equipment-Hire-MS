import frappe


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": "Machine", "fieldname": "machine", "fieldtype": "Link", "options": "Equipment Machine", "width": 180},
		{"label": "Machine Name", "fieldname": "machine_name", "fieldtype": "Data", "width": 180},
		{"label": "Policy", "fieldname": "policy", "fieldtype": "Link", "options": "Insurance Policy", "width": 180},
		{"label": "Provider", "fieldname": "provider", "fieldtype": "Data", "width": 160},
		{"label": "Start Date", "fieldname": "start_date", "fieldtype": "Date", "width": 110},
		{"label": "Expiry Date", "fieldname": "expiry_date", "fieldtype": "Date", "width": 110},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": "Insured Value", "fieldname": "insured_value", "fieldtype": "Currency", "width": 140},
		{"label": "Premium Amount", "fieldname": "premium_amount", "fieldtype": "Currency", "width": 140},
	]


def get_data(filters):
	conditions = []
	params = {}
	if filters.get("status"):
		conditions.append("coalesce(ip.status, em.insurance_status) = %(status)s")
		params["status"] = filters.status
	where = "where " + " and ".join(conditions) if conditions else ""

	return frappe.db.sql(
		f"""
		select
			em.name as machine,
			em.machine_name,
			ip.name as policy,
			ip.provider,
			ip.start_date,
			coalesce(ip.expiry_date, em.insurance_expiry_date) as expiry_date,
			coalesce(ip.status, em.insurance_status) as status,
			ip.insured_value,
			ip.premium_amount
		from `tabEquipment Machine` em
		left join `tabInsurance Policy` ip on ip.name = em.insurance_policy
		{where}
		order by expiry_date asc, em.machine_name
		""",
		params,
		as_dict=True,
	)

