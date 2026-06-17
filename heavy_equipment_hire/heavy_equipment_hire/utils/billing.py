from __future__ import annotations

import math

import frappe
from frappe.utils import date_diff, flt


def calculate_block_hour_billing(
	start_meter_reading: float | None,
	end_meter_reading: float | None,
	block_size_hours: float | None,
	block_rate: float | None,
	minimum_blocks: int | None = 1,
) -> dict:
	"""Calculate hire charges where one price is charged for each hour block.

	Example: 8 hours = TZS 700,000. Any partial block rounds up to the next block.
	"""
	start = flt(start_meter_reading)
	end = flt(end_meter_reading)
	block_size = flt(block_size_hours)
	rate = flt(block_rate)
	min_blocks = int(minimum_blocks or 1)

	if block_size <= 0:
		frappe.throw("Block Size Hours must be greater than zero.")

	if end < start:
		frappe.throw("End Meter Reading cannot be less than Start Meter Reading.")

	actual_hours = end - start
	calculated_blocks = math.ceil(actual_hours / block_size) if actual_hours else 0
	billable_blocks = max(calculated_blocks, min_blocks)
	total = billable_blocks * rate

	return {
		"actual_hours": actual_hours,
		"billable_blocks": billable_blocks,
		"hire_amount": total,
	}


def calculate_daily_billing(from_date, to_date, daily_rate: float | None) -> dict:
	days = max(date_diff(to_date, from_date) + 1, 1)
	amount = days * flt(daily_rate)
	return {"billable_days": days, "hire_amount": amount}


def calculate_monthly_billing(from_date, to_date, monthly_rate: float | None) -> dict:
	days = max(date_diff(to_date, from_date) + 1, 1)
	months = math.ceil(days / 30)
	amount = months * flt(monthly_rate)
	return {"billable_months": months, "hire_amount": amount}

