frappe.ui.form.on("Quotation", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.custom_hire_quotation_simulation) {
			frm.add_custom_button(__("Create Sales Order"), () => {
				frappe.model.open_mapped_doc({
					method: "erpnext.selling.doctype.quotation.quotation.make_sales_order",
					frm,
				});
			}, __("Create"));
		}
	},
});
