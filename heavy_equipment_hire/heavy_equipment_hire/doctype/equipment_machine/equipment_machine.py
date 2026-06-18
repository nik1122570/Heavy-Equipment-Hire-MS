import frappe
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, getdate, today


class EquipmentMachine(Document):
	def validate(self):
		self.validate_default_rates()
		self.validate_cost_center()
		self.set_insurance_details_from_policy()
		self.set_insurance_status()

	def validate_default_rates(self):
		if self.default_billing_method == "Block Hours":
			if not self.default_block_size_hours:
				frappe.throw("Default Block Size Hours is required for Block Hours billing.")
			if not self.default_block_rate:
				frappe.throw("Default Block Rate is required for Block Hours billing.")

	def validate_cost_center(self):
		if not self.cost_center:
			frappe.throw("Machine Cost Center is required because every machine must report cost and revenue separately.")

	def set_insurance_status(self):
		status, summary = get_insurance_status_details(self.insurance_expiry_date)
		self.insurance_status = status
		self.insurance_status_summary = summary

	def set_insurance_details_from_policy(self):
		if not self.insurance_policy:
			return

		policy = frappe.db.get_value(
			"Insurance Policy",
			self.insurance_policy,
			["machine", "provider", "expiry_date"],
			as_dict=True,
		)
		if not policy:
			frappe.throw("Selected Insurance Policy was not found.")

		machine_name = self.name if not self.is_new() else self.registration_no
		if policy.machine and machine_name and policy.machine != machine_name:
			frappe.throw("Selected Insurance Policy belongs to machine {0}.".format(policy.machine))

		self.insurance_provider = policy.provider
		self.insurance_expiry_date = policy.expiry_date


def get_insurance_status_details(expiry_date):
	if not expiry_date:
		return "Not Set", "Not Set"

	expiry = getdate(expiry_date)
	current_date = getdate(today())
	days_remaining = date_diff(expiry, current_date)

	if expiry < current_date:
		return "Expired", "Expired"
	if expiry <= getdate(add_days(current_date, 30)):
		day_label = "day" if days_remaining == 1 else "days"
		return "Expiring Soon", f"Expiring Soon - {days_remaining} {day_label} remaining"
	return "Active", "Active"
