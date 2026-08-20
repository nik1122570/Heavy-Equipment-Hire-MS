frappe.query_reports["Driver License Report"] = {
	filters: [
		{
			fieldname: "driver_name",
			label: __("Driver Name"),
			fieldtype: "Data",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nActive\nExpiring Soon\nExpired\nMissing",
		},
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data || column.fieldname !== "status") return value;

		const colors = {
			Active: "#059669",
			"Expiring Soon": "#d97706",
			Expired: "#dc2626",
			Missing: "#dc2626",
		};
		return `<span style="font-weight:600;color:${colors[data.status] || "#64748b"}">${value}</span>`;
	},
};
