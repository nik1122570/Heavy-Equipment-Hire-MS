frappe.ui.form.on("Compliance Certificate", {
	compliance_type(frm) {
		const critical_types = ["LATRA License", "OSHA Certificate", "Weight Inspection"];
		if (critical_types.includes(frm.doc.compliance_type)) {
			frm.set_value("is_critical", 1);
		}
	},
});
