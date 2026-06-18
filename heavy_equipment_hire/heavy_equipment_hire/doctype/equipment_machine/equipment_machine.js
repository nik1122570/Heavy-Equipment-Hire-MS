frappe.ui.form.on("Equipment Machine", {
	refresh(frm) {
		show_insurance_indicator(frm);
	},
	insurance_policy(frm) {
		set_insurance_details_from_policy(frm);
	},
	insurance_expiry_date(frm) {
		show_insurance_indicator(frm);
	},
	insurance_provider(frm) {
		show_insurance_indicator(frm);
	},
	insurance_status(frm) {
		show_insurance_indicator(frm);
	},
});

function set_insurance_details_from_policy(frm) {
	if (!frm.doc.insurance_policy) {
		frm.set_value("insurance_provider", "");
		show_insurance_indicator(frm);
		return;
	}

	frappe.db.get_value(
		"Insurance Policy",
		frm.doc.insurance_policy,
		["provider", "expiry_date", "status"],
		({ message }) => {
			if (!message) return;

			frm.set_value("insurance_provider", message.provider || "");
			frm.set_value("insurance_expiry_date", message.expiry_date || "");
			frm.set_value("insurance_status", message.status || "Not Set");
			show_insurance_indicator(frm);
		}
	);
}

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
