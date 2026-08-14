frappe.ui.form.on("Employee KPI Review", {
	refresh(frm) {
		show_score_indicator(frm);
		add_status_buttons(frm);
	},
	kpi_template(frm) {
		if (frm.doc.kpi_template && frm.is_new() && !(frm.doc.items || []).length) {
			load_template_items(frm);
		}
	},
});

frappe.ui.form.on("Employee KPI Review Item", {
	employee_score(frm) {
		calculate_scores(frm);
	},
	manager_score(frm) {
		calculate_scores(frm);
	},
	weight(frm) {
		calculate_scores(frm);
	},
	items_remove(frm) {
		calculate_scores(frm);
	},
});

function add_status_buttons(frm) {
	if (frm.is_new()) {
		frm.add_custom_button(__("Load KPI Template"), () => load_template_items(frm));
		return;
	}

	if (!frm.doc.docstatus) {
		frm.add_custom_button(__("Load KPI Template"), () => load_template_items(frm));
	}

	const transitions = {
		Draft: __("Start Self Review"),
		"Self Review": __("Send to Manager"),
		"Manager Review": __("Acknowledge"),
		"Employee Acknowledgement": __("Close by HR"),
	};

	const next_status = {
		Draft: "Self Review",
		"Self Review": "Manager Review",
		"Manager Review": "Employee Acknowledgement",
		"Employee Acknowledgement": "HR Closed",
	};

	if (frm.doc.workflow_status !== "HR Closed" && transitions[frm.doc.workflow_status]) {
		frm.add_custom_button(transitions[frm.doc.workflow_status], () => {
			frm.set_value("workflow_status", next_status[frm.doc.workflow_status]);
			frm.save();
		});
	}
}

function load_template_items(frm) {
	if (!frm.doc.kpi_template) {
		frappe.msgprint(__("Please select a KPI Template first."));
		return;
	}

	frappe.call({
		method:
			"heavy_equipment_hire.heavy_equipment_hire.doctype.employee_kpi_review.employee_kpi_review.get_template_items",
		args: {
			kpi_template: frm.doc.kpi_template,
		},
		callback(r) {
			const rows = r.message || [];
			if (!rows.length) return;

			frm.clear_table("items");
			rows.forEach((row) => {
				const child = frm.add_child("items");
				child.kpi_area = row.kpi_area;
				child.metric = row.metric;
				child.target = row.target;
				child.weight = row.weight;
			});
			frm.refresh_field("items");
			calculate_scores(frm);
		},
	});
}

function calculate_scores(frm) {
	let total_weight = 0;
	let employee_total = 0;
	let manager_total = 0;
	let final_total = 0;

	(frm.doc.items || []).forEach((row) => {
		const weight = flt(row.weight);
		row.employee_weighted_score = (flt(row.employee_score) * weight) / 100;
		row.manager_weighted_score = (flt(row.manager_score) * weight) / 100;
		row.final_weighted_score = row.manager_score === undefined || row.manager_score === null || row.manager_score === ""
			? row.employee_weighted_score
			: row.manager_weighted_score;

		total_weight += weight;
		employee_total += flt(row.employee_weighted_score);
		manager_total += flt(row.manager_weighted_score);
		final_total += flt(row.final_weighted_score);
	});

	frm.set_value("total_weight", total_weight);
	frm.set_value("employee_total_score", employee_total);
	frm.set_value("manager_total_score", manager_total);
	frm.set_value("final_score", final_total);
	frm.refresh_field("items");
}

function show_score_indicator(frm) {
	if (!frm.dashboard || frm.is_new()) return;

	const score = flt(frm.doc.final_score);
	let color = "red";
	if (score >= 95) color = "green";
	else if (score >= 85) color = "blue";
	else if (score >= 75) color = "orange";

	frm.dashboard.clear_headline();
	frm.dashboard.add_indicator(__(`Final Score: ${score}%`), color);
}
