import frappe
from frappe.model.document import Document

from heavy_equipment_hire.compliance import (
	CRITICAL_MACHINE_COMPLIANCE_TYPES,
	get_compliance_status_details,
)


class ComplianceCertificate(Document):
	def validate(self):
		self.set_machine_details()
		self.set_defaults()
		self.set_status()

	def set_machine_details(self):
		if not self.equipment_machine:
			return

		machine = frappe.db.get_value(
			"Equipment Machine",
			self.equipment_machine,
			["registration_no", "cost_center", "company"],
			as_dict=True,
		)
		if machine:
			self.registration_no = machine.registration_no
			self.cost_center = machine.cost_center
			self.company = machine.company

	def set_defaults(self):
		if self.compliance_type in CRITICAL_MACHINE_COMPLIANCE_TYPES:
			self.is_critical = 1

	def set_status(self):
		status, summary, days_remaining = get_compliance_status_details(self.expiry_date)
		self.status = status
		self.status_summary = summary
		self.days_remaining = days_remaining
