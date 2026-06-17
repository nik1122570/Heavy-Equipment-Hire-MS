frappe.query_reports["Revised Hire Profitability"] = {
	filters: [
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "machine",
			label: __("Equipment Machine"),
			fieldtype: "Link",
			options: "Equipment Machine",
		},
	],
};
