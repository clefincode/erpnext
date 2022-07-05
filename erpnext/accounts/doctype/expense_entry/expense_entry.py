# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.setup.utils import get_exchange_rate
from erpnext.accounts.general_ledger import make_reverse_gl_entries

class ExpenseEntry(AccountsController):

	def validate(self):
		self.validate_company_accounts()
		self.validate_accounts_currency()
		self.validate_exchange_rate()
		self.validate_totals()

	def validate_exchange_rate(self):
		if not self.conversion_rate:
			company = frappe.get_doc('Company' , self.company)
			self.conversion_rate = get_exchange_rate(self.account_currency , company.default_currency , self.posting_date)

	def validate_company_accounts(self):
		for acc in self.account:
			account = frappe.get_doc("Account" , acc.account)
			if account.company != self.company:
				frappe.throw('All Accounts Must be From The Same Company')
		account = frappe.get_doc("Account" , self.account_paid_from)
		if account.company != self.company:
				frappe.throw('All Accounts Must be From The Same Company')

	def validate_accounts_currency(self):
		#all account must have the same currency
		for account in self.account:
			if account.account_currency != self.account_currency:
				frappe.throw('All Accounts Must Have The Same Currency')

	def validate_totals(self):
		if not self.total_debit:
			total = 0
			for acc in self.account:
				total += acc.amount
			self.total_debit = total * self.conversion_rate
		
		if not self.total_credit:
			self.total_credit = self.paid_amount * self.conversion_rate
		
		if self.total_debit != self.total_credit :
			frappe.throw('Total Debit And Total Credit Must Be Equal')


	def on_submit(self):
		self.make_gl_entries()

	def on_cancel(self):
		self.ignore_linked_doctypes = ('GL Entry', 'Stock Ledger Entry')
		make_reverse_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

	def make_gl_entries(self):
		for account in self.account:
			expense_gl_entry = self.get_gl_dict({
				"account" : account.account,
				"against" : self.account_paid_from,
				"voucher_type" : "Expense Entry",
				"voucher" : self.name,
				"debit" : account.amount * self.conversion_rate,
				"cost_center" : account.cost_center,
				"remarks" : str(account.remark) + ' Note: ' + str(self.general_remark),
				"account_currency" : account.account_currency
			} , item = account)
			cash_gl_entry = self.get_gl_dict({
				"account" : self.account_paid_from,
				"against" : account.account,
				"credit" : account.amount * self.conversion_rate,
				"cost_center" : account.cost_center,
				"remarks" : str(account.remark) + ' Note: ' + str(self.general_remark),
				"account_currency" : self.account_currency
			},item = self)
			from erpnext.accounts.general_ledger import make_gl_entries
			make_gl_entries([expense_gl_entry, cash_gl_entry], cancel=(self.docstatus == 2),
				update_outstanding="No", merge_entries=False)

