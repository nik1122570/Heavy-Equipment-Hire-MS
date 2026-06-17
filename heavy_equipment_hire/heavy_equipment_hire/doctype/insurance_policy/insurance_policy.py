import frappe
from frappe.model.document import Document
from frappe.utils import getdate

from heavy_equipment_hire.heavy_equipment_hire.doctype.equipment_machine.equipment_machine import get_insurance_status_details


class InsurancePolicy(Document):
	def validate(self):
		if self.expiry_date and self.start_date and getdate(self.expiry_date) < getdate(self.start_date):
			frappe.throw("Expiry Date cannot be before Start Date.")
		self.set_status()

	def on_submit(self):
		if self.machine:
			_status, summary = get_insurance_status_details(self.expiry_date)
			frappe.db.set_value(
				"Equipment Machine",
				self.machine,
				{
					"insurance_policy": self.name,
					"insurance_expiry_date": self.expiry_date,
					"insurance_status": self.status,
					"insurance_status_summary": summary,
				},
			)

	def set_status(self):
		status, _summary = get_insurance_status_details(self.expiry_date)
		self.status = "Draft" if status == "Not Set" else status
