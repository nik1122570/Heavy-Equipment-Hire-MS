import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class FleetTracker(Document):
	def validate(self):
		self.pull_machine_details()
		self.validate_hours()
		self.calculate_variance()
		self.validate_reason()
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

	def validate_hours(self):
		if flt(self.gps_hours) < 0:
			frappe.throw(_("GPS Hours cannot be negative."))
		if flt(self.physical_hours) < 0:
			frappe.throw(_("Physical Hours cannot be negative."))
		if flt(self.mileage) < 0:
			frappe.throw(_("Mileage cannot be negative."))

	def calculate_variance(self):
		self.variance_hours = flt(self.gps_hours) - flt(self.physical_hours)

		if self.variance_hours > 0:
			self.variance_direction = "GPS Greater"
		elif self.variance_hours < 0:
			self.variance_direction = "Physical Greater"
		else:
			self.variance_direction = "No Variance"

	def validate_reason(self):
		if flt(self.variance_hours) > 0 and not self.reason:
			frappe.throw(_("Reason is required when GPS Hours are greater than Physical Hours."))

	def validate_duplicate_entry(self):
		if not (self.tracking_date and self.equipment_machine):
			return

		existing = frappe.db.exists(
			"Fleet Tracker",
			{
				"tracking_date": self.tracking_date,
				"equipment_machine": self.equipment_machine,
				"docstatus": ["!=", 2],
				"name": ["!=", self.name],
			},
		)
		if existing:
			frappe.throw(
				_("Fleet Tracker entry already exists for {0} on {1}: {2}").format(
					self.equipment_machine,
					frappe.format(self.tracking_date, {"fieldtype": "Date"}),
					existing,
				)
			)
