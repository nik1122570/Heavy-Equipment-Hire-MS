import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def create_hire_custom_fields():
	remove_visible_quotation_hire_fields()
	remove_obsolete_sales_order_hire_fields()
	update_stale_report_references()

	custom_fields = {
		"Quotation": [
			{
				"fieldname": "custom_hire_quotation_simulation",
				"fieldtype": "Link",
				"label": "Hire Quotation Simulation",
				"options": "Hire Quotation Simulation",
				"insert_after": "items",
				"read_only": 1,
				"hidden": 1,
			},
			{
				"fieldname": "custom_equipment_machine",
				"fieldtype": "Link",
				"label": "Equipment Machine",
				"options": "Equipment Machine",
				"insert_after": "custom_hire_quotation_simulation",
				"read_only": 1,
				"hidden": 1,
			},
		],
		"Sales Order": [
			{
				"fieldname": "custom_equipment_details",
				"fieldtype": "Small Text",
				"label": "Equipment Details",
				"insert_after": "items",
				"read_only": 1,
			},
			{
				"fieldname": "custom_hire_quotation_simulation",
				"fieldtype": "Link",
				"label": "Hire Quotation Simulation",
				"options": "Hire Quotation Simulation",
				"insert_after": "custom_equipment_details",
				"read_only": 1,
				"hidden": 1,
			},
			{
				"fieldname": "custom_equipment_machine",
				"fieldtype": "Link",
				"label": "Equipment Machine",
				"options": "Equipment Machine",
				"insert_after": "custom_hire_quotation_simulation",
				"read_only": 1,
				"hidden": 1,
			},
			{
				"fieldname": "custom_machine_cost_center",
				"fieldtype": "Link",
				"label": "Machine Cost Center",
				"options": "Cost Center",
				"insert_after": "custom_equipment_machine",
				"read_only": 1,
				"hidden": 1,
			},
			{"fieldname": "custom_hire_from_date", "fieldtype": "Date", "label": "Hire From Date", "insert_after": "custom_machine_cost_center", "read_only": 1, "hidden": 1},
			{"fieldname": "custom_hire_to_date", "fieldtype": "Date", "label": "Hire To Date", "insert_after": "custom_hire_from_date", "read_only": 1, "hidden": 1},
		],
		"Purchase Invoice": [
			{
				"fieldname": "custom_hire_quotation_simulation",
				"fieldtype": "Link",
				"label": "Hire Quotation Simulation",
				"options": "Hire Quotation Simulation",
				"insert_after": "items",
				"read_only": 1,
				"hidden": 1,
			},
			{
				"fieldname": "custom_hire_commercial_adjustment",
				"fieldtype": "Link",
				"label": "Hire Commercial Adjustment",
				"options": "Hire Commercial Adjustment",
				"insert_after": "custom_hire_quotation_simulation",
				"read_only": 1,
				"hidden": 1,
			},
			{
				"fieldname": "custom_machine_cost_center",
				"fieldtype": "Link",
				"label": "Machine Cost Center",
				"options": "Cost Center",
				"insert_after": "custom_hire_commercial_adjustment",
				"read_only": 1,
				"hidden": 1,
			},
		],
		"Sales Invoice": [
			{
				"fieldname": "custom_hire_quotation_simulation",
				"fieldtype": "Link",
				"label": "Hire Quotation Simulation",
				"options": "Hire Quotation Simulation",
				"insert_after": "items",
				"read_only": 1,
				"hidden": 1,
			},
			{
				"fieldname": "custom_hire_commercial_adjustment",
				"fieldtype": "Link",
				"label": "Hire Commercial Adjustment",
				"options": "Hire Commercial Adjustment",
				"insert_after": "custom_hire_quotation_simulation",
				"read_only": 1,
				"hidden": 1,
			},
			{
				"fieldname": "custom_machine_cost_center",
				"fieldtype": "Link",
				"label": "Machine Cost Center",
				"options": "Cost Center",
				"insert_after": "custom_hire_commercial_adjustment",
				"read_only": 1,
				"hidden": 1,
			},
		],
	}
	create_custom_fields(custom_fields, update=True)
	frappe.clear_cache(doctype="Quotation")
	frappe.clear_cache(doctype="Sales Order")
	frappe.clear_cache(doctype="Purchase Invoice")
	frappe.clear_cache(doctype="Sales Invoice")
	update_machine_statuses_after_migrate()


def remove_visible_quotation_hire_fields():
	for fieldname in (
		"hire_details_section",
		"custom_machine_cost_center",
		"custom_hire_from_date",
		"custom_hire_to_date",
		"custom_billing_method",
		"custom_block_size_hours",
		"custom_block_rate",
		"custom_minimum_blocks",
	):
		custom_field = frappe.db.exists("Custom Field", {"dt": "Quotation", "fieldname": fieldname})
		if custom_field:
			frappe.delete_doc("Custom Field", custom_field, ignore_permissions=True, force=True)


def remove_obsolete_sales_order_hire_fields():
	for fieldname in (
		"hire_details_section",
		"custom_hire_order",
		"custom_hire_contract",
		"custom_billing_method",
		"custom_block_size_hours",
		"custom_block_rate",
		"custom_minimum_blocks",
	):
		custom_field = frappe.db.exists("Custom Field", {"dt": "Sales Order", "fieldname": fieldname})
		if custom_field:
			frappe.delete_doc("Custom Field", custom_field, ignore_permissions=True, force=True)


def update_machine_statuses_after_migrate():
	from heavy_equipment_hire.equipment_status import update_all_machine_hire_statuses

	update_all_machine_hire_statuses()


def update_stale_report_references():
	report_refs = {
		"Hire Machine Utilization": "Sales Order",
		"Machine Availability Calendar": "Equipment Machine",
	}
	for report_name, ref_doctype in report_refs.items():
		if frappe.db.exists("Report", report_name):
			frappe.db.set_value("Report", report_name, "ref_doctype", ref_doctype, update_modified=False)
