frappe.pages["equipment-availability-calendar"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Equipment Availability Calendar"),
		single_column: true,
	});

	const state = {
		from_date: frappe.datetime.get_today(),
		to_date: frappe.datetime.add_days(frappe.datetime.get_today(), 30),
		machine: null,
		customer: null,
		project: null,
	};

	const fields = {};
	fields.from_date = page.add_field({
		fieldname: "from_date",
		label: __("From"),
		fieldtype: "Date",
		default: state.from_date,
		change: () => {
			state.from_date = fields.from_date.get_value();
			load_calendar();
		},
	});
	fields.to_date = page.add_field({
		fieldname: "to_date",
		label: __("To"),
		fieldtype: "Date",
		default: state.to_date,
		change: () => {
			state.to_date = fields.to_date.get_value();
			load_calendar();
		},
	});
	fields.machine = page.add_field({
		fieldname: "machine",
		label: __("Machine"),
		fieldtype: "Link",
		options: "Equipment Machine",
		change: () => {
			state.machine = fields.machine.get_value();
			load_calendar();
		},
	});
	fields.customer = page.add_field({
		fieldname: "customer",
		label: __("Customer"),
		fieldtype: "Link",
		options: "Customer",
		change: () => {
			state.customer = fields.customer.get_value();
			load_calendar();
		},
	});
	fields.project = page.add_field({
		fieldname: "project",
		label: __("Project"),
		fieldtype: "Link",
		options: "Project",
		change: () => {
			state.project = fields.project.get_value();
			load_calendar();
		},
	});

	page.set_primary_action(__("Refresh"), () => load_calendar(), "refresh");
	page.main.html(`<div class="equipment-calendar-shell"></div>`);
	const $shell = page.main.find(".equipment-calendar-shell");

	function load_calendar() {
		$shell.html(`<div class="equipment-calendar-loading">${__("Loading calendar...")}</div>`);
		frappe.call({
			method: "heavy_equipment_hire.heavy_equipment_hire.report.machine_availability_calendar.machine_availability_calendar.get_calendar_data",
			args: state,
			callback: (r) => {
				render_calendar(r.message || {});
			},
		});
	}

	function render_calendar(data) {
		const dates = data.dates || [];
		const machines = data.machines || [];
		const stats = get_stats(machines);

		$shell.html(`
			<style>${get_styles(dates.length)}</style>
			<div class="equipment-calendar">
				<div class="equipment-calendar__summary">
					${summary_tile(__("Machines"), machines.length, "neutral")}
					${summary_tile(__("Available"), stats.available, "available")}
					${summary_tile(__("On Hire"), stats.on_hire, "on-hire")}
					${summary_tile(__("Booked"), stats.booked, "booked")}
					${summary_tile(__("Insurance Risk"), stats.insurance_risk, "risk")}
				</div>
				<div class="equipment-calendar__legend">
					${legend_item("available", __("Available"))}
					${legend_item("on-hire", __("On Hire"))}
					${legend_item("booked", __("Booked"))}
					${legend_item("maintenance", __("Unavailable"))}
					${legend_item("risk", __("Insurance Risk"))}
				</div>
				<div class="equipment-calendar__grid-wrap">
					${render_grid(dates, machines)}
				</div>
			</div>
		`);

		$shell.find("[data-sales-order]").on("click", function () {
			frappe.set_route("Form", "Sales Order", this.dataset.salesOrder);
		});
		$shell.find("[data-machine]").on("click", function () {
			frappe.set_route("Form", "Equipment Machine", this.dataset.machine);
		});
	}

	function render_grid(dates, machines) {
		if (!dates.length) {
			return `<div class="equipment-calendar-empty">${__("Select a valid date range.")}</div>`;
		}
		if (!machines.length) {
			return `<div class="equipment-calendar-empty">${__("No machines found for the selected filters.")}</div>`;
		}

		return `
			<div class="equipment-calendar__grid">
				<div class="equipment-calendar__machine-head">${__("Machine")}</div>
				${dates.map((date) => `<div class="equipment-calendar__date-head">${format_day(date)}</div>`).join("")}
				${machines.map((machine) => render_machine_row(machine, dates)).join("")}
			</div>
		`;
	}

	function render_machine_row(machine, dates) {
		const cells = dates.map((date) => render_day_cell(machine, date)).join("");
		const insurance_class = get_insurance_class(machine.insurance_status);
		return `
			<div class="equipment-calendar__machine" data-machine="${frappe.utils.escape_html(machine.machine)}">
				<div class="equipment-calendar__machine-title">${frappe.utils.escape_html(machine.machine_name || machine.machine)}</div>
				<div class="equipment-calendar__machine-sub">${frappe.utils.escape_html(machine.machine)} · ${frappe.utils.escape_html(machine.machine_type || "")}</div>
				<div class="equipment-calendar__machine-tags">
					<span class="machine-status">${frappe.utils.escape_html(machine.status || "")}</span>
					<span class="insurance-status ${insurance_class}">${frappe.utils.escape_html(machine.insurance_status_summary || machine.insurance_status || "Not Set")}</span>
				</div>
			</div>
			${cells}
		`;
	}

	function render_day_cell(machine, date) {
		const booking = get_booking_for_date(machine.bookings || [], date);
		const date_class = date === frappe.datetime.get_today() ? " today" : "";

		if (is_unavailable(machine.status)) {
			return `<div class="equipment-calendar__cell maintenance${date_class}"><span>${__("Unavailable")}</span></div>`;
		}
		if (!booking) {
			return `<div class="equipment-calendar__cell available${date_class}"><span>${__("Free")}</span></div>`;
		}

		const klass = booking.availability === "On Hire" ? "on-hire" : "booked";
		const customer = booking.customer_name || booking.customer || __("Customer");
		const project = booking.project ? ` · ${frappe.utils.escape_html(booking.project)}` : "";
		return `
			<div class="equipment-calendar__cell ${klass}${date_class}" data-sales-order="${frappe.utils.escape_html(booking.sales_order)}">
				<span class="booking-customer">${frappe.utils.escape_html(customer)}</span>
				<span class="booking-meta">${frappe.utils.escape_html(booking.sales_order)}${project}</span>
			</div>
		`;
	}

	function get_booking_for_date(bookings, date) {
		const current = frappe.datetime.str_to_obj(date);
		return bookings.find((booking) => {
			const start = frappe.datetime.str_to_obj(booking.from_date);
			const end = frappe.datetime.str_to_obj(booking.to_date);
			return current >= start && current <= end;
		});
	}

	function get_stats(machines) {
		return machines.reduce(
			(acc, machine) => {
				const current_booking = get_booking_for_date(machine.bookings || [], frappe.datetime.get_today());
				if (machine.insurance_status === "Expired" || machine.insurance_status === "Expiring Soon") acc.insurance_risk++;
				if (is_unavailable(machine.status)) acc.maintenance++;
				else if (current_booking) acc.on_hire++;
				else if ((machine.bookings || []).length) acc.booked++;
				else acc.available++;
				return acc;
			},
			{ available: 0, on_hire: 0, booked: 0, maintenance: 0, insurance_risk: 0 }
		);
	}

	function is_unavailable(status) {
		return ["Under Maintenance", "Maintenance Required", "Out of Service"].includes(status);
	}

	function get_insurance_class(status) {
		if (status === "Expired") return "risk";
		if (status === "Expiring Soon") return "soon";
		if (status === "Active") return "active";
		return "neutral";
	}

	function summary_tile(label, value, klass) {
		return `
			<div class="equipment-calendar__tile ${klass}">
				<div>${frappe.utils.escape_html(label)}</div>
				<strong>${frappe.utils.escape_html(String(value))}</strong>
			</div>
		`;
	}

	function legend_item(klass, label) {
		return `<span><i class="${klass}"></i>${frappe.utils.escape_html(label)}</span>`;
	}

	function format_day(date) {
		const parts = frappe.datetime.str_to_obj(date);
		return `<strong>${parts.getDate()}</strong><span>${parts.toLocaleString(undefined, { month: "short" })}</span>`;
	}

	function get_styles(day_count) {
		const day_width = day_count > 20 ? 118 : 132;
		return `
			.equipment-calendar { padding: 14px 0 28px; }
			.equipment-calendar-loading,
			.equipment-calendar-empty { padding: 28px; color: var(--text-muted); text-align: center; }
			.equipment-calendar__summary { display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 10px; margin-bottom: 12px; }
			.equipment-calendar__tile { border: 1px solid var(--border-color); border-radius: 8px; padding: 10px 12px; background: var(--fg-color); color: var(--text-muted); }
			.equipment-calendar__tile strong { display: block; font-size: 22px; color: var(--text-color); margin-top: 3px; }
			.equipment-calendar__tile.available strong { color: #0f9d58; }
			.equipment-calendar__tile.on-hire strong { color: #2563eb; }
			.equipment-calendar__tile.booked strong { color: #b7791f; }
			.equipment-calendar__tile.risk strong { color: #c53030; }
			.equipment-calendar__legend { display: flex; gap: 14px; flex-wrap: wrap; align-items: center; margin: 0 0 12px; color: var(--text-muted); }
			.equipment-calendar__legend span { display: inline-flex; align-items: center; gap: 6px; }
			.equipment-calendar__legend i { width: 10px; height: 10px; border-radius: 99px; display: inline-block; }
			.equipment-calendar__legend .available { background: #dcfce7; border: 1px solid #86efac; }
			.equipment-calendar__legend .on-hire { background: #dbeafe; border: 1px solid #93c5fd; }
			.equipment-calendar__legend .booked { background: #fef3c7; border: 1px solid #fcd34d; }
			.equipment-calendar__legend .maintenance { background: #e5e7eb; border: 1px solid #cbd5e1; }
			.equipment-calendar__legend .risk { background: #fee2e2; border: 1px solid #fca5a5; }
			.equipment-calendar__grid-wrap { border: 1px solid var(--border-color); border-radius: 8px; overflow: auto; background: var(--fg-color); }
			.equipment-calendar__grid { display: grid; grid-template-columns: 280px repeat(${day_count}, minmax(${day_width}px, 1fr)); min-width: ${280 + day_count * day_width}px; }
			.equipment-calendar__machine-head,
			.equipment-calendar__date-head { position: sticky; top: 0; z-index: 3; background: var(--fg-color); border-bottom: 1px solid var(--border-color); font-weight: 600; }
			.equipment-calendar__machine-head { left: 0; z-index: 4; padding: 12px; }
			.equipment-calendar__date-head { padding: 8px 10px; text-align: center; border-left: 1px solid var(--border-color); }
			.equipment-calendar__date-head strong,
			.equipment-calendar__date-head span { display: block; line-height: 1.2; }
			.equipment-calendar__date-head span { color: var(--text-muted); font-size: 11px; }
			.equipment-calendar__machine { position: sticky; left: 0; z-index: 2; background: var(--fg-color); border-top: 1px solid var(--border-color); padding: 10px 12px; min-height: 88px; cursor: pointer; }
			.equipment-calendar__machine-title { font-weight: 650; color: var(--text-color); }
			.equipment-calendar__machine-sub { color: var(--text-muted); font-size: 12px; margin-top: 2px; }
			.equipment-calendar__machine-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
			.equipment-calendar__machine-tags span { font-size: 11px; border-radius: 999px; padding: 3px 7px; background: var(--control-bg); }
			.insurance-status.active { color: #0f9d58; }
			.insurance-status.soon { color: #b7791f; }
			.insurance-status.risk { color: #c53030; }
			.equipment-calendar__cell { border-top: 1px solid var(--border-color); border-left: 1px solid var(--border-color); min-height: 88px; padding: 8px; display: flex; flex-direction: column; justify-content: center; gap: 3px; cursor: default; overflow: hidden; }
			.equipment-calendar__cell.today { box-shadow: inset 0 0 0 2px rgba(37, 99, 235, .18); }
			.equipment-calendar__cell.available { background: #f0fdf4; color: #166534; }
			.equipment-calendar__cell.on-hire { background: #eff6ff; color: #1d4ed8; cursor: pointer; }
			.equipment-calendar__cell.booked { background: #fffbeb; color: #92400e; cursor: pointer; }
			.equipment-calendar__cell.maintenance { background: #f1f5f9; color: #475569; }
			.equipment-calendar__cell > span { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
			.booking-customer { font-weight: 650; }
			.booking-meta { font-size: 11px; opacity: .78; }
			@media (max-width: 900px) {
				.equipment-calendar__summary { grid-template-columns: repeat(2, minmax(140px, 1fr)); }
			}
		`;
	}

	load_calendar();
};
