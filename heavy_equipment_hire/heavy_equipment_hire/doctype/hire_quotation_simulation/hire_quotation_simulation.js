frappe.ui.form.on("Hire Quotation Simulation", {
	refresh(frm) {
		calculate_simulation_totals(frm);
		render_profit_dashboard(frm);

		if (frm.doc.docstatus === 1 && !frm.doc.quotation) {
			frm.add_custom_button(__("Create Quotation"), () => {
				frappe.call({
					method: "heavy_equipment_hire.heavy_equipment_hire.doctype.hire_quotation_simulation.hire_quotation_simulation.make_quotation",
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

		if (frm.doc.docstatus === 1 && get_unpaid_cost_rows(frm).length) {
			frm.add_custom_button(__("Pay Expenses"), () => {
				show_pay_expenses_dialog(frm);
			});
		}

		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__("Commercial Adjustment"), () => {
				frappe.call({
					method: "heavy_equipment_hire.heavy_equipment_hire.doctype.hire_quotation_simulation.hire_quotation_simulation.make_commercial_adjustment",
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
	},
	charges_add(frm) {
		calculate_simulation_totals(frm);
	},
	charges_remove(frm) {
		calculate_simulation_totals(frm);
	},
	additional_costs_add(frm) {
		calculate_simulation_totals(frm);
	},
	additional_costs_remove(frm) {
		calculate_simulation_totals(frm);
	},
});

function get_unpaid_cost_rows(frm) {
	return (frm.doc.additional_costs || []).filter((row) => {
		const amount = flt(row.amount || flt(row.qty) * flt(row.rate));
		return row.cost_type && amount > 0 && !row.purchase_invoice;
	});
}

function show_pay_expenses_dialog(frm) {
	const rows = get_unpaid_cost_rows(frm);
	if (!rows.length) {
		frappe.msgprint(__("All expenses already have Purchase Invoices."));
		return;
	}

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
			label: __("Expenses to Pay"),
		},
	];

	rows.forEach((row, index) => {
		const amount = flt(row.amount || flt(row.qty) * flt(row.rate));
		fields.push({
			fieldname: `cost_${index}`,
			fieldtype: "Check",
			label: `${row.idx}. ${row.cost_type} - ${format_currency(amount, frappe.defaults.get_default("currency"))}`,
			default: 1,
		});
	});

	const dialog = new frappe.ui.Dialog({
		title: __("Pay Expenses"),
		fields,
		primary_action_label: __("Create Purchase Invoice"),
		primary_action(values) {
			const selected_rows = rows
				.filter((row, index) => values[`cost_${index}`])
				.map((row) => row.name);

			if (!selected_rows.length) {
				frappe.msgprint(__("Select at least one expense."));
				return;
			}

			frappe.call({
				method: "heavy_equipment_hire.heavy_equipment_hire.doctype.hire_quotation_simulation.hire_quotation_simulation.make_purchase_invoice",
				args: {
					source_name: frm.doc.name,
					supplier: values.supplier,
					cost_rows: selected_rows,
				},
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

frappe.ui.form.on("Hire Simulation Revenue", {
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

frappe.ui.form.on("Hire Simulation Cost", {
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

function money(value) {
	return format_currency(flt(value), frappe.defaults.get_default("currency"));
}

function calculate_child_amount(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	frappe.model.set_value(cdt, cdn, "amount", flt(row.qty) * flt(row.rate));
	calculate_simulation_totals(frm);
}

function calculate_simulation_totals(frm) {
	const revenue = (frm.doc.charges || []).reduce((total, row) => {
		return total + flt(row.amount || flt(row.qty) * flt(row.rate));
	}, 0);
	const cost = (frm.doc.additional_costs || []).reduce((total, row) => {
		return total + flt(row.amount || flt(row.qty) * flt(row.rate));
	}, 0);
	const profit = revenue - cost;
	const margin = revenue ? (profit / revenue) * 100 : 0;

	frm.set_value("total_expected_revenue", revenue);
	frm.set_value("total_expected_cost", cost);
	frm.set_value("expected_profit", profit);
	frm.set_value("profit_margin_percentage", margin);
	render_profit_dashboard(frm);
}

function render_profit_dashboard(frm) {
	if (!frm.fields_dict.profitability_dashboard) return;

	const revenue = flt(frm.doc.total_expected_revenue);
	const cost = flt(frm.doc.total_expected_cost);
	const profit = flt(frm.doc.expected_profit);
	const margin = flt(frm.doc.profit_margin_percentage);
	const scale = Math.max(revenue, cost, Math.abs(profit), 1);
	const revenue_width = Math.min(100, Math.round((revenue / scale) * 100));
	const cost_width = Math.min(100, Math.round((cost / scale) * 100));
	const profit_width = Math.min(100, Math.round((Math.abs(profit) / scale) * 100));
	const profit_class = profit >= 0 ? "positive" : "negative";
	const points = [
		...(frm.doc.charges || []).map((row) => flt(row.amount || flt(row.qty) * flt(row.rate))),
		...(frm.doc.additional_costs || []).map((row) => -flt(row.amount || flt(row.qty) * flt(row.rate))),
	];
	if (!points.length) points.push(0);
	const max = Math.max(...points.map(Math.abs), 1);
	const spark = points.map((point, index) => {
		const x = (index / (points.length - 1)) * 100;
		const y = 50 - (point / max) * 38;
		return `${x},${y}`;
	}).join(" ");

	frm.fields_dict.profitability_dashboard.$wrapper.html(`
		<style>
			.hire-market {
				background: linear-gradient(135deg, #101820 0%, #16242f 55%, #20313d 100%);
				color: #f7fafc;
				border-radius: 8px;
				padding: 18px;
				box-shadow: 0 14px 36px rgba(16, 24, 32, .18);
				font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
			}
			.hire-market__grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
			.hire-market__tile { background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.12); border-radius: 8px; padding: 12px; }
			.hire-market__label { color: #9fb2c1; font-size: 11px; text-transform: uppercase; letter-spacing: .08em; }
			.hire-market__value { font-size: 22px; font-weight: 700; margin-top: 4px; }
			.hire-market__value.positive { color: #51d88a; }
			.hire-market__value.negative { color: #ff6b6b; }
			.hire-market__bars { margin-top: 16px; display: grid; gap: 9px; }
			.hire-market__bar { height: 12px; border-radius: 99px; background: rgba(255,255,255,.12); overflow: hidden; }
			.hire-market__fill { height: 100%; border-radius: 99px; }
			.hire-market__fill.revenue { width: ${revenue_width}%; background: #2dd4bf; }
			.hire-market__fill.cost { width: ${cost_width}%; background: #f59e0b; }
			.hire-market__fill.profit { width: ${profit_width}%; background: ${profit >= 0 ? "#51d88a" : "#ff6b6b"}; }
			.hire-market__row { display: grid; grid-template-columns: 120px 1fr 120px; align-items: center; gap: 10px; color: #d7e2ea; font-size: 12px; }
			.hire-market__chart { height: 96px; margin-top: 16px; background: rgba(255,255,255,.06); border-radius: 8px; padding: 8px; }
			@media (max-width: 900px) { .hire-market__grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
		</style>
		<div class="hire-market">
			<div class="hire-market__grid">
				<div class="hire-market__tile"><div class="hire-market__label">Expected Revenue</div><div class="hire-market__value">${money(revenue)}</div></div>
				<div class="hire-market__tile"><div class="hire-market__label">Expected Cost</div><div class="hire-market__value">${money(cost)}</div></div>
				<div class="hire-market__tile"><div class="hire-market__label">Expected Profit</div><div class="hire-market__value ${profit_class}">${money(profit)}</div></div>
				<div class="hire-market__tile"><div class="hire-market__label">Margin</div><div class="hire-market__value ${profit_class}">${margin.toFixed(2)}%</div></div>
			</div>
			<div class="hire-market__bars">
				<div class="hire-market__row"><span>Revenue</span><div class="hire-market__bar"><div class="hire-market__fill revenue"></div></div><span>${money(revenue)}</span></div>
				<div class="hire-market__row"><span>Cost</span><div class="hire-market__bar"><div class="hire-market__fill cost"></div></div><span>${money(cost)}</span></div>
				<div class="hire-market__row"><span>Profit</span><div class="hire-market__bar"><div class="hire-market__fill profit"></div></div><span>${money(profit)}</span></div>
			</div>
			<div class="hire-market__chart">
				<svg viewBox="0 0 100 100" preserveAspectRatio="none" width="100%" height="100%">
					<line x1="0" y1="50" x2="100" y2="50" stroke="rgba(255,255,255,.18)" stroke-width="1" />
					<polyline points="${spark}" fill="none" stroke="${profit >= 0 ? "#51d88a" : "#ff6b6b"}" stroke-width="2.4" vector-effect="non-scaling-stroke" />
				</svg>
			</div>
		</div>
	`);
}
