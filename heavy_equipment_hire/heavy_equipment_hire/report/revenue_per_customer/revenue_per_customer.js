frappe.query_reports["Revenue per Customer"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_end(),
			reqd: 1,
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center / Machine"),
			fieldtype: "Link",
			options: "Cost Center",
		},
		{
			fieldname: "chart_view",
			label: __("Chart View"),
			fieldtype: "Select",
			options: "Revenue Trend\nMost Served Customers",
			default: "Revenue Trend",
		},
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;

		if (data.is_group) {
			if (["customer_header", "amount"].includes(column.fieldname)) {
				return `<strong>${value}</strong>`;
			}
			return "";
		}

		if (column.fieldname === "amount") {
			return `<span style="font-weight:600">${value}</span>`;
		}

		return value;
	},
};
