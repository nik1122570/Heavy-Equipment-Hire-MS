frappe.ui.form.on("Equipment Machine", {
	refresh(frm) {
		show_insurance_indicator(frm);
	},
	insurance_expiry_date(frm) {
		show_insurance_indicator(frm);
	},
	insurance_status(frm) {
		show_insurance_indicator(frm);
	},
});

function show_insurance_indicator(frm) {
	if (!frm.dashboard || frm.is_new()) return;

	const status = frm.doc.insurance_status || "Not Set";
	const summary = frm.doc.insurance_status_summary || status;
	const color = {
		Active: "green",
		"Expiring Soon": "orange",
		Expired: "red",
		"Not Set": "gray",
	}[status] || "gray";

	frm.dashboard.clear_headline();
	frm.dashboard.add_indicator(__(`Insurance: ${summary}`), color);
}
