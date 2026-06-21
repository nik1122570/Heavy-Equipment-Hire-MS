frappe.ui.form.on("Fleet Tracker", {
	refresh(frm) {
		set_reason_requirement(frm);
		show_variance_indicator(frm);
	},
	equipment_machine(frm) {
		if (!frm.doc.equipment_machine) return;

		frappe.db.get_value(
			"Equipment Machine",
			frm.doc.equipment_machine,
			["machine_name", "company", "cost_center"],
			({ message }) => {
				if (!message) return;
				frm.set_value("machine_name", message.machine_name || "");
				frm.set_value("company", message.company || "");
				frm.set_value("cost_center", message.cost_center || "");
			}
		);
	},
	gps_hours(frm) {
		calculate_variance(frm);
	},
	physical_hours(frm) {
		calculate_variance(frm);
	},
});

function calculate_variance(frm) {
	const variance = flt(frm.doc.gps_hours) - flt(frm.doc.physical_hours);
	frm.set_value("variance_hours", variance);

	let direction = "No Variance";
	if (variance > 0) direction = "GPS Greater";
	if (variance < 0) direction = "Physical Greater";
	frm.set_value("variance_direction", direction);

	set_reason_requirement(frm);
	show_variance_indicator(frm);
}

function set_reason_requirement(frm) {
	frm.toggle_reqd("reason", flt(frm.doc.variance_hours) > 0);
}

function show_variance_indicator(frm) {
	if (!frm.dashboard || frm.is_new()) return;

	const variance = flt(frm.doc.variance_hours);
	const direction = frm.doc.variance_direction || "No Variance";
	const color = variance > 0 ? "red" : variance < 0 ? "orange" : "green";
	frm.dashboard.clear_headline();
	frm.dashboard.add_indicator(__(`Variance: ${variance.toFixed(2)} hrs (${direction})`), color);
}
