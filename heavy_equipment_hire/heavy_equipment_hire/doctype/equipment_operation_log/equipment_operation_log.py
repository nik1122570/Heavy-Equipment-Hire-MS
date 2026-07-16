import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class EquipmentOperationLog(Document):
	def validate(self):
		self.pull_machine_details()
		self.validate_payment_details()
		self.validate_status_details()
		self.validate_day_flags()
		self.validate_duplicate_entry()

	def pull_machine_details(self):
		if not self.equipment_machine:
			return

		machine = frappe.db.get_value(
			"Equipment Machine",
			self.equipment_machine,
			["machine_name", "company", "cost_center"],
			as_dict=True,
		)
		if not machine:
			return

		self.machine_name = machine.machine_name
		if not self.company:
			self.company = machine.company
		if not self.cost_center:
			self.cost_center = machine.cost_center

	def validate_payment_details(self):
		if flt(self.payment_amount) < 0:
			frappe.throw(_("Payment Amount cannot be negative."))

		if flt(self.payment_amount) > 0 and not self.customer:
			frappe.throw(_("Customer is required when Payment Amount is entered."))

	def validate_status_details(self):
		if self.operation_status == "Idle" and not self.idle_reason:
			frappe.throw(_("Idle Reason is required when Operation Status is Idle."))

		if self.operation_status == "Under Maintenance" and not self.maintenance_job_card:
			frappe.msgprint(_("Consider linking the Maintenance Job Card for this maintenance note."), indicator="orange")

	def validate_day_flags(self):
		if self.full_day and self.half_day:
			frappe.throw(_("Select either Full Day or Half Day, not both."))

	def validate_duplicate_entry(self):
		if not (self.operation_date and self.equipment_machine):
			return

		existing = frappe.db.exists(
			"Equipment Operation Log",
			{
				"operation_date": self.operation_date,
				"equipment_machine": self.equipment_machine,
				"docstatus": ["!=", 2],
				"name": ["!=", self.name],
			},
		)
		if existing:
			frappe.throw(
				_("Operation Log already exists for {0} on {1}: {2}").format(
					self.equipment_machine,
					frappe.format(self.operation_date, {"fieldtype": "Date"}),
					existing,
				)
			)
