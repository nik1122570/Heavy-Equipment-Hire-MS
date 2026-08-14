import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class EmployeeKPIReview(Document):
	def validate(self):
		self.validate_cycle()
		self.validate_template()
		self.validate_items()
		self.calculate_scores()
		self.set_final_rating()

	def validate_cycle(self):
		if not self.review_cycle:
			return

		status = frappe.db.get_value("KPI Review Cycle", self.review_cycle, "status")
		if status == "Closed" and self.workflow_status != "HR Closed":
			frappe.throw(_("Selected KPI Review Cycle is closed."))

	def validate_template(self):
		if not self.kpi_template:
			return

		status = frappe.db.get_value("KPI Template", self.kpi_template, "status")
		if status == "Inactive":
			frappe.throw(_("Selected KPI Template is inactive."))

	def validate_items(self):
		if not self.items:
			frappe.throw(_("Load or add KPI review items before saving."))

		for row in self.items:
			self.validate_score(row.employee_score, _("Employee Score"), row.idx)
			self.validate_score(row.manager_score, _("Manager Score"), row.idx)

	def validate_score(self, score, label, row_idx):
		if score in (None, ""):
			return
		if flt(score) < 0 or flt(score) > 100:
			frappe.throw(_("{0} must be between 0 and 100 in row {1}.").format(label, row_idx))

	def calculate_scores(self):
		total_weight = 0
		employee_score = 0
		manager_score = 0
		final_score = 0

		for row in self.items:
			total_weight += flt(row.weight)
			row.employee_weighted_score = flt(row.employee_score) * flt(row.weight) / 100
			row.manager_weighted_score = flt(row.manager_score) * flt(row.weight) / 100

			employee_score += flt(row.employee_weighted_score)
			manager_score += flt(row.manager_weighted_score)

			final_row_score = row.manager_weighted_score if row.manager_score not in (None, "") else row.employee_weighted_score
			row.final_weighted_score = flt(final_row_score)
			final_score += flt(row.final_weighted_score)

		if flt(total_weight, 2) != 100:
			frappe.throw(_("Total KPI weight must be 100%. Current total is {0}%.").format(flt(total_weight, 2)))

		self.total_weight = flt(total_weight, 2)
		self.employee_total_score = flt(employee_score, 2)
		self.manager_total_score = flt(manager_score, 2)
		self.final_score = flt(final_score, 2)

	def set_final_rating(self):
		score = flt(self.final_score)
		if score >= 95:
			self.final_rating = "Outstanding"
		elif score >= 85:
			self.final_rating = "Exceeds Expectations"
		elif score >= 75:
			self.final_rating = "Meets Expectations"
		elif score >= 51:
			self.final_rating = "Needs Improvement"
		else:
			self.final_rating = "Unsatisfactory"


@frappe.whitelist()
def get_template_items(kpi_template):
	if not kpi_template:
		frappe.throw(_("KPI Template is required."))

	template = frappe.get_doc("KPI Template", kpi_template)
	if template.status == "Inactive":
		frappe.throw(_("Selected KPI Template is inactive."))

	return [
		{
			"kpi_area": row.kpi_area,
			"metric": row.metric,
			"target": row.target,
			"weight": row.weight,
		}
		for row in template.items
	]


def get_permission_query_conditions(user):
	if not user:
		user = frappe.session.user

	if user == "Administrator" or "System Manager" in frappe.get_roles(user) or "HR Manager" in frappe.get_roles(user):
		return ""

	escaped_user = frappe.db.escape(user)
	return f"(`tabEmployee KPI Review`.employee_user = {escaped_user} or `tabEmployee KPI Review`.line_manager = {escaped_user})"


def has_permission(doc, user=None, permission_type=None):
	if not user:
		user = frappe.session.user

	if user == "Administrator" or "System Manager" in frappe.get_roles(user) or "HR Manager" in frappe.get_roles(user):
		return True

	return doc.employee_user == user or doc.line_manager == user
