import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, today

from heavy_equipment_hire.equipment_status import update_machine_hire_status


class EquipmentMaintenanceJobCard(Document):
	def validate(self):
		self.pull_machine_details()
		self.validate_dates()
		self.calculate_total()

	def on_submit(self):
		self.set_machine_under_maintenance()

	def on_update_after_submit(self):
		if self.status == "Completed":
			if not self.completed_date:
				self.db_set("completed_date", today(), update_modified=False)
			update_machine_hire_status(self.equipment_machine, force=True)
		elif self.status == "Open":
			self.set_machine_under_maintenance()

	def on_cancel(self):
		update_machine_hire_status(self.equipment_machine, force=True)

	def pull_machine_details(self):
		if not self.equipment_machine:
			return

		machine = frappe.get_cached_doc("Equipment Machine", self.equipment_machine)
		self.company = machine.company
		self.cost_center = machine.cost_center
		self.machine_name = machine.machine_name

	def validate_dates(self):
		if (
			self.expected_completion_date
			and self.reported_date
			and getdate(self.expected_completion_date) < getdate(self.reported_date)
		):
			frappe.throw(_("Expected Completion Date cannot be before Reported Date."))

		if self.completed_date and self.reported_date and getdate(self.completed_date) < getdate(self.reported_date):
			frappe.throw(_("Completed Date cannot be before Reported Date."))

	def calculate_total(self):
		for row in self.get("items", []):
			row.amount = flt(row.qty) * flt(row.rate)
		self.total_maintenance_cost = sum(flt(row.amount) for row in self.get("items", []))

	def set_machine_under_maintenance(self):
		if self.status != "Open" or not self.equipment_machine:
			return
		frappe.db.set_value(
			"Equipment Machine",
			self.equipment_machine,
			"status",
			"Under Maintenance",
			update_modified=False,
		)


@frappe.whitelist()
def make_purchase_order(source_name):
	job_card = frappe.get_doc("Equipment Maintenance Job Card", source_name)
	if job_card.docstatus != 1:
		frappe.throw(_("Submit the Equipment Maintenance Job Card before creating a Purchase Order."))
	if job_card.status != "Open":
		frappe.throw(_("Purchase Order can only be created while the Job Card is Open."))
	if job_card.purchase_order:
		return frappe.get_doc("Purchase Order", job_card.purchase_order)
	if not job_card.supplier:
		frappe.throw(_("Supplier is required to create a Purchase Order."))
	if not job_card.get("items"):
		frappe.throw(_("Add at least one charge or spare part before creating a Purchase Order."))

	purchase_order = frappe.new_doc("Purchase Order")
	purchase_order.company = job_card.company
	purchase_order.supplier = job_card.supplier
	purchase_order.transaction_date = today()
	purchase_order.schedule_date = job_card.expected_completion_date or today()
	if purchase_order.meta.has_field("cost_center"):
		purchase_order.cost_center = job_card.cost_center
	if purchase_order.meta.has_field("custom_equipment_maintenance_job_card"):
		purchase_order.custom_equipment_maintenance_job_card = job_card.name
	if purchase_order.meta.has_field("custom_equipment_machine"):
		purchase_order.custom_equipment_machine = job_card.equipment_machine
	if purchase_order.meta.has_field("custom_machine_cost_center"):
		purchase_order.custom_machine_cost_center = job_card.cost_center
	purchase_order.remarks = _("Maintenance Purchase Order from Job Card {0}").format(job_card.name)

	for row in job_card.get("items", []):
		add_purchase_order_item(purchase_order, job_card, row)

	purchase_order.insert()
	frappe.db.set_value(
		"Equipment Maintenance Job Card",
		job_card.name,
		"purchase_order",
		purchase_order.name,
		update_modified=False,
	)
	return purchase_order


def add_purchase_order_item(purchase_order, job_card, row):
	amount = flt(row.amount) or flt(row.qty) * flt(row.rate)
	if not amount:
		return

	item_name = frappe.db.get_value("Item", row.item_code, "item_name") or row.item_code
	item = purchase_order.append("items", {})
	item.item_code = row.item_code
	item.qty = flt(row.qty) or 1
	item.rate = flt(row.rate) or amount
	item.amount = amount
	item.schedule_date = job_card.expected_completion_date or today()
	item.description = row.remarks or _("{0} - Maintenance for {1}").format(
		item_name, job_card.equipment_machine
	)
	if item.meta.has_field("cost_center"):
		item.cost_center = job_card.cost_center
