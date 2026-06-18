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
		self.update_equipment_machine()

	def on_update_after_submit(self):
		self.update_equipment_machine()

	def set_status(self):
		status, _summary = get_insurance_status_details(self.expiry_date)
		self.status = "Draft" if status == "Not Set" else status

	def update_equipment_machine(self):
		if not self.machine:
			return

		status, summary = get_insurance_status_details(self.expiry_date)
		frappe.db.set_value(
			"Equipment Machine",
			self.machine,
			{
				"insurance_policy": self.name,
				"insurance_provider": self.provider,
				"insurance_expiry_date": self.expiry_date,
				"insurance_status": status,
				"insurance_status_summary": summary,
			},
		)


def sync_machine_insurance_from_policies():
	for machine in frappe.get_all("Equipment Machine", pluck="name"):
		policy = frappe.db.get_all(
			"Insurance Policy",
			filters={"machine": machine, "docstatus": ["<", 2]},
			fields=["name", "provider", "expiry_date"],
			order_by="expiry_date desc, modified desc",
			limit=1,
		)
		if not policy:
			continue

		policy = policy[0]
		status, summary = get_insurance_status_details(policy.expiry_date)
		frappe.db.set_value(
			"Equipment Machine",
			machine,
			{
				"insurance_policy": policy.name,
				"insurance_provider": policy.provider,
				"insurance_expiry_date": policy.expiry_date,
				"insurance_status": status,
				"insurance_status_summary": summary,
			},
			update_modified=False,
		)
