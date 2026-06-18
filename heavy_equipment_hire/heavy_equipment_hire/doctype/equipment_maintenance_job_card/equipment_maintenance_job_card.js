frappe.ui.form.on("Equipment Maintenance Job Card", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.status === "Open" && !frm.doc.purchase_order) {
			frm.add_custom_button(__("Create Purchase Order"), () => {
				frappe.call({
					method: "heavy_equipment_hire.heavy_equipment_hire.doctype.equipment_maintenance_job_card.equipment_maintenance_job_card.make_purchase_order",
					args: { source_name: frm.doc.name },
					freeze: true,
					callback(r) {
						if (r.message) {
							frappe.model.sync(r.message);
							frappe.set_route("Form", r.message.doctype, r.message.name);
						}
					},
				});
			}, __("Create"));
		}

		if (frm.doc.docstatus === 1 && frm.doc.status === "Open") {
			frm.add_custom_button(__("Mark Completed"), () => {
				frm.set_value("status", "Completed");
				frm.set_value("completed_date", frappe.datetime.get_today());
				frm.save("Update");
			});
		}
	},
	equipment_machine(frm) {
		if (!frm.doc.equipment_machine) return;

		frappe.db.get_doc("Equipment Machine", frm.doc.equipment_machine).then((machine) => {
			frm.set_value({
				company: machine.company,
				cost_center: machine.cost_center,
				machine_name: machine.machine_name,
			});
		});
	},
	items_add(frm) {
		calculate_total(frm);
	},
	items_remove(frm) {
		calculate_total(frm);
	},
});

frappe.ui.form.on("Equipment Maintenance Item", {
	qty(frm, cdt, cdn) {
		calculate_row_amount(frm, cdt, cdn);
	},
	rate(frm, cdt, cdn) {
		calculate_row_amount(frm, cdt, cdn);
	},
	item_code(frm, cdt, cdn) {
		calculate_row_amount(frm, cdt, cdn);
	},
});

function calculate_row_amount(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	frappe.model.set_value(cdt, cdn, "amount", flt(row.qty) * flt(row.rate));
	calculate_total(frm);
}

function calculate_total(frm) {
	const total = (frm.doc.items || []).reduce((sum, row) => {
		return sum + flt(row.amount || flt(row.qty) * flt(row.rate));
	}, 0);
	frm.set_value("total_maintenance_cost", total);
}
