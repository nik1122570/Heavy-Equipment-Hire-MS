from frappe.model.document import Document

from heavy_equipment_hire.compliance import get_compliance_status_details


class DriverCompliance(Document):
	def validate(self):
		self.set_status()

	def set_status(self):
		status, summary, days_remaining = get_compliance_status_details(self.expiry_date)
		self.status = status
		self.status_summary = summary
		self.days_remaining = days_remaining
