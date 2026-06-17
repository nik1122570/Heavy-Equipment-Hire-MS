import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, today


class HireQuotationSimulation(Document):
	def validate(self):
		self.pull_machine_defaults()
		self.validate_dates()
		self.calculate_totals()

	def on_submit(self):
		if self.expected_profit < 0:
			frappe.throw(_("Simulation cannot be submitted while expected profit is negative."))

	def pull_machine_defaults(self):
		if not self.machine:
			return

		machine = frappe.get_cached_doc("Equipment Machine", self.machine)
		if not self.cost_center and machine.get("cost_center"):
			self.cost_center = machine.cost_center

	def validate_dates(self):
		if self.to_date and self.from_date and getdate(self.to_date) < getdate(self.from_date):
			frappe.throw(_("To Date cannot be before From Date."))

	def calculate_totals(self):
		for row in self.get("charges", []):
			row.amount = flt(row.qty) * flt(row.rate)

		for row in self.get("additional_costs", []):
			row.amount = flt(row.qty) * flt(row.rate)

		self.total_expected_revenue = sum(flt(row.amount) for row in self.get("charges", []))
		self.total_expected_cost = sum(flt(row.amount) for row in self.get("additional_costs", []))
		self.expected_profit = flt(self.total_expected_revenue) - flt(self.total_expected_cost)
		self.profit_margin_percentage = (
			flt(self.expected_profit) / flt(self.total_expected_revenue) * 100
			if flt(self.total_expected_revenue)
			else 0
		)


@frappe.whitelist()
def make_quotation(source_name):
	simulation = frappe.get_doc("Hire Quotation Simulation", source_name)
	if simulation.docstatus != 1:
		frappe.throw(_("Submit the Hire Quotation Simulation before creating a Quotation."))
	if not simulation.get("charges"):
		frappe.throw(_("Add at least one revenue charge before creating a Quotation."))

	quotation = frappe.new_doc("Quotation")
	quotation.quotation_to = "Customer"
	quotation.party_name = simulation.customer
	quotation.customer_name = simulation.customer
	quotation.transaction_date = today()
	quotation.valid_till = simulation.to_date
	quotation.company = simulation.company
	if quotation.meta.has_field("cost_center"):
		quotation.cost_center = simulation.cost_center
	if quotation.meta.has_field("project"):
		quotation.project = simulation.project
	quotation.custom_hire_quotation_simulation = simulation.name
	quotation.custom_equipment_machine = simulation.machine

	for row in simulation.get("charges", []):
		add_quotation_item(quotation, simulation, row)

	if not quotation.items:
		frappe.throw(_("At least one customer-facing revenue amount is required."))

	quotation.insert()
	frappe.db.set_value("Hire Quotation Simulation", simulation.name, "quotation", quotation.name)
	return quotation


def add_quotation_item(quotation, simulation, row):
	amount = flt(row.amount) or (flt(row.qty) * flt(row.rate))
	if not amount:
		return

	item_code = row.revenue_charge
	if not item_code:
		frappe.throw(_("Revenue Charge is required in row {0}.").format(row.idx))

	item = quotation.append("items", {})
	item.item_code = item_code
	item.qty = flt(row.qty) or 1
	item.rate = flt(row.rate) or amount
	item.description = f"{frappe.db.get_value('Item', item_code, 'item_name') or item_code} - {simulation.machine}"
	if item.meta.has_field("cost_center"):
		item.cost_center = simulation.cost_center
	if item.meta.has_field("project"):
		item.project = simulation.project


@frappe.whitelist()
def make_purchase_invoice(source_name, supplier, cost_rows=None):
	simulation = frappe.get_doc("Hire Quotation Simulation", source_name)
	if simulation.docstatus != 1:
		frappe.throw(_("Submit the Hire Quotation Simulation before paying expenses."))
	if not supplier:
		frappe.throw(_("Supplier is required to create a Purchase Invoice."))

	selected_rows = get_selected_cost_rows(simulation, cost_rows)
	if not selected_rows:
		frappe.throw(_("Select at least one unpaid expense."))

	purchase_invoice = frappe.new_doc("Purchase Invoice")
	purchase_invoice.company = simulation.company
	purchase_invoice.supplier = supplier
	purchase_invoice.posting_date = today()
	purchase_invoice.set_posting_time = 1
	cost_center = get_simulation_cost_center(simulation)
	if purchase_invoice.meta.has_field("project"):
		purchase_invoice.project = simulation.project
	if purchase_invoice.meta.has_field("cost_center"):
		purchase_invoice.cost_center = cost_center
	if purchase_invoice.meta.has_field("custom_machine_cost_center"):
		purchase_invoice.custom_machine_cost_center = cost_center
	if purchase_invoice.meta.has_field("custom_hire_quotation_simulation"):
		purchase_invoice.custom_hire_quotation_simulation = simulation.name
	purchase_invoice.remarks = _("Expenses from Hire Quotation Simulation {0}").format(simulation.name)

	for row in selected_rows:
		add_purchase_invoice_item(purchase_invoice, simulation, row)

	if not purchase_invoice.items:
		frappe.throw(_("No valid expense items found for Purchase Invoice."))

	purchase_invoice.insert()
	for row in selected_rows:
		frappe.db.set_value(row.doctype, row.name, "purchase_invoice", purchase_invoice.name, update_modified=False)

	return purchase_invoice


def get_selected_cost_rows(simulation, cost_rows):
	if isinstance(cost_rows, str):
		cost_rows = frappe.parse_json(cost_rows)
	cost_rows = set(cost_rows or [])

	rows = []
	for row in simulation.get("additional_costs", []):
		if cost_rows and row.name not in cost_rows:
			continue
		if row.purchase_invoice:
			continue
		if not row.cost_type:
			frappe.throw(_("Cost Type is required in additional cost row {0}.").format(row.idx))
		if not (flt(row.amount) or flt(row.qty) * flt(row.rate)):
			continue
		rows.append(row)

	return rows


def add_purchase_invoice_item(purchase_invoice, simulation, row):
	item_code = row.cost_type
	item_name = frappe.db.get_value("Item", item_code, "item_name") or item_code
	amount = flt(row.amount) or (flt(row.qty) * flt(row.rate))

	item = purchase_invoice.append("items", {})
	item.item_code = item_code
	item.qty = flt(row.qty) or 1
	item.rate = flt(row.rate) or amount
	item.amount = amount
	item.description = _("{0} - {1}").format(item_name, simulation.machine)
	if item.meta.has_field("cost_center"):
		item.cost_center = get_simulation_cost_center(simulation)
	if item.meta.has_field("project"):
		item.project = simulation.project


@frappe.whitelist()
def make_commercial_adjustment(source_name):
	simulation = frappe.get_doc("Hire Quotation Simulation", source_name)
	if simulation.docstatus != 1:
		frappe.throw(_("Submit the Hire Quotation Simulation before creating a Commercial Adjustment."))

	adjustment = frappe.new_doc("Hire Commercial Adjustment")
	adjustment.hire_quotation_simulation = simulation.name
	adjustment.adjustment_date = today()
	adjustment.company = simulation.company
	adjustment.customer = simulation.customer
	adjustment.project = simulation.project
	adjustment.machine = simulation.machine
	adjustment.cost_center = get_simulation_cost_center(simulation)
	adjustment.original_expected_revenue = simulation.total_expected_revenue
	adjustment.original_expected_cost = simulation.total_expected_cost
	adjustment.original_expected_profit = simulation.expected_profit
	adjustment.original_margin_percentage = simulation.profit_margin_percentage
	adjustment.revised_revenue = simulation.total_expected_revenue
	adjustment.revised_cost = simulation.total_expected_cost
	adjustment.revised_profit = simulation.expected_profit
	adjustment.revised_margin_percentage = simulation.profit_margin_percentage
	adjustment.sales_order = frappe.db.get_value(
		"Sales Order",
		{
			"custom_hire_quotation_simulation": simulation.name,
			"docstatus": ["!=", 2],
		},
		"name",
		order_by="creation desc",
	)
	adjustment.insert()
	return adjustment


def get_simulation_cost_center(simulation):
	return simulation.cost_center or frappe.db.get_value("Equipment Machine", simulation.machine, "cost_center")
