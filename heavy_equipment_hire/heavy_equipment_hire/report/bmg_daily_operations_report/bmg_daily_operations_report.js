frappe.query_reports["BMG Daily Operations Report"] = {
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
			fieldname: "equipment_machine",
			label: __("Equipment Machine"),
			fieldtype: "Link",
			options: "Equipment Machine",
		},
		{
			fieldname: "fleet_owner",
			label: __("Fleet Owner"),
			fieldtype: "Select",
			options: "\nBMG\nHINNO\nOther",
		},
		{
			fieldname: "asset_group",
			label: __("Asset Group"),
			fieldtype: "Select",
			options: "\nMachine\nTruck\nOther",
		},
		{
			fieldname: "operation_status",
			label: __("Operation Status"),
			fieldtype: "Select",
			options:
				"\nWorking\nIdle\nIn Transit\nUnder Maintenance\nUnder Contract\nWaiting Customer Order\nWaiting Loading\nMobilization\nDemobilization\nBreakdown\nOther",
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "Link",
			options: "Cost Center",
		},
		{
			fieldname: "billable_only",
			label: __("Billable Days Only"),
			fieldtype: "Check",
			default: 0,
		},
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;

		if (data.is_group) {
			if (["operation_date", "hours_worked", "chargeable_days", "payment_amount"].includes(column.fieldname)) {
				return `<strong>${value}</strong>`;
			}
			return "";
		}

		if (column.fieldname === "operation_status") {
			const colors = {
				Working: "green",
				Idle: "orange",
				"In Transit": "blue",
				"Under Maintenance": "red",
				"Under Contract": "purple",
				"Waiting Customer Order": "orange",
				"Waiting Loading": "orange",
				Mobilization: "blue",
				Demobilization: "blue",
				Breakdown: "red",
			};
			const color = colors[data.operation_status] || "gray";
			return `<span class="indicator-pill ${color}">${value}</span>`;
		}

		if (["hours_worked", "chargeable_days", "payment_amount"].includes(column.fieldname)) {
			return `<span style="font-weight:600">${value}</span>`;
		}

		return value;
	},
};
