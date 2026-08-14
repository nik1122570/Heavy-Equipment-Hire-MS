import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class KPITemplate(Document):
	def validate(self):
		self.validate_items()
		self.calculate_total_weight()

	def validate_items(self):
		if not self.items:
			frappe.throw(_("Add at least one KPI item."))

		for row in self.items:
			if flt(row.weight) <= 0:
				frappe.throw(_("Weight must be greater than zero in row {0}.").format(row.idx))
			if flt(row.weight) > 100:
				frappe.throw(_("Weight cannot exceed 100% in row {0}.").format(row.idx))

	def calculate_total_weight(self):
		self.total_weight = sum(flt(row.weight) for row in self.items)
		if flt(self.total_weight, 2) != 100:
			frappe.throw(_("Total KPI weight must be 100%. Current total is {0}%.").format(flt(self.total_weight, 2)))
