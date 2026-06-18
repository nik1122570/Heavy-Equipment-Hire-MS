app_name = "heavy_equipment_hire"
app_title = "Heavy Equipment Hire"
app_publisher = "Nickson John"
app_description = "ERPNext/Frappe app for managing heavy equipment hiring, rental contracts, machine availability, operators, billing, maintenance, and utilization."
app_email = "nickson4422@gmail.com"
app_license = "mit"

# Apps
# ------------------

required_apps = ["erpnext"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "heavy_equipment_hire",
# 		"logo": "/assets/heavy_equipment_hire/logo.png",
# 		"title": "Heavy Equipment Hire",
# 		"route": "/heavy_equipment_hire",
# 		"has_permission": "heavy_equipment_hire.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/heavy_equipment_hire/css/heavy_equipment_hire.css"
# app_include_js = "/assets/heavy_equipment_hire/js/heavy_equipment_hire.js"

# include js, css files in header of web template
# web_include_css = "/assets/heavy_equipment_hire/css/heavy_equipment_hire.css"
# web_include_js = "/assets/heavy_equipment_hire/js/heavy_equipment_hire.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "heavy_equipment_hire/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_js = {
	"Quotation": "public/js/quotation.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "heavy_equipment_hire/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "heavy_equipment_hire.utils.jinja_methods",
# 	"filters": "heavy_equipment_hire.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "heavy_equipment_hire.install.before_install"
# after_install = "heavy_equipment_hire.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "heavy_equipment_hire.uninstall.before_uninstall"
# after_uninstall = "heavy_equipment_hire.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "heavy_equipment_hire.utils.before_app_install"
# after_app_install = "heavy_equipment_hire.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "heavy_equipment_hire.utils.before_app_uninstall"
# after_app_uninstall = "heavy_equipment_hire.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "heavy_equipment_hire.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Sales Order": {
		"validate": "heavy_equipment_hire.overrides.sales_order.validate_sales_order",
		"before_submit": "heavy_equipment_hire.overrides.sales_order.before_submit_sales_order",
		"on_submit": "heavy_equipment_hire.overrides.sales_order.on_submit_sales_order",
		"on_cancel": "heavy_equipment_hire.overrides.sales_order.on_cancel_sales_order",
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"heavy_equipment_hire.tasks.update_insurance_statuses",
		"heavy_equipment_hire.tasks.update_machine_statuses",
	],
}

after_migrate = "heavy_equipment_hire.custom_fields.create_hire_custom_fields"

# Testing
# -------

# before_tests = "heavy_equipment_hire.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"erpnext.selling.doctype.quotation.quotation.make_sales_order": "heavy_equipment_hire.overrides.sales_order.make_sales_order",
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "heavy_equipment_hire.task.get_dashboard_data"
# }
override_doctype_dashboards = {
	"Equipment Maintenance Job Card": "heavy_equipment_hire.heavy_equipment_hire.doctype.equipment_maintenance_job_card.equipment_maintenance_job_card_dashboard.get_data",
	"Hire Commercial Adjustment": "heavy_equipment_hire.heavy_equipment_hire.doctype.hire_commercial_adjustment.hire_commercial_adjustment_dashboard.get_data",
	"Hire Quotation Simulation": "heavy_equipment_hire.heavy_equipment_hire.doctype.hire_quotation_simulation.hire_quotation_simulation_dashboard.get_data",
	"Purchase Invoice": "heavy_equipment_hire.overrides.purchase_invoice_dashboard.get_data",
	"Purchase Order": "heavy_equipment_hire.overrides.purchase_order_dashboard.get_data",
	"Quotation": "heavy_equipment_hire.overrides.quotation_dashboard.get_data",
	"Sales Invoice": "heavy_equipment_hire.overrides.sales_invoice_dashboard.get_data",
	"Sales Order": "heavy_equipment_hire.overrides.sales_order_dashboard.get_data",
}

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["heavy_equipment_hire.utils.before_request"]
# after_request = ["heavy_equipment_hire.utils.after_request"]

# Job Events
# ----------
# before_job = ["heavy_equipment_hire.utils.before_job"]
# after_job = ["heavy_equipment_hire.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"heavy_equipment_hire.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
