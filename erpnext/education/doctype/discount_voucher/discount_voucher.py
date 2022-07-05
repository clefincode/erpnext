# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.accounts.general_ledger import make_reverse_gl_entries
from frappe.utils import flt

class DiscountVoucher(AccountsController):

	def validate(self):
		self.validate_fees_outstanding_amount()

	def validate_fees_outstanding_amount(self):
		fee = frappe.get_doc("Fees",self.apply_for_fee)
		if fee.outstanding_amount - self.discount_amount < 0:
			frappe.throw('Cannot Give Student Discount More Than Outstanding Fees Amount')
	
	def validate_direct_discount(self):
		if self.direct_discount and not "Discount Approval - Edu" in frappe.get_roles():
			frappe.throw('You Cannot Submit Direct Discount')


	def on_submit(self):
		self.validate_direct_discount()
		self.make_gl_entries()
		self.calculate_total_discount_applied()
	
	def on_cancel(self):
		self.ignore_linked_doctypes = ('GL Entry', 'Stock Ledger Entry')
		make_reverse_gl_entries(voucher_type=self.doctype, voucher_no=self.name)
		self.calculate_total_discount_applied()

	
	def make_gl_entries(self):
		discount_gl_entry = self.get_gl_dict({
			"account": self.expense_account,
			"against": self.student,
			"debit": self.discount_amount,
			"debit_in_account_currency": self.discount_amount,
			"cost_center": self.cost_center
		}, item=self)

		student_gl_entries =  self.get_gl_dict({
			"account": self.receivable_account,
			"party_type": "Student",
			"party": self.student,
			"against": self.expense_account,
			"credit": self.discount_amount,
			"credit_in_account_currency": self.discount_amount,
			"against_voucher": self.apply_for_fee,
			"against_voucher_type": "Fees",
			"cost_center": self.cost_center
		}, item=self)


		from erpnext.accounts.general_ledger import make_gl_entries
		make_gl_entries([student_gl_entries, discount_gl_entry], cancel=(self.docstatus == 2),
			update_outstanding="Yes", merge_entries=False)
	
	
	@frappe.whitelist()
	def calculate_total_discount_applied(self):
		atts = frappe.get_list("Discount Voucher",{"apply_for_fee": self.apply_for_fee , "docstatus": 1 },["discount_amount"])
		total = sum(flt(att.discount_amount) for att in atts)
		frappe.db.set_value("Fees",self.apply_for_fee,"total_discount_applied_for_this_fee" , total)
	