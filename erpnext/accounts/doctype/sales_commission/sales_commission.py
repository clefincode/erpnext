# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import barry_as_FLUFL, unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt

class SalesCommission(Document):
	@frappe.whitelist()
	def get_data(self):
		self.details = []
		unwanted_student_groups = frappe.db.get_list("Sales Commission Detail", filters = {"docstatus":["<",2]}, fields = ["distinct student_group"], pluck="student_group")
		student_groups = frappe.db.get_list("Student Group", filters = {"name": ["not in", unwanted_student_groups], "type": "General Course", "status": ["in",["Active", "Finished"]], "company": self.company}, pluck = "name", order_by = "name")
		for sg in student_groups:
			fees_status = frappe.get_list("Fees", fields = ["sum(grand_total - total_discount_applied_for_this_fee) as sum", "outstanding_amount"], filters = {"student_group": sg, "docstatus": 1}, group_by = "outstanding_amount")
			is_all_paid = True
			sum_paid = 0
			for fees_stat in fees_status:
				if flt(fees_stat.sum):
					if fees_stat.outstanding_amount != 0:
						is_all_paid = False
						break
					else:
						sum_paid = flt(fees_stat.sum)
			if is_all_paid:
				fees = frappe.get_list("Fees", filters= {"student_group": sg, "docstatus": 1}, fields=["name", "fees_category", "student", "program_enrollment", "fee_structure", "grand_total", "total_discount_applied_for_this_fee", "student_group"])
				avg_mini_limit = calculate_avg_min_limit_fee_structure(fees)
				for fee in fees:
					self.add_detail(fee, sum_paid, avg_mini_limit)
		self.refresh_summaries()
					
	def add_detail(self, fees, sum_paid, avg_mini_limit):
		fee_structure = frappe.get_doc("Fee Structure", fees.fee_structure)
		fees_category = frappe.get_doc("Fee Category", fees.fees_category)
		salesman = frappe.db.get_value("Program Enrollment", fees.program_enrollment, "salesman")
		program = frappe.db.get_value("Student Group", fees.student_group, "program")
		is_owner = check_salesman_is_owner(salesman, program)
		is_delaied_by_sales = check_student_group_delay(fees.student_group)
		amount = get_amount(fee_structure, fees_category, is_owner, is_delaied_by_sales, sum_paid, fees, avg_mini_limit)
		if amount and salesman:
			self.append("details", {
				"doctype": "Sales Commission Detail",
				"student_group": fees.student_group,
				"salesman": salesman,
				"student": fees.student,
				"amount": amount,
				"owner": is_owner
			})

	@frappe.whitelist()
	def refresh_summaries(self):
		self.summary_student_group = []
		res = {}
		for detail in self.details:
			key = detail.student_group + " " + detail.salesman
			if res.get(key):
				res[key]["amount"] += detail.amount
			else:
				res.update({key: {
					"doctype": "Sales Commission Summary by Student Group",
					"student_group": detail.student_group,
					"salesman": detail.salesman,
					"amount": detail.amount
				}})
		for key, value in res.items():
			self.append("summary_student_group", value)
		#last summary
		self.summary = []
		summary_res = {}
		for s in self.summary_student_group:
			if summary_res.get(s.student_group):
				summary_res[s.student_group] += s.amount
			else:
				summary_res.update({s.student_group: s.amount})
		for key, value in summary_res.items():
			self.append("summary", {
				"student_group": key,
				"amount": value
			})

def calculate_avg_min_limit_fee_structure(fees):
	if fees:
		avg = 0
		for fee in fees:
			limit = frappe.db.get_value("Fee Structure", fee.fee_structure, "minimum_limit")
			avg += limit
		return avg/len(fees)
	return 0

def get_amount(fee_structure, fees_category, is_owner, is_delaied_by_sales, sum_paid, fees, avg_mini_limit):
	if (sum_paid < avg_mini_limit or is_delaied_by_sales) and is_owner:
		return 0

	if not fee_structure.disable_commission:
		if fee_structure.base_rate and fee_structure.extra_rate and fees_category.enable_commission:
			cur_percent = fee_structure.base_rate if sum_paid <= avg_mini_limit else fee_structure.extra_rate
			return (flt(fees.grand_total) - flt(fees.total_discount_applied_for_this_fee)) * flt(cur_percent)
		if fees_category.enable_commission:
			if fees_category.base_rate:
				cur_percent = fees_category.base_rate if sum_paid <= avg_mini_limit else fees_category.extra_rate
				return (flt(fees.grand_total) - flt(fees.total_discount_applied_for_this_fee)) * flt(cur_percent)
	return 0

def check_salesman_is_owner(salesman, program):
	return frappe.db.get_value("Program", program, "salesman_owner") == salesman

def check_student_group_delay(student_group):
	delay_respons = frappe.get_list("Student Group Delay Reason", filters={"parent": student_group, "responsibility": "Sales"}, fields=["name"])
	return len(delay_respons) > 0


