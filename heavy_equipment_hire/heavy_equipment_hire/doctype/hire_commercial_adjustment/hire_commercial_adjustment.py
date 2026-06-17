import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today


class HireCommercialAdjustment(Document):
	def validate(self):
		self.pull_source_details()
		self.calculate_totals()

	def pull_source_details(self):
		if not self.hire_quotation_simulation:
			return

		simulation = frappe.get_cached_doc("Hire Quotation Simulation", self.hire_quotation_simulation)
		self.company = simulation.company
		self.customer = simulation.customer
		self.project = simulation.project
		self.machine = simulation.machine
		self.cost_center = simulation.cost_center or frappe.db.get_value(
			"Equipment Machine", simulation.machine, "cost_center"
		)
		self.original_expected_revenue = simulation.total_expected_revenue
		self.original_expected_cost = simulation.total_expected_cost
		self.original_expected_profit = simulation.expected_profit
		self.original_margin_percentage = simulation.profit_margin_percentage

		if not self.sales_order:
			self.sales_order = frappe.db.get_value(
				"Sales Order",
				{
					"custom_hire_quotation_simulation": self.hire_quotation_simulation,
					"docstatus": ["!=", 2],
				},
				"name",
				order_by="creation desc",
			)

	def calculate_totals(self):
		for row in self.get("additional_costs", []):
			row.amount = flt(row.qty) * flt(row.rate)

		for row in self.get("back_charges", []):
			row.amount = flt(row.qty) * flt(row.rate)

		self.additional_cost = sum(flt(row.amount) for row in self.get("additional_costs", []))
		self.additional_revenue = sum(flt(row.amount) for row in self.get("back_charges", []))
		self.net_adjustment = flt(self.additional_revenue) - flt(self.additional_cost)
		self.revised_revenue = flt(self.original_expected_revenue) + flt(self.additional_revenue)
		self.revised_cost = flt(self.original_expected_cost) + flt(self.additional_cost)
		self.revised_profit = flt(self.revised_revenue) - flt(self.revised_cost)
		self.revised_margin_percentage = (
			flt(self.revised_profit) / flt(self.revised_revenue) * 100
			if flt(self.revised_revenue)
			else 0
		)


@frappe.whitelist()
def make_purchase_invoice(source_name, supplier, cost_rows=None):
	adjustment = frappe.get_doc("Hire Commercial Adjustment", source_name)
	if adjustment.docstatus != 1:
		frappe.throw(_("Submit the Hire Commercial Adjustment before paying extra costs."))
	if not supplier:
		frappe.throw(_("Supplier is required to create a Purchase Invoice."))

	selected_rows = get_selected_rows(adjustment, "additional_costs", "purchase_invoice", "cost_type", cost_rows)
	if not selected_rows:
		frappe.throw(_("Select at least one unpaid extra cost."))

	purchase_invoice = frappe.new_doc("Purchase Invoice")
	purchase_invoice.company = adjustment.company
	purchase_invoice.supplier = supplier
	purchase_invoice.posting_date = today()
	purchase_invoice.set_posting_time = 1
	cost_center = get_adjustment_cost_center(adjustment)
	if purchase_invoice.meta.has_field("project"):
		purchase_invoice.project = adjustment.project
	if purchase_invoice.meta.has_field("cost_center"):
		purchase_invoice.cost_center = cost_center
	if purchase_invoice.meta.has_field("custom_machine_cost_center"):
		purchase_invoice.custom_machine_cost_center = cost_center
	if purchase_invoice.meta.has_field("custom_hire_quotation_simulation"):
		purchase_invoice.custom_hire_quotation_simulation = adjustment.hire_quotation_simulation
	if purchase_invoice.meta.has_field("custom_hire_commercial_adjustment"):
		purchase_invoice.custom_hire_commercial_adjustment = adjustment.name
	purchase_invoice.remarks = _("Extra site costs from Hire Commercial Adjustment {0}").format(adjustment.name)

	for row in selected_rows:
		add_purchase_invoice_item(purchase_invoice, adjustment, row)

	purchase_invoice.insert()
	for row in selected_rows:
		frappe.db.set_value(row.doctype, row.name, "purchase_invoice", purchase_invoice.name, update_modified=False)

	return purchase_invoice


@frappe.whitelist()
def make_sales_invoice(source_name, charge_rows=None):
	adjustment = frappe.get_doc("Hire Commercial Adjustment", source_name)
	if adjustment.docstatus != 1:
		frappe.throw(_("Submit the Hire Commercial Adjustment before billing back charges."))
	if not adjustment.customer:
		frappe.throw(_("Customer is required to create a Sales Invoice."))

	selected_rows = get_selected_rows(adjustment, "back_charges", "sales_invoice", "revenue_charge", charge_rows)
	if not selected_rows:
		frappe.throw(_("Select at least one unbilled back charge."))

	sales_invoice = frappe.new_doc("Sales Invoice")
	sales_invoice.company = adjustment.company
	sales_invoice.customer = adjustment.customer
	sales_invoice.posting_date = today()
	sales_invoice.set_posting_time = 1
	cost_center = get_adjustment_cost_center(adjustment)
	if sales_invoice.meta.has_field("project"):
		sales_invoice.project = adjustment.project
	if sales_invoice.meta.has_field("cost_center"):
		sales_invoice.cost_center = cost_center
	if sales_invoice.meta.has_field("custom_machine_cost_center"):
		sales_invoice.custom_machine_cost_center = cost_center
	if sales_invoice.meta.has_field("custom_hire_quotation_simulation"):
		sales_invoice.custom_hire_quotation_simulation = adjustment.hire_quotation_simulation
	if sales_invoice.meta.has_field("custom_hire_commercial_adjustment"):
		sales_invoice.custom_hire_commercial_adjustment = adjustment.name
	sales_invoice.remarks = _("Back charges from Hire Commercial Adjustment {0}").format(adjustment.name)

	for row in selected_rows:
		add_sales_invoice_item(sales_invoice, adjustment, row)

	sales_invoice.insert()
	for row in selected_rows:
		frappe.db.set_value(row.doctype, row.name, "sales_invoice", sales_invoice.name, update_modified=False)

	return sales_invoice


def get_selected_rows(adjustment, table_fieldname, invoice_fieldname, item_fieldname, selected_names):
	if isinstance(selected_names, str):
		selected_names = frappe.parse_json(selected_names)
	selected_names = set(selected_names or [])

	rows = []
	for row in adjustment.get(table_fieldname, []):
		if selected_names and row.name not in selected_names:
			continue
		if row.get(invoice_fieldname):
			continue
		if not row.get(item_fieldname):
			frappe.throw(_("Item is required in row {0}.").format(row.idx))
		if not (flt(row.amount) or flt(row.qty) * flt(row.rate)):
			continue
		rows.append(row)

	return rows


def add_purchase_invoice_item(purchase_invoice, adjustment, row):
	item_code = row.cost_type
	item = purchase_invoice.append("items", {})
	set_invoice_item_values(item, item_code, adjustment, row)


def add_sales_invoice_item(sales_invoice, adjustment, row):
	item_code = row.revenue_charge
	item = sales_invoice.append("items", {})
	set_invoice_item_values(item, item_code, adjustment, row)
	if adjustment.sales_order and item.meta.has_field("sales_order"):
		item.sales_order = adjustment.sales_order


def set_invoice_item_values(item, item_code, adjustment, row):
	item_name = frappe.db.get_value("Item", item_code, "item_name") or item_code
	amount = flt(row.amount) or (flt(row.qty) * flt(row.rate))
	item.item_code = item_code
	item.qty = flt(row.qty) or 1
	item.rate = flt(row.rate) or amount
	item.amount = amount
	item.description = _("{0} - {1}").format(item_name, adjustment.machine)
	if item.meta.has_field("cost_center"):
		item.cost_center = get_adjustment_cost_center(adjustment)
	if item.meta.has_field("project"):
		item.project = adjustment.project


def get_adjustment_cost_center(adjustment):
	return adjustment.cost_center or frappe.db.get_value("Equipment Machine", adjustment.machine, "cost_center")
