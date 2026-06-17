frappe.ui.form.on("Hire Commercial Adjustment", {
	refresh(frm) {
		render_adjustment_dashboard(frm);

		if (frm.doc.docstatus === 1 && get_unpaid_cost_rows(frm).length) {
			frm.add_custom_button(__("Pay Extra Costs"), () => {
				show_pay_costs_dialog(frm);
			});
		}

		if (frm.doc.docstatus === 1 && get_unbilled_charge_rows(frm).length) {
			frm.add_custom_button(__("Bill Back Charges"), () => {
				show_bill_charges_dialog(frm);
			});
		}
	},
	hire_quotation_simulation(frm) {
		if (frm.doc.hire_quotation_simulation) {
			frappe.db.get_doc("Hire Quotation Simulation", frm.doc.hire_quotation_simulation).then((simulation) => {
				frm.set_value({
					company: simulation.company,
					customer: simulation.customer,
					project: simulation.project,
					machine: simulation.machine,
					cost_center: simulation.cost_center,
					original_expected_revenue: simulation.total_expected_revenue,
					original_expected_cost: simulation.total_expected_cost,
					original_expected_profit: simulation.expected_profit,
					original_margin_percentage: simulation.profit_margin_percentage,
					revised_revenue: simulation.total_expected_revenue,
					revised_cost: simulation.total_expected_cost,
					revised_profit: simulation.expected_profit,
					revised_margin_percentage: simulation.profit_margin_percentage,
				});
				render_adjustment_dashboard(frm);
			});
		}
	},
	additional_costs_add(frm) {
		calculate_adjustment_totals(frm);
	},
	additional_costs_remove(frm) {
		calculate_adjustment_totals(frm);
	},
	back_charges_add(frm) {
		calculate_adjustment_totals(frm);
	},
	back_charges_remove(frm) {
		calculate_adjustment_totals(frm);
	},
});

frappe.ui.form.on("Hire Adjustment Cost", {
	qty(frm, cdt, cdn) {
		calculate_child_amount(frm, cdt, cdn);
	},
	rate(frm, cdt, cdn) {
		calculate_child_amount(frm, cdt, cdn);
	},
	cost_type(frm, cdt, cdn) {
		calculate_child_amount(frm, cdt, cdn);
	},
});

frappe.ui.form.on("Hire Adjustment Charge", {
	qty(frm, cdt, cdn) {
		calculate_child_amount(frm, cdt, cdn);
	},
	rate(frm, cdt, cdn) {
		calculate_child_amount(frm, cdt, cdn);
	},
	revenue_charge(frm, cdt, cdn) {
		calculate_child_amount(frm, cdt, cdn);
	},
});

function calculate_child_amount(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	frappe.model.set_value(cdt, cdn, "amount", flt(row.qty) * flt(row.rate));
	calculate_adjustment_totals(frm);
}

function calculate_adjustment_totals(frm) {
	const additional_cost = (frm.doc.additional_costs || []).reduce((total, row) => {
		return total + flt(row.amount || flt(row.qty) * flt(row.rate));
	}, 0);
	const additional_revenue = (frm.doc.back_charges || []).reduce((total, row) => {
		return total + flt(row.amount || flt(row.qty) * flt(row.rate));
	}, 0);
	const revised_revenue = flt(frm.doc.original_expected_revenue) + additional_revenue;
	const revised_cost = flt(frm.doc.original_expected_cost) + additional_cost;
	const revised_profit = revised_revenue - revised_cost;
	const revised_margin = revised_revenue ? (revised_profit / revised_revenue) * 100 : 0;

	frm.set_value("additional_cost", additional_cost);
	frm.set_value("additional_revenue", additional_revenue);
	frm.set_value("net_adjustment", additional_revenue - additional_cost);
	frm.set_value("revised_revenue", revised_revenue);
	frm.set_value("revised_cost", revised_cost);
	frm.set_value("revised_profit", revised_profit);
	frm.set_value("revised_margin_percentage", revised_margin);
	render_adjustment_dashboard(frm);
}

function get_unpaid_cost_rows(frm) {
	return (frm.doc.additional_costs || []).filter((row) => {
		const amount = flt(row.amount || flt(row.qty) * flt(row.rate));
		return row.cost_type && amount > 0 && !row.purchase_invoice;
	});
}

function get_unbilled_charge_rows(frm) {
	return (frm.doc.back_charges || []).filter((row) => {
		const amount = flt(row.amount || flt(row.qty) * flt(row.rate));
		return row.revenue_charge && amount > 0 && !row.sales_invoice;
	});
}

function show_pay_costs_dialog(frm) {
	const rows = get_unpaid_cost_rows(frm);
	const fields = [
		{
			fieldname: "supplier",
			fieldtype: "Link",
			label: __("Supplier"),
			options: "Supplier",
			reqd: 1,
		},
		{
			fieldname: "expense_section",
			fieldtype: "Section Break",
			label: __("Extra Costs to Pay"),
		},
		...make_selection_fields(rows, "cost_type"),
	];
	show_invoice_dialog(frm, __("Pay Extra Costs"), fields, rows, "cost", "make_purchase_invoice");
}

function show_bill_charges_dialog(frm) {
	const rows = get_unbilled_charge_rows(frm);
	const fields = [
		{
			fieldname: "charge_section",
			fieldtype: "Section Break",
			label: __("Back Charges to Bill"),
		},
		...make_selection_fields(rows, "revenue_charge"),
	];
	show_invoice_dialog(frm, __("Bill Back Charges"), fields, rows, "charge", "make_sales_invoice");
}

function make_selection_fields(rows, item_fieldname) {
	return rows.map((row, index) => {
		const amount = flt(row.amount || flt(row.qty) * flt(row.rate));
		return {
			fieldname: `row_${index}`,
			fieldtype: "Check",
			label: `${row.idx}. ${row[item_fieldname]} - ${format_currency(amount, frappe.defaults.get_default("currency"))}`,
			default: 1,
		};
	});
}

function show_invoice_dialog(frm, title, fields, rows, row_type, method_name) {
	const dialog = new frappe.ui.Dialog({
		title,
		fields,
		primary_action_label: row_type === "cost" ? __("Create Purchase Invoice") : __("Create Sales Invoice"),
		primary_action(values) {
			const selected_rows = rows.filter((row, index) => values[`row_${index}`]).map((row) => row.name);
			if (!selected_rows.length) {
				frappe.msgprint(__("Select at least one row."));
				return;
			}

			const args = { source_name: frm.doc.name };
			if (row_type === "cost") {
				args.supplier = values.supplier;
				args.cost_rows = selected_rows;
			} else {
				args.charge_rows = selected_rows;
			}

			frappe.call({
				method: `heavy_equipment_hire.heavy_equipment_hire.doctype.hire_commercial_adjustment.hire_commercial_adjustment.${method_name}`,
				args,
				freeze: true,
				callback(r) {
					if (r.message) {
						dialog.hide();
						frappe.model.sync(r.message);
						frappe.set_route("Form", r.message.doctype, r.message.name);
					}
				},
			});
		},
	});
	dialog.show();
}

function money(value) {
	return format_currency(flt(value), frappe.defaults.get_default("currency"));
}

function render_adjustment_dashboard(frm) {
	if (!frm.fields_dict.profitability_dashboard) return;

	const original_revenue = flt(frm.doc.original_expected_revenue);
	const original_cost = flt(frm.doc.original_expected_cost);
	const revised_revenue = flt(frm.doc.revised_revenue);
	const revised_cost = flt(frm.doc.revised_cost);
	const revised_profit = flt(frm.doc.revised_profit);
	const revised_margin = flt(frm.doc.revised_margin_percentage);
	const profit_class = revised_profit >= 0 ? "positive" : "negative";

	frm.fields_dict.profitability_dashboard.$wrapper.html(`
		<style>
			.adjustment-market { background: #101820; color: #f7fafc; border-radius: 8px; padding: 18px; }
			.adjustment-market__grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
			.adjustment-market__tile { background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.12); border-radius: 8px; padding: 12px; }
			.adjustment-market__label { color: #9fb2c1; font-size: 11px; text-transform: uppercase; letter-spacing: .08em; }
			.adjustment-market__value { font-size: 21px; font-weight: 700; margin-top: 4px; }
			.adjustment-market__value.positive { color: #51d88a; }
			.adjustment-market__value.negative { color: #ff6b6b; }
			.adjustment-market__compare { margin-top: 14px; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
			@media (max-width: 900px) { .adjustment-market__grid, .adjustment-market__compare { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
		</style>
		<div class="adjustment-market">
			<div class="adjustment-market__grid">
				<div class="adjustment-market__tile"><div class="adjustment-market__label">Additional Revenue</div><div class="adjustment-market__value">${money(frm.doc.additional_revenue)}</div></div>
				<div class="adjustment-market__tile"><div class="adjustment-market__label">Additional Cost</div><div class="adjustment-market__value">${money(frm.doc.additional_cost)}</div></div>
				<div class="adjustment-market__tile"><div class="adjustment-market__label">Revised Profit</div><div class="adjustment-market__value ${profit_class}">${money(revised_profit)}</div></div>
				<div class="adjustment-market__tile"><div class="adjustment-market__label">Revised Margin</div><div class="adjustment-market__value ${profit_class}">${revised_margin.toFixed(2)}%</div></div>
			</div>
			<div class="adjustment-market__compare">
				<div class="adjustment-market__tile"><div class="adjustment-market__label">Original Revenue / Cost</div><div class="adjustment-market__value">${money(original_revenue)} / ${money(original_cost)}</div></div>
				<div class="adjustment-market__tile"><div class="adjustment-market__label">Revised Revenue / Cost</div><div class="adjustment-market__value">${money(revised_revenue)} / ${money(revised_cost)}</div></div>
			</div>
		</div>
	`);
}
