frappe.query_reports["Machine Compliance Report"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
		},
		{
			fieldname: "equipment_machine",
			label: __("Equipment Machine"),
			fieldtype: "Link",
			options: "Equipment Machine",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nCompliant\nAttention Required\nNon-Compliant",
		},
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;

		const field = column.fieldname;
		const status_fields = [
			"latra_license",
			"osha_certificate",
			"usalama_barabarani_sticker",
			"tools_compliance",
			"weight_inspection",
			"overall_status",
		];
		if (!status_fields.includes(field)) return value;

		const raw = data[field] || "";
		let color = "#64748b";
		if (raw.includes("Active") || raw === "Compliant") color = "#059669";
		if (raw.includes("Expiring Soon") || raw === "Attention Required") color = "#d97706";
		if (raw.includes("Expired") || raw.includes("Missing") || raw === "Non-Compliant") color = "#dc2626";

		return `<span style="font-weight:600;color:${color}">${value}</span>`;
	},
};
