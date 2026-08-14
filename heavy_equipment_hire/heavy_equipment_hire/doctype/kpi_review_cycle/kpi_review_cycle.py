import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class KPIReviewCycle(Document):
	def validate(self):
		if self.to_date and self.from_date and getdate(self.to_date) < getdate(self.from_date):
			frappe.throw(_("To Date cannot be before From Date."))
