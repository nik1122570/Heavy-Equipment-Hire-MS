frappe.query_reports["Daily Fleet Variance Report"] = {
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
			fieldname: "equipment_machine",
			label: __("Equipment Machine"),
			fieldtype: "Link",
			options: "Equipment Machine",
		},
		{
			fieldname: "variance_direction",
			label: __("Variance Direction"),
			fieldtype: "Select",
			options: "\nGPS Greater\nPhysical Greater\nNo Variance",
		},
		{
			fieldname: "exceptions_only",
			label: __("Exceptions Only"),
			fieldtype: "Check",
			default: 0,
		},
		{
			fieldname: "missing_reason_only",
			label: __("Missing Reason Only"),
			fieldtype: "Check",
			default: 0,
		},
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;

		if (column.fieldname === "variance_hours") {
			const variance = flt(data.variance_hours);
			if (variance > 0) return `<span style="color:#dc2626;font-weight:700">${value}</span>`;
			if (variance < 0) return `<span style="color:#d97706;font-weight:700">${value}</span>`;
			return `<span style="color:#16a34a;font-weight:700">${value}</span>`;
		}

		if (column.fieldname === "variance_direction") {
			const colors = {
				"GPS Greater": "red",
				"Physical Greater": "orange",
				"No Variance": "green",
			};
			return `<span class="indicator-pill ${colors[data.variance_direction] || "gray"}">${value}</span>`;
		}

		if (column.fieldname === "reason_required" && data.reason_required) {
			return `<span class="indicator-pill red">${__("Required")}</span>`;
		}

		return value;
	},
};
