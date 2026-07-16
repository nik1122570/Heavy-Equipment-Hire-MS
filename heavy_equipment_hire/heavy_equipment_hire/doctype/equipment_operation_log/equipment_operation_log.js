frappe.ui.form.on("Equipment Operation Log", {
	refresh(frm) {
		set_dynamic_requirements(frm);
		show_operation_indicator(frm);
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
	operation_status(frm) {
		set_dynamic_requirements(frm);
		show_operation_indicator(frm);
	},
	payment_amount(frm) {
		set_dynamic_requirements(frm);
	},
	customer(frm) {
		set_dynamic_requirements(frm);
	},
});

function set_dynamic_requirements(frm) {
	frm.toggle_reqd("idle_reason", frm.doc.operation_status === "Idle");
	frm.toggle_reqd("customer", flt(frm.doc.payment_amount) > 0);
}

function show_operation_indicator(frm) {
	if (!frm.dashboard || frm.is_new()) return;

	const status = frm.doc.operation_status || "Not Set";
	const color = {
		Working: "green",
		Idle: "orange",
		"In Transit": "blue",
		"Under Maintenance": "red",
		"Under Contract": "purple",
		"Waiting Customer Order": "orange",
		Mobilization: "blue",
		Demobilization: "blue",
		Breakdown: "red",
	}[status] || "gray";

	frm.dashboard.clear_headline();
	frm.dashboard.add_indicator(__(`Operation: ${status}`), color);
}
