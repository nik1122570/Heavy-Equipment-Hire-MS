import frappe
from frappe import _
from frappe.utils import add_days, get_link_to_form, getdate, today

from heavy_equipment_hire.equipment_status import update_machine_hire_status
from heavy_equipment_hire.heavy_equipment_hire.doctype.equipment_machine.equipment_machine import get_insurance_status_details


@frappe.whitelist()
def make_sales_order(source_name, target_doc=None, args=None):
	from erpnext.selling.doctype.quotation.quotation import make_sales_order as erpnext_make_sales_order

	sales_order = erpnext_make_sales_order(source_name, target_doc=target_doc, args=args)
	apply_hire_details_from_quotation(source_name, sales_order)
	return sales_order


def apply_hire_details_from_quotation(source_name, sales_order):
	quotation = frappe.get_doc("Quotation", source_name)
	simulation_name = quotation.get("custom_hire_quotation_simulation")
	if not simulation_name:
		return

	simulation = frappe.get_doc("Hire Quotation Simulation", simulation_name)
	apply_hire_details_from_simulation(sales_order, simulation)
	apply_cost_center_from_quotation(sales_order, quotation)


def validate_sales_order(doc, method=None):
	hydrate_hire_details(doc)
	validate_hire_dates(doc)


def before_submit_sales_order(doc, method=None):
	hydrate_hire_details(doc)
	validate_hire_dates(doc)
	validate_machine_insurance(doc)
	validate_machine_availability(doc)


def on_submit_sales_order(doc, method=None):
	update_machine_hire_status(doc.get("custom_equipment_machine"))


def on_cancel_sales_order(doc, method=None):
	machine = doc.get("custom_equipment_machine")
	if not machine:
		return

	update_machine_hire_status(machine)


def hydrate_hire_details(doc):
	simulation_name = doc.get("custom_hire_quotation_simulation")
	if simulation_name:
		simulation = frappe.get_doc("Hire Quotation Simulation", simulation_name)
		apply_hire_details_from_simulation(doc, simulation)
	elif doc.get("custom_equipment_machine"):
		doc.custom_equipment_details = get_equipment_details(doc.custom_equipment_machine)


def apply_hire_details_from_simulation(doc, simulation):
	cost_center = simulation.cost_center or get_machine_cost_center(simulation.machine)
	doc.custom_hire_quotation_simulation = simulation.name
	doc.custom_equipment_machine = simulation.machine
	doc.custom_machine_cost_center = cost_center
	doc.custom_hire_from_date = simulation.from_date
	doc.custom_hire_to_date = simulation.to_date
	doc.custom_equipment_details = get_equipment_details(simulation.machine)

	if doc.meta.has_field("project") and simulation.project:
		doc.project = simulation.project

	for row in doc.get("items", []):
		if row.meta.has_field("cost_center") and cost_center:
			row.cost_center = cost_center
		if row.meta.has_field("project") and simulation.project:
			row.project = simulation.project


def apply_cost_center_from_quotation(doc, quotation):
	cost_center = doc.get("custom_machine_cost_center") or get_first_item_cost_center(quotation)
	if not cost_center:
		return

	doc.custom_machine_cost_center = cost_center
	for row in doc.get("items", []):
		if row.meta.has_field("cost_center"):
			row.cost_center = cost_center


def get_first_item_cost_center(doc):
	for row in doc.get("items", []):
		if row.get("cost_center"):
			return row.cost_center
	return None


def get_machine_cost_center(machine_name):
	if not machine_name:
		return None
	return frappe.db.get_value("Equipment Machine", machine_name, "cost_center")


def get_equipment_details(machine_name):
	if not machine_name:
		return ""

	machine = frappe.get_cached_doc("Equipment Machine", machine_name)
	details = [
		machine.get("machine_name"),
		machine.get("registration_no"),
		machine.get("machine_description"),
	]
	return "\n".join(detail for detail in details if detail)


def validate_hire_dates(doc):
	if not doc.get("custom_equipment_machine"):
		return

	if not doc.get("custom_hire_from_date") or not doc.get("custom_hire_to_date"):
		frappe.throw(_("Hire From Date and Hire To Date are required for equipment hire Sales Orders."))

	if getdate(doc.custom_hire_to_date) < getdate(doc.custom_hire_from_date):
		frappe.throw(_("Hire To Date cannot be before Hire From Date."))


def validate_machine_availability(doc):
	machine = doc.get("custom_equipment_machine")
	if not machine:
		return

	overlap = frappe.db.sql(
		"""
		select name
		from `tabSales Order`
		where docstatus = 1
			and custom_equipment_machine = %(machine)s
			and name != %(name)s
			and custom_hire_from_date <= %(to_date)s
			and custom_hire_to_date >= %(from_date)s
		limit 1
		""",
		{
			"machine": machine,
			"name": doc.name,
			"from_date": doc.custom_hire_from_date,
			"to_date": doc.custom_hire_to_date,
		},
		as_dict=True,
	)
	if overlap:
		frappe.throw(
			_("Machine {0} is already booked in Sales Order {1} for an overlapping period.").format(
				get_link_to_form("Equipment Machine", machine),
				get_link_to_form("Sales Order", overlap[0].name),
			)
		)


def validate_machine_insurance(doc):
	machine = doc.get("custom_equipment_machine")
	if not machine:
		return

	insurance = get_machine_insurance(machine)
	status = insurance.get("status")

	if status == "Expired":
		frappe.throw(
			_("Cannot submit this Sales Order because {0} has expired insurance.").format(
				get_link_to_form("Equipment Machine", machine)
			)
		)

	if status == "Expiring Soon":
		frappe.msgprint(
			_("{0} insurance is expiring soon on {1}. You can continue, but please renew/follow up.").format(
				get_link_to_form("Equipment Machine", machine),
				frappe.format(insurance.get("expiry_date"), {"fieldtype": "Date"}),
			),
			title=_("Insurance Expiring Soon"),
			indicator="orange",
		)


def get_machine_insurance(machine):
	expiry_date = frappe.db.get_value("Equipment Machine", machine, "insurance_expiry_date")
	status, summary = get_insurance_status_details(expiry_date)

	if status:
		frappe.db.set_value(
			"Equipment Machine",
			machine,
			{"insurance_status": status, "insurance_status_summary": summary},
			update_modified=False,
		)

	return {"expiry_date": expiry_date, "status": status}


def get_insurance_status(expiry_date):
	status, _summary = get_insurance_status_details(expiry_date)
	return status
