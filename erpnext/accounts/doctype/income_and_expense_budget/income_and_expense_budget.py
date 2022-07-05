# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.accounts.utils import get_balance_on
from frappe.utils import flt

class IncomeandExpenseBudget(Document):
	@frappe.whitelist()
	def get_accounts(self):
		self.expenses = self.incomes = []
		expense_accounts = frappe.get_list('Account', {'account_type': 'Expense Account', 'is_group': 0 }, ['name'])
		for ea in expense_accounts:
			balance = get_balance_on(account = ea.name, date = self.till_date, in_account_currency = False, company = self.company)
			if balance : 
				self.append('expenses',{
					'account': ea.name,
					'period_balance': balance,
					'growth_rate': 0,
					'growth_balance': balance
				})
		income_accounts = frappe.get_list('Account',{'account_type': 'Income Account', 'is_group': 0}, ['name'])
		for ia in income_accounts:
			balance = get_balance_on(account = ia.name, date = self.till_date, in_account_currency = False, company = self.company)
			if balance:
				self.append('incomes',{
					'account': ia.name,
					'period_balance': -balance,
					'growth_rate': 0,
					'growth_balance': -balance
				})
	def validate(self):
		self.calc_totals()
	
	def calc_totals(self):
		income_total_growth = 0
		income_total = 0 
		for i in self.incomes:
			income_total_growth += i.growth_balance
			income_total += i.period_balance
		self.income_growth_total = income_total_growth
		self.income_total = income_total
		self.income_difference = income_total_growth - income_total
		self.inc_difference_rate = str(flt((income_total_growth / income_total - 1) * 100 , 2)) + " %"

		expense_total_growth = 0 
		expense_total = 0
		for e in self.expenses:
			expense_total_growth += e.growth_balance
			expense_total += e.period_balance
		self.expense_growth_total = expense_total_growth
		self.expense_total = expense_total
		self.expense_difference = expense_total_growth - expense_total
		self.exp_difference_rate = str(flt((expense_total_growth / expense_total - 1) * 100 , 2)) + " %"

			
